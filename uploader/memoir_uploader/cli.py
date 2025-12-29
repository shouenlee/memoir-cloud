"""
CLI entry point for memoir-uploader.
"""

import click
from pathlib import Path
from datetime import datetime

from memoir_uploader.config import load_config, save_config
from memoir_uploader.uploader import PhotoUploader
from memoir_uploader.deleter import PhotoDeleter


@click.group()
@click.version_option()
def cli():
    """Memoir Uploader - Upload photos to Memoir Cloud storage."""
    pass


@cli.command()
@click.option(
    "--connection-string",
    prompt="Azure Storage Connection String",
    hide_input=True,
    help="Azure Storage connection string",
)
def config(connection_string: str):
    """Configure Azure Storage connection."""
    save_config({"connection_string": connection_string})
    click.echo("✅ Configuration saved to ~/.memoir-uploader/config.json")


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Preview without uploading")
@click.option("--recursive", "-r", is_flag=True, help="Include subdirectories")
@click.option("--skip-duplicates", is_flag=True, help="Skip photos already in storage")
@click.option("--skip-no-date", is_flag=True, help="Skip photos with no EXIF or filename date")
@click.option(
    "--date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Override date for photos without EXIF (YYYY-MM-DD)",
)
def upload(folder: Path, dry_run: bool, recursive: bool, skip_duplicates: bool, skip_no_date: bool, date: datetime):
    """Upload photos from a folder to blob storage."""
    config_data = load_config()
    
    # Allow dry-run without connection string
    if not dry_run and not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    connection_string = config_data.get("connection_string")
    uploader = PhotoUploader(connection_string)
    
    try:
        uploader.upload_folder(
            folder,
            dry_run=dry_run,
            recursive=recursive,
            skip_duplicates=skip_duplicates,
            override_date=date,
            skip_no_date=skip_no_date,
        )
    except Exception as e:
        click.echo(f"❌ Upload failed: {e}")
        raise click.Abort()


@cli.command("list")
def list_containers():
    """List all photo containers and counts."""
    config_data = load_config()
    if not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    uploader = PhotoUploader(config_data["connection_string"])
    uploader.list_containers()


@cli.command()
@click.argument("photo_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
def delete(photo_id: str, force: bool):
    """Delete a photo by ID."""
    config_data = load_config()
    if not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    if not force:
        click.confirm(f"Are you sure you want to delete photo {photo_id}?", abort=True)

    deleter = PhotoDeleter(config_data["connection_string"])
    
    try:
        deleter.delete_photo(photo_id)
        click.echo(f"✅ Photo {photo_id} deleted successfully")
    except Exception as e:
        click.echo(f"❌ Delete failed: {e}")
        raise click.Abort()


@cli.command()
@click.argument("photo_id")
def show(photo_id: str):
    """Show details of a photo by ID."""
    config_data = load_config()
    if not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    from memoir_uploader.viewer import PhotoViewer
    
    viewer = PhotoViewer(config_data["connection_string"])
    
    try:
        viewer.show_photo(photo_id)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.argument("container", required=False)
@click.option("--limit", "-n", default=20, help="Number of photos to show")
def photos(container: str, limit: int):
    """List photos in a container (or all containers)."""
    config_data = load_config()
    if not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    from memoir_uploader.viewer import PhotoViewer
    
    viewer = PhotoViewer(config_data["connection_string"])
    
    try:
        viewer.list_photos(container, limit)
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--container", "-c", help="Only clear a specific container (e.g., 2025-q4)")
def clear(force: bool, container: str):
    """Clear all photo containers from blob storage.
    
    This will delete all photos and their metadata. Use with caution!
    """
    config_data = load_config()
    if not config_data.get("connection_string"):
        click.echo("❌ No connection string configured. Run: memoir-uploader config")
        raise click.Abort()

    from azure.storage.blob import BlobServiceClient
    
    blob_service = BlobServiceClient.from_connection_string(config_data["connection_string"])
    
    # Find containers to delete
    containers_to_delete = []
    for c in blob_service.list_containers():
        # Match photo containers (YYYY-qN format)
        if len(c.name) == 7 and c.name[4:6].lower() == "-q":
            if container is None or c.name == container:
                containers_to_delete.append(c.name)
    
    if not containers_to_delete:
        if container:
            click.echo(f"❌ Container '{container}' not found")
        else:
            click.echo("ℹ️  No photo containers found")
        return
    
    # Show what will be deleted
    click.echo("📦 Containers to delete:")
    for name in sorted(containers_to_delete):
        # Get photo count
        try:
            client = blob_service.get_container_client(name)
            index_blob = client.get_blob_client("index.json")
            import json
            data = json.loads(index_blob.download_blob().readall())
            count = len(data.get("photos", []))
            click.echo(f"   - {name} ({count} photos)")
        except Exception:
            click.echo(f"   - {name}")
    
    if not force:
        click.confirm("\n⚠️  This will permanently delete all photos. Continue?", abort=True)
    
    # Delete containers
    for name in containers_to_delete:
        click.echo(f"🗑️  Deleting {name}...")
        blob_service.delete_container(name)
    
    click.echo(f"\n✅ Cleared {len(containers_to_delete)} container(s)")


if __name__ == "__main__":
    cli()
