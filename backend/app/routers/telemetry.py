"""
Telemetry API endpoint.
"""

from fastapi import APIRouter, Request

from app.models.schemas import TelemetryEvent
from app.services.telemetry_service import telemetry_service
from app.services.geoip_service import lookup_ip

router = APIRouter()


@router.post("/telemetry")
async def record_telemetry(event: TelemetryEvent, request: Request):
    """
    Record a telemetry event from the frontend.
    Extracts IP address and performs GeoIP lookup for location.
    """
    # Get client IP from X-Forwarded-For (set by reverse proxy) or direct connection
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Perform GeoIP lookup for country, state, city
    geo = await lookup_ip(client_ip)
    
    # Get user agent
    user_agent = request.headers.get("User-Agent", "unknown")
    
    await telemetry_service.track_event(
        event=event,
        client_ip=client_ip,
        geo=geo,
        user_agent=user_agent
    )
    
    return {"status": "recorded"}
