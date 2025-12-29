"""
In-memory caching service for index.json files.
"""

from typing import Any, Optional
from datetime import datetime, timedelta

from cachetools import TTLCache

from app.config import get_settings


class CacheService:
    """
    Simple in-memory cache with TTL.
    Estimated memory usage: ~1KB per 100 photos in index.json.
    Safe for galleries with thousands of photos.
    """

    def __init__(self):
        settings = get_settings()
        # Max 100 items (containers), 5-minute TTL
        self._cache: TTLCache = TTLCache(
            maxsize=100,
            ttl=settings.cache_ttl_seconds
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def invalidate_container(self, container_name: str) -> None:
        """Invalidate cache for a specific container."""
        self.delete(f"index:{container_name}")
        self.delete("available_years")


# Singleton instance
cache_service = CacheService()
