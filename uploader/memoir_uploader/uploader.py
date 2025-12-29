"""
Photo uploader service.
"""

import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from memoir_uploader.exif import extract_exif_data, get_photo_date
from memoir_uploader.thumbnail import generate_thumbnail
from memoir_uploader.converter import convert_heic_to_jpeg

console = Console()

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


class PhotoUploader:
    """Handles uploading photos to Azure Blob Storage."""

    # Content type mapping for image extensions
    CONTENT_TYPES = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    def __init__(self, connection_string: Optional[str]):
        self.connection_string = connection_string
        self.blob_service = None
        if connection_string:
            self.blob_service = BlobServiceClient.from_connection_string(connection_string)

    def _get_content_type(self, extension: str) -> str:
        """Get content type for file extension."""
        return self.CONTENT_TYPES.get(extension.lower(), "application/octet-stream")

    def _get_quarter(self, month: int) -> int:
        """Get quarter number from month."""
        return (month - 1) // 3 + 1

    def _get_container_name(self, date: datetime) -> str:
        """Generate container name from date (lowercase for Azure compatibility)."""
        quarter = self._get_quarter(date.month)
        return f"{date.year}-q{quarter}"

    def _ensure_container(self, container_name: str) -> ContainerClient:
        """Ensure container exists, create if not."""
        container_client = self.blob_service.get_container_client(container_name)
        
        if not container_client.exists():
            console.print(f"📁 Creating container: {container_name}")
            container_client.create_container(public_access="blob")
        
        return container_client

    def _get_container_index(self, container_client: ContainerClient) -> Dict[str, Any]:
        """Get or create index.json for a container."""
        try:
            blob_client = container_client.get_blob_client("index.json")
            if blob_client.exists():
                data = blob_client.download_blob().readall()
                return json.loads(data)
        except Exception:
            pass
        
        return {"photos": []}

    def _save_container_index(
        self, container_client: ContainerClient, index: Dict[str, Any]
    ) -> None:
        """Save index.json to container."""
        blob_client = container_client.get_blob_client("index.json")
        blob_client.upload_blob(
            json.dumps(index, indent=2),
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file for duplicate detection."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _scan_for_photos(self, folder: Path, recursive: bool) -> List[Path]:
        """Scan folder for photo files."""
        photos = []
        
        pattern = "**/*" if recursive else "*"
        for file_path in folder.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                photos.append(file_path)
        
        return sorted(photos)

    def upload_folder(
        self,
        folder: Path,
        dry_run: bool = False,
        recursive: bool = False,
        skip_duplicates: bool = False,
        override_date: Optional[datetime] = None,
    ) -> None:
        """Upload all photos from a folder."""
        photos = self._scan_for_photos(folder, recursive)
        
        if not photos:
            console.print("⚠️  No photos found in folder")
            return

        console.print(f"📷 Found {len(photos)} photos")

        # Filter out photos without valid dates (no JSON metadata)
        no_date_files: List[Path] = []
        valid_photos: List[Path] = []
        
        if not override_date:
            for photo in photos:
                date = get_photo_date(photo)
                if date is None:
                    no_date_files.append(photo)
                else:
                    valid_photos.append(photo)
            
            if no_date_files:
                console.print(f"\n[yellow]⚠️  {len(no_date_files)} files have no JSON metadata (skipping):[/yellow]")
                for f in no_date_files[:10]:
                    console.print(f"   - {f.name}")
                if len(no_date_files) > 10:
                    console.print(f"   ... and {len(no_date_files) - 10} more")
                console.print("[yellow]   Ensure each photo has a .supplemental-metadata.json sidecar file.[/yellow]\n")
            
            photos = valid_photos
        
        if not photos:
            console.print("⚠️  No photos with valid dates to upload")
            return

        if dry_run:
            console.print("\n[yellow]DRY RUN - No files will be uploaded[/yellow]\n")
            for photo in photos:
                if override_date:
                    date = override_date
                else:
                    date = get_photo_date(photo)
                container = self._get_container_name(date)
                console.print(f"  {photo.name} → {container}")
            return

        # Group photos by target container
        by_container: Dict[str, List[tuple]] = {}
        for photo in photos:
            if override_date:
                date = override_date
            else:
                date = get_photo_date(photo)
            container = self._get_container_name(date)
            by_container.setdefault(container, []).append((photo, date))

        # Upload photos
        uploaded = 0
        skipped = 0
        errors = 0

        with Progress() as progress:
            task = progress.add_task("Uploading photos...", total=len(photos))

            for container_name, container_photos in by_container.items():
                container_client = self._ensure_container(container_name)
                index = self._get_container_index(container_client)
                existing_hashes = {p.get("hash") for p in index["photos"] if p.get("hash")}

                for photo_path, photo_date in container_photos:
                    try:
                        # Check for duplicates
                        if skip_duplicates:
                            file_hash = self._compute_file_hash(photo_path)
                            if file_hash in existing_hashes:
                                console.print(f"⏭️  Skipped (duplicate): {photo_path.name}")
                                skipped += 1
                                progress.advance(task)
                                continue
                        else:
                            file_hash = self._compute_file_hash(photo_path)

                        # Process and upload photo
                        photo_id = str(uuid.uuid4())
                        result = self._upload_single_photo(
                            container_client, photo_path, photo_id, photo_date
                        )
                        
                        # Add hash for duplicate detection
                        result["hash"] = file_hash
                        
                        # Add to index
                        index["photos"].append(result)
                        existing_hashes.add(file_hash)
                        
                        uploaded += 1
                        console.print(f"✅ Uploaded: {photo_path.name}")

                    except Exception as e:
                        errors += 1
                        console.print(f"❌ Error uploading {photo_path.name}: {e}")

                    progress.advance(task)

                # Save updated index
                self._save_container_index(container_client, index)

        # Summary
        console.print(f"\n📊 Summary: {uploaded} uploaded, {skipped} skipped, {errors} errors")

    def _upload_single_photo(
        self, container_client: ContainerClient, photo_path: Path, photo_id: str, taken_at: datetime
    ) -> Dict[str, Any]:
        """Upload a single photo with its thumbnail."""
        # Extract EXIF data
        exif_data = extract_exif_data(photo_path)

        # Handle HEIC conversion
        original_path = photo_path
        if photo_path.suffix.lower() in {".heic", ".heif"}:
            original_path = convert_heic_to_jpeg(photo_path)
            original_ext = ".jpg"
        else:
            original_ext = photo_path.suffix.lower()

        # Generate thumbnail
        thumbnail_path, thumb_width, thumb_height = generate_thumbnail(original_path)

        # Get original dimensions
        from PIL import Image
        with Image.open(original_path) as img:
            width, height = img.size

        # Upload original with cache headers (images are immutable, cache for 1 year)
        original_blob_name = f"originals/{photo_id}{original_ext}"
        content_type = self._get_content_type(original_ext)
        with open(original_path, "rb") as f:
            container_client.upload_blob(
                original_blob_name,
                f,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type=content_type,
                    cache_control="public, max-age=31536000, immutable",
                ),
            )

        # Upload thumbnail with cache headers
        thumbnail_blob_name = f"thumbnails/{photo_id}_thumb.webp"
        with open(thumbnail_path, "rb") as f:
            container_client.upload_blob(
                thumbnail_blob_name,
                f,
                overwrite=True,
                content_settings=ContentSettings(
                    content_type="image/webp",
                    cache_control="public, max-age=31536000, immutable",
                ),
            )

        # Clean up temp files
        if original_path != photo_path:
            original_path.unlink()
        thumbnail_path.unlink()

        return {
            "id": photo_id,
            "filename": photo_path.name,
            "originalBlob": original_blob_name,
            "thumbnailBlob": thumbnail_blob_name,
            "takenAt": taken_at.isoformat() + "Z",
            "uploadedAt": datetime.utcnow().isoformat() + "Z",
            "width": width,
            "height": height,
            "sizeBytes": photo_path.stat().st_size,
            "exif": exif_data,
        }

    def list_containers(self) -> None:
        """List all photo containers with counts."""
        table = Table(title="Photo Containers")
        table.add_column("Container", style="cyan")
        table.add_column("Photos", justify="right")
        table.add_column("Size", justify="right")

        total_photos = 0
        total_size = 0

        for container in self.blob_service.list_containers():
            name = container.name
            # Check if it matches our naming pattern (YYYY-qN)
            if not (len(name) == 7 and name[4:6].lower() == "-q"):
                continue

            container_client = self.blob_service.get_container_client(name)
            index = self._get_container_index(container_client)
            
            photo_count = len(index.get("photos", []))
            size_bytes = sum(p.get("sizeBytes", 0) for p in index.get("photos", []))
            
            # Format size
            if size_bytes >= 1_000_000_000:
                size_str = f"{size_bytes / 1_000_000_000:.1f} GB"
            elif size_bytes >= 1_000_000:
                size_str = f"{size_bytes / 1_000_000:.1f} MB"
            else:
                size_str = f"{size_bytes / 1_000:.1f} KB"

            table.add_row(name, str(photo_count), size_str)
            total_photos += photo_count
            total_size += size_bytes

        # Format total size
        if total_size >= 1_000_000_000:
            total_size_str = f"{total_size / 1_000_000_000:.1f} GB"
        elif total_size >= 1_000_000:
            total_size_str = f"{total_size / 1_000_000:.1f} MB"
        else:
            total_size_str = f"{total_size / 1_000:.1f} KB"

        table.add_section()
        table.add_row("[bold]Total[/bold]", f"[bold]{total_photos}[/bold]", f"[bold]{total_size_str}[/bold]")

        console.print(table)
