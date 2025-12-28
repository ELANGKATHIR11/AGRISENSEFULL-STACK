"""
Centralized Error Handling
Provides consistent error responses and error tracking
"""
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Optional Sentry integration
_sentry_available = False
try:
    import sentry_sdk
    _sentry_available = True
except ImportError:
    sentry_sdk = None


def init_sentry(dsn: Optional[str], environment: str, traces_sample_rate: float) -> None:
    """Initialize Sentry error tracking if DSN provided"""
    if not dsn or not _sentry_available:
        logger.info("Sentry error tracking not configured")
        return
    
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            integrations=[],  # Add specific integrations as needed
        )
        logger.info(f"Sentry initialized for environment: {environment}")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "path": request.url.path,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with consistent format and logging"""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    
    # Report to Sentry if available
    if _sentry_available and sentry_sdk:
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "error": "Internal Server Error",
            "path": request.url.path,
            "message": "An unexpected error occurred. Please contact support if the problem persists.",
        },
    )


def create_error_response(
    status_code: int,
    error: str,
    detail: Optional[str] = None,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized error response dictionary"""
    response: Dict[str, Any] = {
        "status": status_code,
        "error": error,
    }
    if detail:
        response["detail"] = detail
    if path:
        response["path"] = path
    return response
