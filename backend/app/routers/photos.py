"""
Photos API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from app.models.schemas import YearsResponse, PhotosResponse, PhotoDetailResponse
from app.services.blob_service import blob_service

router = APIRouter()


@router.get("/years", response_model=YearsResponse)
async def get_years():
    """
    Get list of years that have photos.
    Returns years in descending order with the most recent as default.
    """
    years = await blob_service.get_available_years()
    
    if not years:
        return YearsResponse(years=[], default=None)
    
    return YearsResponse(
        years=sorted(years, reverse=True),
        default=max(years)
    )


@router.get("/photos/{year}", response_model=PhotosResponse)
async def get_photos(
    year: int,
    cursor: Optional[str] = Query(None, description="Pagination cursor (ISO timestamp)"),
    limit: int = Query(50, ge=1, le=100, description="Number of photos to return")
):
    """
    Get photos for a specific year, grouped by quarter.
    Supports cursor-based pagination for infinite scroll.
    """
    result = await blob_service.get_photos_by_year(year, cursor, limit)
    
    if result is None:
        raise HTTPException(status_code=404, detail=f"No photos found for year {year}")
    
    return result


@router.get("/photo/{photo_id}", response_model=PhotoDetailResponse)
async def get_photo(photo_id: str):
    """
    Get detailed metadata for a single photo.
    Used for lightbox view with EXIF data.
    """
    photo = await blob_service.get_photo_by_id(photo_id)
    
    if photo is None:
        raise HTTPException(status_code=404, detail=f"Photo not found: {photo_id}")
    
    return photo
