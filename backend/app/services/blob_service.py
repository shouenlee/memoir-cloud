"""
Azure Blob Storage service for photo management.
"""

import json
import re
from typing import Optional
from datetime import datetime

from azure.storage.blob import BlobServiceClient

from app.config import get_settings
from app.models.schemas import (
    PhotosResponse,
    PhotoDetailResponse,
    QuarterSection,
    PhotoSummary,
    ExifData,
)
from app.services.cache_service import cache_service


def _is_demo_mode() -> bool:
    """Check if running in demo mode (no Azure connection configured)."""
    settings = get_settings()
    return not settings.azure_storage_connection_string

# Demo data for local development
DEMO_PHOTOS = {
    "2025-q4": {
        "photos": [
            {
                "id": "demo-001",
                "filename": "sunset.jpg",
                "originalBlob": "originals/demo-001.jpg",
                "thumbnailBlob": "thumbnails/demo-001_thumb.webp",
                "takenAt": "2025-12-15T16:30:00Z",
                "width": 4032,
                "height": 3024,
                "exif": {"camera": "iPhone 15 Pro", "focalLength": "24mm", "aperture": "f/1.8", "iso": 100}
            },
            {
                "id": "demo-002",
                "filename": "mountains.jpg",
                "originalBlob": "originals/demo-002.jpg",
                "thumbnailBlob": "thumbnails/demo-002_thumb.webp",
                "takenAt": "2025-11-20T10:15:00Z",
                "width": 4032,
                "height": 3024,
                "exif": {"camera": "iPhone 15 Pro", "focalLength": "24mm", "aperture": "f/2.0", "iso": 64}
            },
            {
                "id": "demo-003",
                "filename": "city_lights.jpg",
                "originalBlob": "originals/demo-003.jpg",
                "thumbnailBlob": "thumbnails/demo-003_thumb.webp",
                "takenAt": "2025-10-05T21:45:00Z",
                "width": 3024,
                "height": 4032,
                "exif": {"camera": "iPhone 15 Pro", "focalLength": "24mm", "aperture": "f/1.8", "iso": 800}
            },
        ]
    },
    "2025-q3": {
        "photos": [
            {
                "id": "demo-004",
                "filename": "beach.jpg",
                "originalBlob": "originals/demo-004.jpg",
                "thumbnailBlob": "thumbnails/demo-004_thumb.webp",
                "takenAt": "2025-08-22T14:00:00Z",
                "width": 4032,
                "height": 3024,
                "exif": {"camera": "iPhone 15 Pro", "focalLength": "24mm", "aperture": "f/2.2", "iso": 50}
            },
            {
                "id": "demo-005",
                "filename": "forest.jpg",
                "originalBlob": "originals/demo-005.jpg",
                "thumbnailBlob": "thumbnails/demo-005_thumb.webp",
                "takenAt": "2025-07-10T09:30:00Z",
                "width": 4032,
                "height": 3024,
                "exif": {"camera": "iPhone 15 Pro", "focalLength": "24mm", "aperture": "f/1.8", "iso": 200}
            },
        ]
    },
    "2024-q4": {
        "photos": [
            {
                "id": "demo-006",
                "filename": "snow.jpg",
                "originalBlob": "originals/demo-006.jpg",
                "thumbnailBlob": "thumbnails/demo-006_thumb.webp",
                "takenAt": "2024-12-25T11:00:00Z",
                "width": 4032,
                "height": 3024,
                "exif": {"camera": "iPhone 14 Pro", "focalLength": "24mm", "aperture": "f/1.8", "iso": 100}
            },
        ]
    },
}


