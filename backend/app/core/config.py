"""Configuration management using environment variables."""

import json
import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration from environment variables
    
    SECURITY CRITICAL:
    - All secrets MUST be set via environment variables
    - No hardcoded defaults for: SECRET_KEY, passwords, API keys
    - Validate required secrets in __init__
    """
    
    APP_NAME: str = "MAYA SOC Enterprise"
    APP_VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # CRITICAL: SECRET_KEY MUST be set in environment, no default
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET_KEY", ""))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    )
    
    # IMPORTANT: Admin credentials MUST be strong and set in environment
    # Never use default credentials - must be set before first run
    INIT_ADMIN_USERNAME: str = os.getenv("INIT_ADMIN_USERNAME", "admin")
    INIT_ADMIN_PASSWORD: str = os.getenv("INIT_ADMIN_PASSWORD", "")
    
    # CRITICAL: Database password MUST be set in environment
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "soc_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maya_soc")
    
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_EVENTS: str = "security-events"
    KAFKA_TOPIC_INCIDENTS: str = "security-incidents"
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
    
    def validate_production_secrets(self) -> None:
        """
        Validate that critical secrets are set in production
        Raises ValueError if required secrets are missing
        """
        if self.ENV == "production":
            errors = []
            
            # SECRET_KEY is always required
            if not self.SECRET_KEY or self.SECRET_KEY == "":
                errors.append("SECRET_KEY must be set in environment (non-empty)")
            
            # Password requirements
            if not self.INIT_ADMIN_PASSWORD or len(self.INIT_ADMIN_PASSWORD) < 12:
                errors.append(
                    "INIT_ADMIN_PASSWORD must be set (min 12 chars, upper/lower/numbers/symbols)"
                )
            
            if not self.POSTGRES_PASSWORD or len(self.POSTGRES_PASSWORD) < 12:
                errors.append(
                    "POSTGRES_PASSWORD must be set (min 12 chars)"
                )
            
            if errors:
                raise ValueError(
                    "Production security validation failed:\n" + "\n".join(errors)
                )

    def get_cors_origins(self) -> List[str]:
        """Return CORS origins from either JSON array or comma-separated string."""
        raw_value = (self.CORS_ORIGINS or "").strip()
        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
