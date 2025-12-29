"""
HEIC to JPEG conversion.
"""

import tempfile
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF/HEIC opener with Pillow
register_heif_opener()


def convert_heic_to_jpeg(heic_path: Path) -> Path:
    """
    Convert a HEIC/HEIF image to JPEG.
    
    Args:
        heic_path: Path to the HEIC file
        
    Returns:
        Path to the temporary JPEG file
    """
    with Image.open(heic_path) as img:
        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save as JPEG
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        
        # Preserve EXIF data if available
        exif_data = img.info.get("exif")
        
        if exif_data:
            img.save(temp_file.name, "JPEG", quality=95, exif=exif_data)
        else:
            img.save(temp_file.name, "JPEG", quality=95)

        return Path(temp_file.name)
