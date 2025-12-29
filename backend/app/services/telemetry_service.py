"""
Telemetry service for Application Insights integration.
"""

import logging
from typing import Optional

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

from app.config import get_settings
from app.models.schemas import TelemetryEvent

logger = logging.getLogger(__name__)


class TelemetryService:
    """Service for tracking events in Application Insights."""

    def __init__(self):
        self._initialized = False
        self._tracer: Optional[trace.Tracer] = None

    def _ensure_initialized(self):
        """Initialize Azure Monitor if not already done."""
        if self._initialized:
            return

        settings = get_settings()
        if settings.applicationinsights_connection_string:
            try:
                configure_azure_monitor(
                    connection_string=settings.applicationinsights_connection_string
                )
                self._tracer = trace.get_tracer(__name__)
                self._initialized = True
                logger.info("Application Insights initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Application Insights: {e}")
        else:
            logger.warning("Application Insights connection string not configured")

    async def track_event(
        self,
        event: TelemetryEvent,
        client_ip: str,
        country: str,
        user_agent: str,
    ) -> None:
        """
        Track a telemetry event.
        
        Args:
            event: The telemetry event from the frontend
            client_ip: Client IP address
            country: Country from geolocation
            user_agent: Browser user agent
        """
        self._ensure_initialized()

        if not self._tracer:
            # Log locally if App Insights not available
            logger.info(
                f"Telemetry: {event.event} | "
                f"photoId={event.photoId} | "
                f"ip={client_ip} | "
                f"country={country}"
            )
            return

        # Create a span for the event
        with self._tracer.start_as_current_span(f"telemetry.{event.event}") as span:
            span.set_attribute("event.type", event.event)
            span.set_attribute("session.id", event.sessionId)
            span.set_attribute("client.ip", client_ip)
            span.set_attribute("client.country", country)
            span.set_attribute("client.user_agent", user_agent)
            
            if event.photoId:
                span.set_attribute("photo.id", event.photoId)
            
            if event.timestamp:
                span.set_attribute("event.timestamp", event.timestamp)


# Singleton instance
telemetry_service = TelemetryService()
