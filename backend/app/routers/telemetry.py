"""
Telemetry API endpoint.
"""

from fastapi import APIRouter, Request

from app.models.schemas import TelemetryEvent
from app.services.telemetry_service import telemetry_service

router = APIRouter()


@router.post("/telemetry")
async def record_telemetry(event: TelemetryEvent, request: Request):
    """
    Record a telemetry event from the frontend.
    Extracts IP address and geolocation from request headers.
    """
    # Get client IP from X-Forwarded-For (set by Front Door) or direct connection
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Get country from Azure Front Door header if available
    country = request.headers.get("X-Azure-ClientIPCountry", "unknown")
    
    # Get user agent
    user_agent = request.headers.get("User-Agent", "unknown")
    
    await telemetry_service.track_event(
        event=event,
        client_ip=client_ip,
        country=country,
        user_agent=user_agent
    )
    
    return {"status": "recorded"}
