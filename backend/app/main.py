"""
Memoir Cloud - FastAPI Application
"""


from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import photos, telemetry, health
from app.services.cache_service import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Memoir Cloud API...")
    yield
    # Shutdown
    cache_service.clear()
    print("Shutting down Memoir Cloud API...")


app = FastAPI(
    title="Memoir Cloud API",
    description="Photo gallery API for Memoir Cloud",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production via Front Door
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(photos.router, prefix="/api", tags=["photos"])
app.include_router(telemetry.router, prefix="/api", tags=["telemetry"])

# Serve static files (React frontend) if the directory exists
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