class BlobService:
    """Service for interacting with Azure Blob Storage."""

    def __init__(self):
        self._client: Optional[BlobServiceClient] = None

    @property
    def _demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return _is_demo_mode()

    @property
    def client(self) -> BlobServiceClient:
        """Lazy initialization of blob service client."""
        if self._client is None:
            settings = get_settings()
            if settings.azure_storage_connection_string:
                self._client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
            else:
                raise ValueError("Azure Storage connection string not configured")
        return self._client

    def _parse_container_name(self, name: str) -> Optional[tuple[int, int]]:
        """
        Parse container name to extract year and quarter.
        Returns (year, quarter) or None if not a valid photo container.
        """
        match = re.match(r"^(\d{4})-q([1-4])$", name, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    def _get_quarter_label(self, quarter: int) -> str:
        """Get human-readable label for a quarter."""
        labels = {
            1: "January - March",
            2: "April - June",
            3: "July - September",
            4: "October - December",
        }
        return labels.get(quarter, f"Q{quarter}")

    async def get_available_years(self) -> list[int]:
        """Get list of years that have photo containers."""
        # Demo mode - return demo years
        if self._demo_mode:
            years = set()
            for container_name in DEMO_PHOTOS.keys():
                parsed = self._parse_container_name(container_name)
                if parsed:
                    years.add(parsed[0])
            return sorted(years, reverse=True)

        cache_key = "available_years"
        cached = cache_service.get(cache_key)
        if cached is not None:
            return cached

        years = set()
        containers = self.client.list_containers()
        
        for container in containers:
            parsed = self._parse_container_name(container.name)
            if parsed:
                years.add(parsed[0])

        result = sorted(years, reverse=True)
        cache_service.set(cache_key, result)
        return result

    async def _get_container_index(self, container_name: str) -> Optional[dict]:
        """Fetch and cache index.json from a container."""
        # Demo mode - return demo data
        if self._demo_mode:
            return DEMO_PHOTOS.get(container_name)

        cache_key = f"index:{container_name}"
        cached = cache_service.get(cache_key)
        if cached is not None:
            return cached

        try:
            container_client = self.client.get_container_client(container_name)
            blob_client = container_client.get_blob_client("index.json")
            
            if not blob_client.exists():
                return None
                
            data = blob_client.download_blob().readall()
            index = json.loads(data)
            cache_service.set(cache_key, index)
            return index
        except Exception:
            return None

    async def get_photos_by_year(
        self, year: int, cursor: Optional[str], limit: int
    ) -> Optional[PhotosResponse]:
        """
        Get photos for a year, grouped by quarter.
        Supports cursor-based pagination.
        """
        # Demo mode - use placeholder images
        if self._demo_mode:
            base_url = "https://picsum.photos"
        else:
            settings = get_settings()
            base_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
        
        # Get all containers for this year
        containers = []
        if self._demo_mode:
            for container_name in DEMO_PHOTOS.keys():
                parsed = self._parse_container_name(container_name)
                if parsed and parsed[0] == year:
                    containers.append((container_name, parsed[1]))
        else:
            for container in self.client.list_containers():
                parsed = self._parse_container_name(container.name)
                if parsed and parsed[0] == year:
                    containers.append((container.name, parsed[1]))

        if not containers:
            return None

        # Sort by quarter descending (Q4 first)
        containers.sort(key=lambda x: x[1], reverse=True)

        # Parse cursor timestamp
        cursor_dt = None
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            except ValueError:
                pass

        sections: list[QuarterSection] = []
        total_photos = 0
        next_cursor: Optional[str] = None

        for container_name, quarter in containers:
            index = await self._get_container_index(container_name)
            if not index or "photos" not in index:
                continue

            # Filter and sort photos
            photos = index["photos"]
            photos.sort(key=lambda p: p.get("takenAt", ""), reverse=True)

            # Apply cursor filter
            if cursor_dt:
                photos = [
                    p for p in photos
                    if datetime.fromisoformat(p["takenAt"].replace("Z", "+00:00")) < cursor_dt
                ]

            if not photos:
                continue

            # Build photo summaries
            section_photos: list[PhotoSummary] = []
            for photo in photos:
                if total_photos >= limit:
                    next_cursor = photo.get("takenAt")
                    break

                # Generate URLs based on mode
                if self._demo_mode:
                    # Use picsum.photos with seed for consistent images
                    seed = hash(photo["id"]) % 1000
                    thumbnail_url = f"{base_url}/seed/{seed}/300/300"
                    original_url = f"{base_url}/seed/{seed}/{photo.get('width', 1200)}/{photo.get('height', 800)}"
                else:
                    thumbnail_url = f"{base_url}/{container_name}/{photo['thumbnailBlob']}"
                    original_url = f"{base_url}/{container_name}/{photo['originalBlob']}"

                section_photos.append(
                    PhotoSummary(
                        id=photo["id"],
                        thumbnailUrl=thumbnail_url,
                        originalUrl=original_url,
                        takenAt=photo["takenAt"],
                        width=photo.get("width", 0),
                        height=photo.get("height", 0),
                        aspectRatio=photo.get("width", 1) / max(photo.get("height", 1), 1),
                    )
                )
                total_photos += 1

            if section_photos:
                sections.append(
                    QuarterSection(
                        quarter=f"Q{quarter}",
                        label=f"{self._get_quarter_label(quarter)} {year}",
                        photos=section_photos,
                    )
                )

            if total_photos >= limit:
                break

        return PhotosResponse(
            year=year,
            sections=sections,
            nextCursor=next_cursor,
            hasMore=next_cursor is not None,
        )

    async def get_photo_by_id(self, photo_id: str) -> Optional[PhotoDetailResponse]:
        """Get detailed information for a single photo."""
        # Demo mode - use placeholder images
        if self._demo_mode:
            base_url = "https://picsum.photos"
            # Search demo photos
            for container_name, index_data in DEMO_PHOTOS.items():
                for photo in index_data["photos"]:
                    if photo["id"] == photo_id:
                        seed = hash(photo["id"]) % 1000
                        return PhotoDetailResponse(
                            id=photo["id"],
                            thumbnailUrl=f"{base_url}/seed/{seed}/300/300",
                            originalUrl=f"{base_url}/seed/{seed}/{photo.get('width', 1200)}/{photo.get('height', 800)}",
                            takenAt=photo["takenAt"],
                            width=photo.get("width", 0),
                            height=photo.get("height", 0),
                            exif=ExifData(
                                camera=photo.get("exif", {}).get("camera"),
                                focalLength=photo.get("exif", {}).get("focalLength"),
                                aperture=photo.get("exif", {}).get("aperture"),
                                iso=photo.get("exif", {}).get("iso"),
                            ) if photo.get("exif") else None,
                        )
            return None

        settings = get_settings()
        base_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"

        # Search all containers for the photo
        for container in self.client.list_containers():
            parsed = self._parse_container_name(container.name)
            if not parsed:
                continue

            index = await self._get_container_index(container.name)
            if not index or "photos" not in index:
                continue

            for photo in index["photos"]:
                if photo["id"] == photo_id:
                    return PhotoDetailResponse(
                        id=photo["id"],
                        thumbnailUrl=f"{base_url}/{container.name}/{photo['thumbnailBlob']}",
                        originalUrl=f"{base_url}/{container.name}/{photo['originalBlob']}",
                        takenAt=photo["takenAt"],
                        width=photo.get("width", 0),
                        height=photo.get("height", 0),
                        exif=ExifData(
                            camera=photo.get("exif", {}).get("camera"),
                            focalLength=photo.get("exif", {}).get("focalLength"),
                            aperture=photo.get("exif", {}).get("aperture"),
                            iso=photo.get("exif", {}).get("iso"),
                        ) if photo.get("exif") else None,
                    )

        return None


# Singleton instance
blob_service = BlobService()
