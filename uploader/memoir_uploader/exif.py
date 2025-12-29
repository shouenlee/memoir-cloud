"""
EXIF metadata extraction.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


# Patterns to extract date from filenames
FILENAME_DATE_PATTERNS = [
    # IMG_20250928_223213.heic or 20251226_230108.jpg
    (r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})", "%Y%m%d_%H%M%S"),
    # IMG-20251129-WA0002.jpg (WhatsApp - no time, use noon)
    (r"IMG-(\d{4})(\d{2})(\d{2})-WA", None),
    # 2025-09-28_22-32-13.jpg
    (r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", "%Y-%m-%d_%H-%M-%S"),
    # Screenshot_2025-09-28-22-32-13.png
    (r"Screenshot_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})", "%Y-%m-%d-%H-%M-%S"),
]


def _parse_google_takeout_json(photo_path: Path) -> Optional[datetime]:
    """
    Look for a Google Takeout JSON sidecar file and extract photoTakenTime.
    Google Takeout exports photos with companion .json files containing metadata.
    
    Tries multiple naming patterns:
    - photo.jpg.json (most common)
    - photo.json (sometimes)
    - photo(1).jpg -> photo.jpg.json (edited photos)
    """
    # Try common JSON sidecar patterns
    json_paths = [
        photo_path.with_suffix(photo_path.suffix + ".json"),  # photo.jpg.json
        photo_path.with_suffix(".json"),  # photo.json (replaces extension)
    ]
    
    # Handle edited photos: "photo(1).jpg" -> try "photo.jpg.json"
    name = photo_path.stem
    if name.endswith(")") and "(" in name:
        base_name = re.sub(r"\(\d+\)$", "", name)
        json_paths.append(photo_path.parent / f"{base_name}{photo_path.suffix}.json")
    
    for json_path in json_paths:
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Try photoTakenTime first (actual photo timestamp)
                # Then creationTime (when added to Google Photos)
                for time_key in ["photoTakenTime", "creationTime"]:
                    if time_key in data and "timestamp" in data[time_key]:
                        timestamp = int(data[time_key]["timestamp"])
                        return datetime.fromtimestamp(timestamp)
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                continue
    
    return None


def _parse_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Try to extract date/time from filename patterns.
    Returns None if no pattern matches.
    """
    for pattern, fmt in FILENAME_DATE_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            if fmt is None:
                # WhatsApp style - just date, use noon as time
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                try:
                    return datetime(year, month, day, 12, 0, 0)
                except ValueError:
                    continue
            else:
                # Full date+time pattern
                try:
                    date_str = "".join(groups)
                    # Reconstruct the expected format string based on group count
                    if len(groups) == 6:
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        hour, minute, second = int(groups[3]), int(groups[4]), int(groups[5])
                        return datetime(year, month, day, hour, minute, second)
                except (ValueError, IndexError):
                    continue
    return None


def extract_exif_data(photo_path: Path) -> Dict[str, Any]:
    """
    Extract relevant EXIF metadata from a photo.
    Returns a dictionary with camera, focalLength, aperture, iso.
    """
    result: Dict[str, Any] = {}
    
    try:
        with Image.open(photo_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return result

            # Map EXIF tag IDs to names
            exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value

            # Camera make and model
            make = exif.get("Make", "").strip()
            model = exif.get("Model", "").strip()
            if model:
                # Remove redundant make from model if present
                if make and model.startswith(make):
                    model = model[len(make):].strip()
                result["camera"] = f"{make} {model}".strip() if make else model

            # Focal length
            focal_length = exif.get("FocalLength")
            if focal_length:
                if hasattr(focal_length, "numerator"):
                    fl_value = focal_length.numerator / focal_length.denominator
                else:
                    fl_value = float(focal_length)
                result["focalLength"] = f"{fl_value:.0f}mm"

            # Aperture (F-number)
            f_number = exif.get("FNumber")
            if f_number:
                if hasattr(f_number, "numerator"):
                    f_value = f_number.numerator / f_number.denominator
                else:
                    f_value = float(f_number)
                result["aperture"] = f"f/{f_value:.1f}"

            # ISO
            iso = exif.get("ISOSpeedRatings")
            if iso:
                if isinstance(iso, tuple):
                    iso = iso[0]
                result["iso"] = int(iso)

    except Exception:
        pass

    return result


class DateSource:
    """Indicates where the date was sourced from."""
    EXIF = "exif"
    GOOGLE_TAKEOUT = "google_takeout"
    FILENAME = "filename"
    FILE_MTIME = "file_mtime"


def get_photo_date(photo_path: Path, return_source: bool = False) -> datetime | tuple[datetime, str]:
    """
    Get the date a photo was taken.
    Priority:
    1. EXIF DateTimeOriginal/DateTime/DateTimeDigitized
    2. Google Takeout JSON sidecar file (photoTakenTime)
    3. Date parsed from filename (e.g., IMG_20250928_223213.heic)
    4. File modification time (last resort - often unreliable)
    
    If return_source=True, returns tuple of (datetime, source) where source
    is one of DateSource.EXIF, DateSource.GOOGLE_TAKEOUT, DateSource.FILENAME, 
    or DateSource.FILE_MTIME.
    """
    # Try EXIF first
    try:
        with Image.open(photo_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # Map EXIF tag IDs to names
                exif = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif[tag] = value

                # Try DateTimeOriginal first, then DateTime
                for date_tag in ["DateTimeOriginal", "DateTime", "DateTimeDigitized"]:
                    date_str = exif.get(date_tag)
                    if date_str:
                        try:
                            # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                            return (dt, DateSource.EXIF) if return_source else dt
                        except ValueError:
                            continue

    except Exception:
        pass

    # Try Google Takeout JSON sidecar file
    takeout_date = _parse_google_takeout_json(photo_path)
    if takeout_date:
        return (takeout_date, DateSource.GOOGLE_TAKEOUT) if return_source else takeout_date

    # Try parsing date from filename
    filename_date = _parse_date_from_filename(photo_path.name)
    if filename_date:
        return (filename_date, DateSource.FILENAME) if return_source else filename_date

    # Fall back to file modification time (unreliable for copied files)
    mtime = photo_path.stat().st_mtime
    dt = datetime.fromtimestamp(mtime)
    return (dt, DateSource.FILE_MTIME) if return_source else dt
