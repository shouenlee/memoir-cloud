"""
GeoIP lookup service using ip-api.com.
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Cache for IP lookups to avoid repeated API calls
_geo_cache: dict[str, "GeoLocation"] = {}


@dataclass
class GeoLocation:
    """Geographic location data from IP lookup."""
    country: str = "unknown"
    country_code: str = "unknown"
    region: str = "unknown"  # State/province code
    region_name: str = "unknown"  # State/province full name
    city: str = "unknown"
    zip_code: str = "unknown"
    lat: float = 0.0
    lon: float = 0.0
    timezone: str = "unknown"
    isp: str = "unknown"


async def lookup_ip(ip_address: str) -> GeoLocation:
    """
    Look up geographic location for an IP address.
    Uses ip-api.com free tier (45 requests/minute for non-commercial use).
    
    Args:
        ip_address: The IP address to look up
        
    Returns:
        GeoLocation with country, state, city, etc.
    """
    # Return cached result if available
    if ip_address in _geo_cache:
        return _geo_cache[ip_address]
    
    # Skip lookup for local/private IPs
    if ip_address in ("unknown", "127.0.0.1", "localhost") or ip_address.startswith(("10.", "192.168.", "172.")):
        return GeoLocation()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # ip-api.com provides free geolocation API
            # Fields: country, countryCode, region, regionName, city, zip, lat, lon, timezone, isp
            response = await client.get(
                f"http://ip-api.com/json/{ip_address}",
                params={"fields": "status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    geo = GeoLocation(
                        country=data.get("country", "unknown"),
                        country_code=data.get("countryCode", "unknown"),
                        region=data.get("region", "unknown"),
                        region_name=data.get("regionName", "unknown"),
                        city=data.get("city", "unknown"),
                        zip_code=data.get("zip", "unknown"),
                        lat=data.get("lat", 0.0),
                        lon=data.get("lon", 0.0),
                        timezone=data.get("timezone", "unknown"),
                        isp=data.get("isp", "unknown"),
                    )
                    # Cache the result
                    _geo_cache[ip_address] = geo
                    return geo
                else:
                    logger.debug(f"GeoIP lookup failed for {ip_address}: {data.get('message')}")
            else:
                logger.debug(f"GeoIP API returned status {response.status_code}")
                
    except Exception as e:
        logger.debug(f"GeoIP lookup error for {ip_address}: {e}")
    
    # Return default on failure
    return GeoLocation()
