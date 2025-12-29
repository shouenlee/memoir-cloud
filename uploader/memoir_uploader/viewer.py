"""
Photo viewing and listing service.
"""

import json
from typing import Optional

from azure.storage.blob import BlobServiceClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


class PhotoViewer:
    """Handles viewing photo details from Azure Blob Storage."""

    def __init__(self, connection_string: str):
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)

    def _get_container_index(self, container_name: str) -> dict:
        """Get index.json for a container."""
        container_client = self.blob_service.get_container_client(container_name)
        try:
            blob_client = container_client.get_blob_client("index.json")
            if blob_client.exists():
                data = blob_client.download_blob().readall()
                return json.loads(data)
        except Exception:
            pass
        return {"photos": []}

    def show_photo(self, photo_id: str) -> None:
        """Show detailed information for a photo."""
        # Search all containers for the photo
        for container in self.blob_service.list_containers():
            name = container.name
            # Check if it matches our naming pattern
            if not (len(name) == 7 and name[4:6] == "-Q"):
                continue

            index = self._get_container_index(name)
            
            for photo in index.get("photos", []):
                if photo.get("id") == photo_id:
                    self._display_photo_details(photo, name)
                    return

        raise ValueError(f"Photo not found: {photo_id}")

    def _display_photo_details(self, photo: dict, container: str) -> None:
        """Display formatted photo details."""
        # Build info text
        info = Text()
        info.append("ID: ", style="bold")
        info.append(f"{photo.get('id', 'N/A')}\n")
        
        info.append("Filename: ", style="bold")
        info.append(f"{photo.get('filename', 'N/A')}\n")
        
        info.append("Container: ", style="bold")
        info.append(f"{container}\n")
        
        info.append("Taken At: ", style="bold")
        info.append(f"{photo.get('takenAt', 'N/A')}\n")
        
        info.append("Uploaded At: ", style="bold")
        info.append(f"{photo.get('uploadedAt', 'N/A')}\n")
        
        info.append("Dimensions: ", style="bold")
        info.append(f"{photo.get('width', 0)} × {photo.get('height', 0)}\n")
        
        # Format size
        size_bytes = photo.get("sizeBytes", 0)
        if size_bytes >= 1_000_000:
            size_str = f"{size_bytes / 1_000_000:.1f} MB"
        else:
            size_str = f"{size_bytes / 1_000:.1f} KB"
        info.append("Size: ", style="bold")
        info.append(f"{size_str}\n")
        
        info.append("Hash: ", style="bold")
        info.append(f"{photo.get('hash', 'N/A')[:16]}...\n")
        
        # EXIF data
        exif = photo.get("exif", {})
        if exif:
            info.append("\n")
            info.append("EXIF Data:\n", style="bold underline")
            if exif.get("camera"):
                info.append("  Camera: ", style="bold")
                info.append(f"{exif['camera']}\n")
            if exif.get("focalLength"):
                info.append("  Focal Length: ", style="bold")
                info.append(f"{exif['focalLength']}\n")
            if exif.get("aperture"):
                info.append("  Aperture: ", style="bold")
                info.append(f"{exif['aperture']}\n")
            if exif.get("iso"):
                info.append("  ISO: ", style="bold")
                info.append(f"{exif['iso']}\n")
        
        # Blob paths
        info.append("\n")
        info.append("Blob Paths:\n", style="bold underline")
        info.append("  Original: ", style="bold")
        info.append(f"{photo.get('originalBlob', 'N/A')}\n")
        info.append("  Thumbnail: ", style="bold")
        info.append(f"{photo.get('thumbnailBlob', 'N/A')}\n")

        console.print(Panel(info, title=f"📷 {photo.get('filename', 'Photo')}", border_style="blue"))

    def list_photos(self, container: Optional[str], limit: int) -> None:
        """List photos in a container or all containers."""
        table = Table(title="Photos")
        table.add_column("ID", style="cyan", max_width=12)
        table.add_column("Filename", style="white")
        table.add_column("Container", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("Size", justify="right")

        count = 0
        
        containers_to_search = []
        if container:
            containers_to_search.append(container)
        else:
            for c in self.blob_service.list_containers():
                name = c.name
                if len(name) == 7 and name[4:6] == "-Q":
                    containers_to_search.append(name)
            # Sort descending (newest first)
            containers_to_search.sort(reverse=True)

        for container_name in containers_to_search:
            if count >= limit:
                break
                
            index = self._get_container_index(container_name)
            photos = index.get("photos", [])
            
            # Sort by date descending
            photos.sort(key=lambda p: p.get("takenAt", ""), reverse=True)
            
            for photo in photos:
                if count >= limit:
                    break
                    
                # Format size
                size_bytes = photo.get("sizeBytes", 0)
                if size_bytes >= 1_000_000:
                    size_str = f"{size_bytes / 1_000_000:.1f} MB"
                else:
                    size_str = f"{size_bytes / 1_000:.1f} KB"
                
                # Format date
                taken_at = photo.get("takenAt", "")[:10] if photo.get("takenAt") else "N/A"
                
                table.add_row(
                    photo.get("id", "")[:12],
                    photo.get("filename", "N/A"),
                    container_name,
                    taken_at,
                    size_str,
                )
                count += 1

        if count == 0:
            console.print("⚠️  No photos found")
        else:
            console.print(table)
            if count == limit:
                console.print(f"\n[dim]Showing first {limit} photos. Use --limit to see more.[/dim]")
