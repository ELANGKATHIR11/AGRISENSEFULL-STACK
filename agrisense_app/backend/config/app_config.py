"""
AgriSense Backend Configuration Module
Centralizes all configuration, environment variables, and feature flags
"""
import os
import secrets
from typing import Any, Dict

# ===== ML Configuration =====
DISABLE_ML = os.getenv("AGRISENSE_DISABLE_ML", "0").lower() in ("1", "true", "yes")

# ===== Database Configuration =====
DB_TYPE = os.getenv("AGRISENSE_DB", "sqlite").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sensors.db")
AGRISENSE_DB_PATH = os.getenv("AGRISENSE_DB_PATH")
AGRISENSE_DATA_DIR = os.getenv("AGRISENSE_DATA_DIR")

# ===== Security Configuration =====
AGRISENSE_ADMIN_TOKEN = os.getenv("AGRISENSE_ADMIN_TOKEN")
AGRISENSE_JWT_SECRET = os.getenv("AGRISENSE_JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# ===== API Configuration =====
API_VERSION = "0.3.0"
API_TITLE = "AgriSense API"
API_DESCRIPTION = "Smart irrigation and crop recommendation system with enhanced real-time features"

# ===== CORS Configuration =====
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS_LIST = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()] or ["*"]

# ===== MQTT Configuration =====
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_PREFIX = os.getenv("MQTT_PREFIX", "agrisense").strip()

# ===== Weather Configuration =====
AGRISENSE_LAT = float(os.getenv("AGRISENSE_LAT", "27.3"))
AGRISENSE_LON = float(os.getenv("AGRISENSE_LON", "88.6"))
AGRISENSE_WEATHER_CACHE = os.getenv("AGRISENSE_WEATHER_CACHE", "weather_cache.csv")

# ===== Chatbot Configuration =====
CHATBOT_DEFAULT_TOPK = 5
CHATBOT_MIN_COSINE = float(os.getenv("CHATBOT_MIN_COSINE", "0.3"))
CHATBOT_ALPHA = float(os.getenv("CHATBOT_ALPHA", "0.5"))
CHATBOT_CACHE_MAX = 100

# ===== Rate Limiting Configuration =====
RATE_LIMITING_ENABLED = not os.getenv("AGRISENSE_DISABLE_RATE_LIMITING", "0").lower() in ("1", "true", "yes")
DEFAULT_RATE_LIMIT = int(os.getenv("DEFAULT_RATE_LIMIT", "100"))
DEFAULT_RATE_WINDOW = int(os.getenv("DEFAULT_RATE_WINDOW", "60"))

# ===== Redis Configuration =====
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ===== Sentry Configuration =====
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

# ===== Feature Flags =====
ENHANCED_BACKEND_ENABLED = True  # Will be set based on import availability
VLM_ENABLED = True  # Will be set based on import availability
WEBSOCKET_ENABLED = True
CELERY_ENABLED = True

# ===== Frontend Configuration =====
FRONTEND_DIST_PATH = os.getenv("FRONTEND_DIST_PATH", "../frontend/farm-fortune-frontend-main/dist")

# ===== Logging Configuration =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_config_dict() -> Dict[str, Any]:
    """Return all configuration as a dictionary for introspection"""
    return {
        "api_version": API_VERSION,
        "ml_enabled": not DISABLE_ML,
        "db_type": DB_TYPE,
        "cors_origins": ALLOWED_ORIGINS_LIST,
        "rate_limiting": RATE_LIMITING_ENABLED,
        "sentry_enabled": bool(SENTRY_DSN),
        "environment": SENTRY_ENVIRONMENT,
    }
