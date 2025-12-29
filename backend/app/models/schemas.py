"""
Pydantic schemas for API request/response models.
"""

from typing import Optional, Literal
from pydantic import BaseModel


# ============== Photo Schemas ==============

class ExifData(BaseModel):
    """EXIF metadata from a photo."""
    camera: Optional[str] = None
    focalLength: Optional[str] = None
    aperture: Optional[str] = None
    iso: Optional[int] = None


class PhotoSummary(BaseModel):
    """Photo summary for gallery grid view."""
    id: str
    thumbnailUrl: str
    originalUrl: str
    takenAt: str
    width: int
    height: int
    aspectRatio: float


class PhotoDetailResponse(BaseModel):
    """Detailed photo information for lightbox view."""
    id: str
    thumbnailUrl: str
    originalUrl: str
    takenAt: str
    width: int
    height: int
    exif: Optional[ExifData] = None


class QuarterSection(BaseModel):
    """A section of photos grouped by quarter."""
    quarter: str  # e.g., "Q4"
    label: str  # e.g., "October - December 2025"
    photos: list[PhotoSummary]


class PhotosResponse(BaseModel):
    """Response for GET /api/photos/{year}."""
    year: int
    sections: list[QuarterSection]
    nextCursor: Optional[str] = None
    hasMore: bool


class YearsResponse(BaseModel):
    """Response for GET /api/years."""
    years: list[int]
    default: Optional[int] = None


# ============== Telemetry Schemas ==============

class TelemetryEvent(BaseModel):
    """Telemetry event from frontend."""
    event: Literal["page_view", "photo_view"]
    photoId: Optional[str] = None
    timestamp: Optional[str] = None
    sessionId: str
