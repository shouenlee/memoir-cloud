"""
Configuration settings for the application.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure Storage
    azure_storage_connection_string: str = ""
    azure_storage_account_name: str = ""
    
    # Application Insights
    applicationinsights_connection_string: str = ""
    
    # Cache settings
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Front Door hostname (for generating photo URLs)
    frontdoor_hostname: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
