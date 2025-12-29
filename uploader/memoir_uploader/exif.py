"""
EXIF metadata extraction.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


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


def get_photo_date(photo_path: Path) -> datetime:
    """
    Get the date a photo was taken.
    Tries EXIF DateTimeOriginal first, then file modification time.
    """
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
                            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            continue

    except Exception:
        pass

    # Fall back to file modification time
    mtime = photo_path.stat().st_mtime
    return datetime.fromtimestamp(mtime)
