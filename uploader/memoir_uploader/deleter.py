"""
Photo deletion service.
"""

import json
from typing import Optional, Tuple

from azure.storage.blob import BlobServiceClient, ContainerClient
from rich.console import Console

console = Console()


class PhotoDeleter:
    """Handles deleting photos from Azure Blob Storage."""

    def __init__(self, connection_string: str):
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)

    def _find_photo(self, photo_id: str) -> Optional[Tuple[ContainerClient, dict, int]]:
        """
        Find a photo by ID across all containers.
        Returns (container_client, index_data, photo_index) or None.
        """
        for container in self.blob_service.list_containers():
            name = container.name
            # Check if it matches our naming pattern
            if not (len(name) == 7 and name[4:6] == "-Q"):
                continue

            container_client = self.blob_service.get_container_client(name)
            
            try:
                blob_client = container_client.get_blob_client("index.json")
                if not blob_client.exists():
                    continue
                    
                data = blob_client.download_blob().readall()
                index = json.loads(data)
                
                for i, photo in enumerate(index.get("photos", [])):
                    if photo.get("id") == photo_id:
                        return container_client, index, i
            except Exception:
                continue

        return None

    def delete_photo(self, photo_id: str) -> None:
        """Delete a photo by ID."""
        result = self._find_photo(photo_id)
        
        if result is None:
            raise ValueError(f"Photo not found: {photo_id}")

        container_client, index, photo_index = result
        photo = index["photos"][photo_index]

        console.print(f"🗑️  Deleting photo: {photo.get('filename', photo_id)}")

        # Delete original blob
        original_blob = photo.get("originalBlob")
        if original_blob:
            try:
                container_client.delete_blob(original_blob)
                console.print(f"  ✓ Deleted original: {original_blob}")
            except Exception as e:
                console.print(f"  ⚠️  Could not delete original: {e}")

        # Delete thumbnail blob
        thumbnail_blob = photo.get("thumbnailBlob")
        if thumbnail_blob:
            try:
                container_client.delete_blob(thumbnail_blob)
                console.print(f"  ✓ Deleted thumbnail: {thumbnail_blob}")
            except Exception as e:
                console.print(f"  ⚠️  Could not delete thumbnail: {e}")

        # Update index
        index["photos"].pop(photo_index)
        
        blob_client = container_client.get_blob_client("index.json")
        blob_client.upload_blob(
            json.dumps(index, indent=2),
            overwrite=True,
            content_settings={"content_type": "application/json"},
        )
        console.print("  ✓ Updated index.json")
