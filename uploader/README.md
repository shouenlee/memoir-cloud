# Memoir Uploader

CLI tool for uploading photos to Memoir Cloud storage.

## Installation

```bash
cd uploader
pip install -e .
```

## Configuration

Before using, configure your Azure Storage connection:

```bash
memoir-uploader config --connection-string "DefaultEndpointsProtocol=https;AccountName=..."
```

Configuration is stored in `~/.memoir-uploader/config.json`.

## Usage

### Upload Photos

Upload all photos from a folder:

```bash
memoir-uploader upload ./my-photos
```

Options:
- `--dry-run`: Preview what would be uploaded without uploading
- `-r, --recursive`: Include subdirectories
- `--skip-duplicates`: Skip photos already in storage (by hash)
- `--date YYYY-MM-DD`: Override date for photos without EXIF

Example with date override (useful for scanned photos):
```bash
memoir-uploader upload ./scanned-photos --date 1995-06-15
```

### List Containers

View all photo containers and counts:

```bash
memoir-uploader list
```

### List Photos

View photos in storage:

```bash
memoir-uploader photos              # List recent photos (all containers)
memoir-uploader photos 2024-Q3      # List photos from specific container
memoir-uploader photos --limit 50   # Show more photos
```

### Show Photo Details

View detailed information about a specific photo:

```bash
memoir-uploader show <photo-id>
```

### Delete Photo

Delete a photo by ID:

```bash
memoir-uploader delete <photo-id>
memoir-uploader delete <photo-id> --force  # Skip confirmation
```

## Features

- **EXIF metadata extraction**: Automatically reads photo date, camera, aperture, ISO from EXIF
- **HEIC conversion**: Converts iPhone HEIC photos to JPEG automatically
- **Thumbnail generation**: Creates 400px WebP thumbnails for fast loading
- **Auto container creation**: Creates `{Year}-Q{Quarter}` containers as needed
- **Duplicate detection**: SHA256 hash-based duplicate skipping
- **Progress tracking**: Shows upload progress for large batches
- **Dry-run mode**: Preview uploads without a connection string

## Supported Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- WebP (`.webp`)
- HEIC/HEIF (`.heic`, `.heif`) - Converted to JPEG
