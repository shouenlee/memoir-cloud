"""
Thumbnail generation.
"""

import tempfile
from pathlib import Path
from typing import Tuple

from PIL import Image


THUMBNAIL_WIDTH = 400


def generate_thumbnail(photo_path: Path) -> Tuple[Path, int, int]:
    """
    Generate a WebP thumbnail for a photo.
    
    Args:
        photo_path: Path to the original photo
        
    Returns:
        Tuple of (thumbnail_path, width, height)
    """
    with Image.open(photo_path) as img:
        # Convert to RGB if necessary (for PNG with alpha, etc.)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Calculate new dimensions maintaining aspect ratio
        original_width, original_height = img.size
        ratio = THUMBNAIL_WIDTH / original_width
        new_height = int(original_height * ratio)

        # Resize with high-quality resampling
        thumbnail = img.resize(
            (THUMBNAIL_WIDTH, new_height),
            Image.Resampling.LANCZOS
        )

        # Save as WebP
        temp_file = tempfile.NamedTemporaryFile(suffix=".webp", delete=False)
        thumbnail.save(
            temp_file.name,
            "WEBP",
            quality=85,
            method=6,  # Slower but better compression
        )

        return Path(temp_file.name), THUMBNAIL_WIDTH, new_height
