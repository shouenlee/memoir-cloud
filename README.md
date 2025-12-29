# Memoir Cloud

A personal photo gallery web application hosted on Azure.

## Status

🚧 **In Development** - Currently in spec/design phase

## Documentation

- [Technical Specification](docs/SPEC.md) - Architecture, API design, and implementation details

## Quick Links

| Component | Description |
|-----------|-------------|
| `frontend/` | React + TypeScript photo gallery UI |
| `backend/` | Python FastAPI server |
| `uploader/` | CLI tool for uploading photos |
| `infra/` | Bicep templates for Azure infrastructure |

## Architecture Overview

```
User → Azure Front Door (CDN) → Blob Storage (photos)
                             → App Service (API)
                             → Application Insights (telemetry)
```

## Getting Started

*Coming soon after spec finalization*
