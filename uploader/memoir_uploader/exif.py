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


def _find_google_takeout_json(photo_path: Path) -> Optional[Path]:
    """
    Find the Google Takeout JSON sidecar file for a photo.
    
    Google Takeout uses several naming patterns:
    - photo.jpg.supplemental-metadata.json (full name)
    - photo.jpg.suppl.json (truncated)
    - photo.jpg.supp.json (truncated)
    - photo.jpg.supplemen.json (truncated)
    - photo.jpg.json (simple)
    
    Also handles truncated filenames where the JSON name may be cut off.
    """
    parent = photo_path.parent
    base = photo_path.name
    
    # Common JSON sidecar patterns in order of preference
    patterns = [
        f"{base}.supplemental-metadata.json",
        f"{base}.suppl.json",
        f"{base}.supp.json",
        f"{base}.json",
    ]
    
    # Check exact matches first
    for pattern in patterns:
        json_path = parent / pattern
        if json_path.exists():
            return json_path
    
    # Check for truncated JSON filenames (e.g., .supplemen.json, .supplemental-metada.json)
    # Look for any JSON file that starts with the photo name + ".supp"
    for json_file in parent.glob(f"{base}.supp*.json"):
        return json_file
    
    # Handle edited photos: "photo-edited.jpg" -> try "photo.jpg.*.json"
    name = photo_path.stem
    suffix = photo_path.suffix
    if "-edited" in name:
        base_name = name.replace("-edited", "")
        for pattern in patterns:
            json_path = parent / pattern.replace(base, f"{base_name}{suffix}")
            if json_path.exists():
                return json_path
        for json_file in parent.glob(f"{base_name}{suffix}.supp*.json"):
            return json_file
    
    # Handle "(1)" style duplicates: "photo(1).jpg" -> try "photo.jpg.*.json"
    if name.endswith(")") and "(" in name:
        base_name = re.sub(r"\(\d+\)$", "", name)
        for pattern in patterns:
            json_path = parent / pattern.replace(base, f"{base_name}{suffix}")
            if json_path.exists():
                return json_path
        for json_file in parent.glob(f"{base_name}{suffix}.supp*.json"):
            return json_file
    
    return None


def _parse_google_takeout_json(photo_path: Path) -> Optional[datetime]:
    """
    Look for a Google Takeout JSON sidecar file and extract photoTakenTime.
    Returns None if no JSON file found or no valid timestamp.
    """
    json_path = _find_google_takeout_json(photo_path)
    if not json_path:
        return None
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Use photoTakenTime only (the actual photo timestamp)
        if "photoTakenTime" in data and "timestamp" in data["photoTakenTime"]:
            timestamp = int(data["photoTakenTime"]["timestamp"])
            return datetime.fromtimestamp(timestamp)
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        pass
    
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


def get_photo_date(photo_path: Path) -> Optional[datetime]:
    """
    Get the date a photo was taken from the Google Takeout JSON sidecar file.
    
    Returns None if no JSON file found or no valid photoTakenTime.
    Photos without a valid date should be skipped.
    """
    return _parse_google_takeout_json(photo_path)
