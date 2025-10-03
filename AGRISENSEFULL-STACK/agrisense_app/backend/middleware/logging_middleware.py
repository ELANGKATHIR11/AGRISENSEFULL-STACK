"""
Request Logging and Metrics Middleware
Handles request ID tracking, timing, and basic metrics
"""
import logging
import threading
import time
import uuid
from typing import Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# In-process metrics storage
_metrics_lock = threading.Lock()
_metrics: Dict[str, Any] = {
    "started_at": time.time(),
    "requests_total": 0,
    "errors_total": 0,
    "by_path": {},
    "by_status": {},
}


def get_metrics() -> Dict[str, Any]:
    """Get current metrics snapshot"""
    with _metrics_lock:
        return dict(_metrics)


def reset_metrics() -> None:
    """Reset metrics (useful for testing)"""
    global _metrics
    with _metrics_lock:
        _metrics = {
            "started_at": time.time(),
            "requests_total": 0,
            "errors_total": 0,
            "by_path": {},
            "by_status": {},
        }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging, timing, and metrics collection"""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        req_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        
        # Time the request
        start = time.perf_counter()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            logger.exception("Unhandled exception in request processing")
            status = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            
            # Update metrics
            with _metrics_lock:
                _metrics["requests_total"] += 1
                
                # Track by path
                path = request.url.path
                by_path: Dict[str, int] = _metrics.setdefault("by_path", {})
                by_path[path] = by_path.get(path, 0) + 1
                
                # Track by status code
                by_status: Dict[str, int] = _metrics.setdefault("by_status", {})
                status_key = f"{status // 100}xx"
                by_status[status_key] = by_status.get(status_key, 0) + 1
                
                # Track errors
                if status >= 500:
                    _metrics["errors_total"] += 1
            
            # Log request
            logger.info(
                "%s %s -> %s in %.1fms [req_id=%s]",
                request.method,
                request.url.path,
                status,
                duration_ms,
                req_id,
            )
        
        # Add headers to response
        response.headers["X-Request-ID"] = req_id
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.1f}"
        
        return response
