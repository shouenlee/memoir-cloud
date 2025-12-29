# Memoir Cloud - Technical Specification

> **Status:** APPROVED - Ready for implementation  
> **Last Updated:** 2025-12-28  
> **Version:** 1.0.0

---

## 1. Overview

**Memoir Cloud** is a personal photo gallery web application hosted on Azure. The site owner uploads photos via a CLI tool, and visitors can browse photos organized by year and quarter in a responsive gallery interface.

### 1.1 Goals
- Simple, fast photo gallery for personal memories
- Automatic organization by photo date (from EXIF metadata)
- CDN-accelerated delivery via Azure Front Door
- Telemetry tracking for visitor analytics
- Automated deployment via GitHub Actions

### 1.2 Non-Goals (v1)
- User authentication for viewing
- Photo comments or social features
- Photo editing capabilities
- Multi-user/multi-gallery support
- Photo captions/descriptions

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Azure Front Door (CDN)                           │
│  - Caches static assets (React app)                                     │
│  - Caches photos from blob storage                                      │
│  - Routes /api/* to App Service                                         │
│  - Routes /photos/* to Blob Storage                                     │
└─────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────────┐
│     Azure App Service         │   │      Azure Blob Storage           │
│     (Python FastAPI)          │   │                                   │
│                               │   │  Containers:                      │
│  Endpoints:                   │   │  ├── 2025-Q4/                     │
│  - GET /api/years             │   │  │   ├── originals/               │
│  - GET /api/photos/{year}     │   │  │   └── thumbnails/              │
│  - GET /api/photo/{id}        │   │  ├── 2025-Q3/                     │
│  - POST /api/telemetry        │   │  │   ├── originals/               │
│                               │   │  │   └── thumbnails/              │
└───────────────────────────────┘   │  └── ...                          │
            │                       └───────────────────────────────────┘
            │
            ▼
┌───────────────────────────────┐
│    Application Insights       │
│                               │
│  Tracks:                      │
│  - Page views                 │
│  - Photo views                │
│  - User geolocation           │
│  - Session data               │
└───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        ADMIN (Local Machine)                            │
│                                                                         │
│   memoir-uploader CLI                                                   │
│   - Reads EXIF metadata from photos                                     │
│   - Converts HEIC to JPEG                                               │
│   - Creates containers if needed ({Year}-{Quarter})                     │
│   - Generates thumbnails (400px wide)                                   │
│   - Uploads originals + thumbnails to Blob Storage                      │
│   - Supports photo deletion                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Blob Storage Schema

### 3.1 Container Naming Convention
```
{Year}-Q{Quarter}
```
Examples: `2025-Q4`, `2025-Q3`, `2024-Q1`

### 3.2 Blob Structure Within Container
```
{container}/
├── originals/
│   ├── {uuid}.{ext}           # Full-resolution photo
│   └── ...
├── thumbnails/
│   ├── {uuid}_thumb.webp      # 400px wide thumbnail (WebP for compression)
│   └── ...
└── index.json                 # Metadata index for the container
```

### 3.3 Photo Metadata (stored in index.json)
```json
{
  "photos": [
    {
      "id": "uuid-v4",
      "filename": "original_filename.jpg",
      "originalBlob": "originals/uuid.jpg",
      "thumbnailBlob": "thumbnails/uuid_thumb.webp",
      "takenAt": "2025-10-15T14:30:00Z",
      "uploadedAt": "2025-12-28T10:00:00Z",
      "width": 4032,
      "height": 3024,
      "sizeBytes": 4500000,
      "exif": {
        "camera": "iPhone 15 Pro",
        "focalLength": "24mm",
        "aperture": "f/1.8",
        "iso": 100
      }
    }
  ]
}
```

### 3.4 Design Decisions

| Decision | Rationale |
|----------|-----------|
| Quarterly containers | Balance between too many containers (monthly) and too few (yearly). Keeps container sizes manageable. |
| UUID filenames | Avoid collisions, hide original filenames from public URLs |
| WebP thumbnails | ~30% smaller than JPEG at same quality, supported by all modern browsers |
| index.json per container | Fast metadata retrieval without scanning blobs. Alternative considered: Azure Table Storage |

**✅ Design Decisions:**
1. **Metadata storage:** index.json only (no blob metadata redundancy for simplicity)
2. **Caching:** index.json cached in App Service memory with 5-minute TTL (estimated ~1KB per 100 photos, safe for thousands of photos)
3. **Batch size:** No hard limit; uploader processes files sequentially to manage memory

---

## 4. API Design

### 4.1 Base URL
```
App Service: https://<app-name>.azurewebsites.net/api
Via CDN:     https://<frontdoor-name>.azurefd.net/api
```

> **Note:** Using Azure-provided URLs for v1. Custom domain to be added later.

### 4.2 Endpoints

#### `GET /api/years`
Returns list of years that have photos.

**Response:**
```json
{
  "years": [2025, 2024, 2023],
  "default": 2025
}
```

#### `GET /api/photos/{year}?cursor={cursor}&limit={limit}`
Returns photos for a given year, paginated for infinite scroll.

**Parameters:**
- `year` (path): Year to fetch photos for
- `cursor` (query, optional): Pagination cursor (timestamp-based)
- `limit` (query, optional): Number of photos to return (default: 50, max: 100)

**Response:**
```json
{
  "year": 2025,
  "sections": [
    {
      "quarter": "Q4",
      "label": "October - December 2025",
      "photos": [
        {
          "id": "uuid",
          "thumbnailUrl": "https://cdn.../2025-Q4/thumbnails/uuid_thumb.webp",
          "originalUrl": "https://cdn.../2025-Q4/originals/uuid.jpg",
          "takenAt": "2025-12-15T14:30:00Z",
          "width": 4032,
          "height": 3024,
          "aspectRatio": 1.33
        }
      ]
    },
    {
      "quarter": "Q3",
      "label": "July - September 2025",
      "photos": [...]
    }
  ],
  "nextCursor": "2025-07-01T00:00:00Z",
  "hasMore": true
}
```

#### `GET /api/photo/{id}`
Returns full metadata for a single photo (for lightbox view).

**Response:**
```json
{
  "id": "uuid",
  "thumbnailUrl": "...",
  "originalUrl": "...",
  "takenAt": "2025-12-15T14:30:00Z",
  "width": 4032,
  "height": 3024,
  "exif": {
    "camera": "iPhone 15 Pro",
    "focalLength": "24mm",
    "aperture": "f/1.8",
    "iso": 100
  }
}
```

#### `POST /api/telemetry`
Records telemetry event (called from frontend).

**Request:**
```json
{
  "event": "page_view" | "photo_view",
  "photoId": "uuid",           // only for photo_view
  "timestamp": "ISO-8601",
  "sessionId": "client-generated-uuid"
}
```

**Note:** IP address and geolocation are extracted server-side from request headers (X-Forwarded-For via Front Door).

---

## 5. Frontend Design

### 5.1 Technology Stack
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling (utility-first, great for responsive galleries)
- **React Query** for data fetching and caching
- **React Router** for year-based routing
- **Dark mode** support (system preference detection + manual toggle)

### 5.2 Routes
```
/           → Redirect to /{latestYear}
/{year}     → Gallery view for specific year
```

### 5.3 Component Hierarchy
```
<App>
├── <Header>
│   ├── <YearTabs years={[2025, 2024, 2023]} selected={2025} />
│   └── <ThemeToggle />  <!-- Light/Dark mode switch -->
├── <Gallery year={2025}>
│   ├── <QuarterSection quarter="Q4" label="Oct-Dec 2025">
│   │   └── <PhotoGrid photos={[...]} onPhotoClick={openLightbox} />
│   ├── <QuarterSection quarter="Q3" label="Jul-Sep 2025">
│   │   └── <PhotoGrid photos={[...]} />
│   └── <InfiniteScrollTrigger onIntersect={loadMore} />
└── <Lightbox photo={selectedPhoto} onClose={closeLightbox} />
```

### 5.4 Lightbox Features
- Full-resolution image display
- Keyboard navigation (←/→ for prev/next, Esc to close)
- Swipe gestures on mobile
- EXIF metadata display (optional toggle)
- Preload adjacent images

### 5.5 Responsive Breakpoints
| Breakpoint | Columns | Thumbnail Size |
|------------|---------|----------------|
| Mobile (<640px) | 2 | 150px |
| Tablet (640-1024px) | 3 | 200px |
| Desktop (1024-1440px) | 4 | 250px |
| Large (>1440px) | 5 | 300px |

---

## 6. Uploader CLI Tool

### 6.1 Name
`memoir-uploader`

### 6.2 Technology
- Python 3.11+
- Click (CLI framework)
- Pillow (image processing, thumbnail generation)
- pillow-heif (HEIC to JPEG conversion)
- Azure Storage Blob SDK

### 6.3 Commands

#### `memoir-uploader upload <folder>`
Uploads all photos from a local folder to blob storage.

```bash
memoir-uploader upload ./vacation-photos --dry-run
memoir-uploader upload ./vacation-photos
```

**Behavior:**
1. Scan folder for image files (jpg, jpeg, png, heic, webp)
2. For each photo:
   - Extract EXIF date taken (fallback to file modified date)
   - **Convert HEIC to JPEG** (preserving EXIF metadata)
   - Determine target container ({Year}-Q{Quarter})
   - Generate UUID for filename
   - Generate thumbnail (400px wide, WebP)
   - Upload original (JPEG for HEIC, original format otherwise) and thumbnail
3. Update index.json in each affected container
4. Print summary

**Options:**
- `--dry-run`: Show what would be uploaded without uploading
- `--recursive`: Include subdirectories
- `--skip-duplicates`: Skip photos already in storage (by hash)

#### `memoir-uploader list`
Lists all containers and photo counts.

```bash
memoir-uploader list

Container     Photos  Size
-----------   ------  --------
2025-Q4       145     1.2 GB
2025-Q3       230     2.1 GB
2024-Q4       180     1.5 GB
```

#### `memoir-uploader delete <photo-id>`
Deletes a photo from blob storage.

```bash
memoir-uploader delete abc123-uuid
memoir-uploader delete abc123-uuid --force  # Skip confirmation
```

**Behavior:**
1. Find photo by ID across all containers
2. Prompt for confirmation (unless --force)
3. Delete original blob
4. Delete thumbnail blob
5. Update index.json to remove entry
6. Print confirmation

#### `memoir-uploader config`
Configure Azure connection.

```bash
memoir-uploader config --connection-string "DefaultEndpointsProtocol=..."
# Stores in ~/.memoir-uploader/config.json
```

---

## 7. Infrastructure (Bicep)

### 7.1 Resources to Create

| Resource | Name | SKU/Tier |
|----------|------|----------|
| Resource Group | rg-memoir-cloud | - |
| Storage Account | stmemoircloud | Standard_LRS |
| App Service Plan | plan-memoir-cloud | B1 (Basic) |
| App Service | app-memoir-cloud | Python 3.11 |
| Application Insights | appi-memoir-cloud | - |
| Front Door | afd-memoir-cloud | Standard |

### 7.2 File Structure
```
infra/
├── main.bicep              # Main orchestration
├── modules/
│   ├── storage.bicep       # Storage account + CORS
│   ├── appservice.bicep    # App Service Plan + Web App
│   ├── insights.bicep      # Application Insights
│   └── frontdoor.bicep     # Front Door + origins
└── parameters/
    └── prod.bicepparam     # Production parameters
```

### 7.3 Key Configuration

**Storage Account CORS** (for direct browser access via CDN):
```json
{
  "allowedOrigins": ["https://<frontdoor-name>.azurefd.net"],
  "allowedMethods": ["GET", "HEAD"],
  "allowedHeaders": ["*"],
  "exposedHeaders": ["*"],
  "maxAgeInSeconds": 86400
}
```

> **Note:** Update allowedOrigins when custom domain is added.

**Front Door Routes:**
| Route | Origin | Caching |
|-------|--------|---------|
| `/api/*` | App Service | No cache |
| `/photos/*` | Blob Storage | 7 days |
| `/*` | App Service (static) | 1 hour |

---

## 8. Telemetry & Analytics

### 8.1 Events Tracked

| Event | Properties |
|-------|------------|
| `page_view` | year, sessionId, timestamp |
| `photo_view` | photoId, year, quarter, sessionId, timestamp |

### 8.2 Automatic Properties (Server-Side)
Extracted from request headers:
- IP Address (from X-Forwarded-For)
- Country (from X-Azure-ClientIPCountry if available, or IP lookup)
- City (IP geolocation lookup)
- User Agent

### 8.3 Application Insights Integration
- Python backend uses `opencensus-ext-azure` or `azure-monitor-opentelemetry`
- Custom events sent via `track_event()`
- Frontend sends events to `/api/telemetry` endpoint (not directly to App Insights)

---

## 9. CI/CD Pipeline

### 9.1 Workflow Triggers
```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

### 9.2 Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Build     │───▶│    Test     │───▶│  Deploy     │───▶│   Verify    │
│   Frontend  │    │   (lint,    │    │  Infra +    │    │   (smoke    │
│   + Backend │    │   pytest)   │    │  App        │    │    test)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 9.3 GitHub Secrets Required
| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure login |
| `AZURE_SUBSCRIPTION_ID` | Target subscription |
| `AZURE_RG_NAME` | Resource group name |

### 9.4 Deployment Strategy
- Bicep deployment runs first (idempotent)
- Frontend build output copied to backend `/static` folder
- Backend deployed as ZIP to App Service
- Health check after deployment

---

## 10. Project Structure

```
memoir-cloud/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── docs/
│   └── SPEC.md                 # This file
├── infra/
│   ├── main.bicep
│   ├── modules/
│   │   ├── storage.bicep
│   │   ├── appservice.bicep
│   │   ├── insights.bicep
│   │   └── frontdoor.bicep
│   └── parameters/
│       └── prod.bicepparam
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   │   └── ThemeContext.tsx  # Dark mode state
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── photos.py
│   │   │   └── telemetry.py
│   │   ├── services/
│   │   │   ├── blob_service.py
│   │   │   ├── cache_service.py    # In-memory index.json caching
│   │   │   └── telemetry_service.py
│   │   └── models/
│   │       └── schemas.py
│   ├── requirements.txt
│   └── pytest.ini
├── uploader/
│   ├── memoir_uploader/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── uploader.py
│   │   ├── deleter.py
│   │   ├── thumbnail.py
│   │   ├── converter.py      # HEIC to JPEG conversion
│   │   └── exif.py
│   ├── pyproject.toml
│   └── README.md
├── README.md
└── .gitignore
```

---

## 11. Decisions Log

All major decisions have been finalized:

| Question | Decision | Notes |
|----------|----------|-------|
| Custom domain | Azure-provided URLs for v1 | Custom domain to be added later |
| Thumbnail size | 400px width | Good balance of quality vs size |
| HEIC support | Convert to JPEG on upload | Using pillow-heif library |
| Metadata caching | In-memory with 5-min TTL | ~1KB per 100 photos, safe for large galleries |
| Photo deletion | Yes, via CLI | `memoir-uploader delete <id>` |
| Backup strategy | Deferred to v2 | Consider LRS → GRS upgrade later |
| Dark mode | Yes | System preference + manual toggle |
| Photo captions | No | Keep it simple for v1 |

---

## 12. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Bicep infrastructure templates
- [ ] Basic backend API (years, photos endpoints)
- [ ] Basic frontend (year tabs, photo grid)
- [ ] Uploader CLI (upload command)
- [ ] GitHub Actions pipeline

### Phase 2: Polish
- [ ] Lightbox component
- [ ] Infinite scroll
- [ ] Telemetry integration
- [ ] EXIF metadata display
- [ ] Dark mode (system preference + toggle)

### Phase 3: Enhancements
- [ ] Front Door CDN integration
- [ ] Performance optimization
- [ ] Error handling & logging
- [ ] Smoke tests in pipeline

---

## Appendix A: Technology Choices Rationale

| Choice | Alternatives Considered | Rationale |
|--------|------------------------|-----------|
| FastAPI | Flask, Django | Async support, automatic OpenAPI docs, Pydantic validation |
| Vite | Create React App, Next.js | Faster builds, simpler for SPA |
| Tailwind | Bootstrap, CSS Modules | Utility-first works great for galleries, responsive helpers |
| Bicep | Terraform, ARM | Native Azure, simpler syntax than ARM |
| WebP thumbnails | JPEG | Better compression, universal browser support |

---

*This spec is a living document. Please review and provide feedback before implementation begins.*
