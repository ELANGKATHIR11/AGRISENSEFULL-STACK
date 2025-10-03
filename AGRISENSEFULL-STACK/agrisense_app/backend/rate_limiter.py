"""
Rate Limiting Middleware for AgriSense API
Comprehensive rate limiting with Redis backend and multiple strategies
"""

import time
from typing import Dict, Optional, Callable, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from functools import wraps

try:
    import redis.asyncio as redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger(__name__)

# Rate limit configurations
RATE_LIMIT_CONFIGS = {
    "default": {"requests": 100, "window": 3600},  # 100 requests per hour
    "login": {"requests": 5, "window": 300},  # 5 login attempts per 5 minutes
    "heavy": {"requests": 10, "window": 600},  # 10 heavy operations per 10 minutes
    "realtime": {"requests": 1000, "window": 3600},  # 1000 real-time requests per hour
    "upload": {"requests": 20, "window": 3600},  # 20 uploads per hour
    "admin": {"requests": 500, "window": 3600},  # 500 admin operations per hour
}

# Endpoint rate limit mappings
ENDPOINT_LIMITS = {
    "/auth/jwt/login": "login",
    "/auth/register": "login",
    "/auth/forgot-password": "login",
    "/recommend": "heavy",
    "/ingest": "realtime",
    "/edge/ingest": "realtime",
    "/upload": "upload",
    "/admin": "admin",
    "/ws": "realtime",
}


class RateLimitManager:
    """Redis-based rate limiting manager"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None  # type: ignore
        self.fallback_cache: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            if REDIS_AVAILABLE and redis:
                self.redis_client = redis.from_url(  # type: ignore
                    self.redis_url, encoding="utf-8", decode_responses=True, health_check_interval=30
                )
                # Test connection
                await self.redis_client.ping()  # type: ignore
                logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using fallback cache: {e}")
            self.redis_client = None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    async def is_rate_limited(self, key: str, limit: int, window: int, cost: int = 1) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited
        Returns (is_limited, rate_info)
        """
        if self.redis_client:
            return await self._redis_rate_limit(key, limit, window, cost)
        else:
            return await self._fallback_rate_limit(key, limit, window, cost)

    async def _redis_rate_limit(self, key: str, limit: int, window: int, cost: int = 1) -> tuple[bool, Dict[str, Any]]:
        """Redis-based sliding window rate limiting"""
        now = time.time()
        window_start = now - window

        pipe = self.redis_client.pipeline()  # type: ignore

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)  # type: ignore

        # Count current requests
        pipe.zcard(key)  # type: ignore

        # Add current request timestamp(s)
        for i in range(cost):
            pipe.zadd(key, {f"{now}_{i}": now})  # type: ignore

        # Set expiration
        pipe.expire(key, window + 1)  # type: ignore

        # Execute pipeline
        results = await pipe.execute()  # type: ignore
        current_count = results[1] + cost

        # Check if limit exceeded
        is_limited = current_count > limit

        if is_limited:
            # Remove the added requests since we're rate limited
            for i in range(cost):
                await self.redis_client.zrem(key, f"{now}_{i}")  # type: ignore

        # Calculate reset time
        oldest_requests = await self.redis_client.zrange(key, 0, 0, withscores=True)  # type: ignore
        reset_time = now + window
        if oldest_requests:
            oldest_time = oldest_requests[0][1]
            reset_time = oldest_time + window

        rate_info = {
            "limit": limit,
            "remaining": max(0, limit - current_count + (cost if is_limited else 0)),
            "reset": int(reset_time),
            "window": window,
            "current": current_count - (cost if is_limited else 0),
        }

        return is_limited, rate_info

    async def _fallback_rate_limit(
        self, key: str, limit: int, window: int, cost: int = 1
    ) -> tuple[bool, Dict[str, Any]]:
        """Fallback in-memory rate limiting"""
        now = time.time()

        if key not in self.fallback_cache:
            self.fallback_cache[key] = {"requests": [], "window": window}

        cache_entry = self.fallback_cache[key]

        # Remove expired requests
        window_start = now - window
        cache_entry["requests"] = [req_time for req_time in cache_entry["requests"] if req_time > window_start]

        current_count = len(cache_entry["requests"])
        is_limited = current_count + cost > limit

        if not is_limited:
            # Add current request timestamp(s)
            for _ in range(cost):
                cache_entry["requests"].append(now)

        # Calculate reset time
        reset_time = now + window
        if cache_entry["requests"]:
            oldest_time = min(cache_entry["requests"])
            reset_time = oldest_time + window

        rate_info = {
            "limit": limit,
            "remaining": max(0, limit - current_count - (0 if is_limited else cost)),
            "reset": int(reset_time),
            "window": window,
            "current": current_count,
        }

        return is_limited, rate_info

    async def get_rate_info(self, key: str, limit: int, window: int) -> Dict[str, Any]:
        """Get current rate limit info without incrementing"""
        if self.redis_client:
            now = time.time()
            window_start = now - window

            # Clean expired entries and count
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis_client.zcard(key)

            # Get oldest request for reset calculation
            oldest_requests = await self.redis_client.zrange(key, 0, 0, withscores=True)
            reset_time = now + window
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                reset_time = oldest_time + window

            return {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset": int(reset_time),
                "window": window,
                "current": current_count,
            }
        else:
            # Fallback implementation
            if key not in self.fallback_cache:
                return {
                    "limit": limit,
                    "remaining": limit,
                    "reset": int(time.time() + window),
                    "window": window,
                    "current": 0,
                }

            now = time.time()
            cache_entry = self.fallback_cache[key]
            window_start = now - window

            # Count non-expired requests
            current_count = sum(1 for req_time in cache_entry["requests"] if req_time > window_start)

            return {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset": int(now + window),
                "window": window,
                "current": current_count,
            }


# Global rate limit manager
rate_limit_manager = RateLimitManager()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)

        # Determine rate limit configuration
        limit_config = self._get_limit_config(request.url.path)

        # Generate rate limit key
        rate_key = await self._generate_rate_key(request)

        try:
            # Check rate limit
            is_limited, rate_info = await rate_limit_manager.is_rate_limited(
                rate_key, limit_config["requests"], limit_config["window"]
            )

            if is_limited:
                return self._create_rate_limit_response(rate_info)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            self._add_rate_limit_headers(response, rate_info)

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return await call_next(request)

    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico", "/static/"]

        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for path"""
        # Check for specific endpoint limits
        for endpoint, limit_type in ENDPOINT_LIMITS.items():
            if path.startswith(endpoint):
                return RATE_LIMIT_CONFIGS[limit_type]

        # Check for admin paths
        if path.startswith("/admin"):
            return RATE_LIMIT_CONFIGS["admin"]

        # Default limit
        return RATE_LIMIT_CONFIGS["default"]

    async def _generate_rate_key(self, request: Request) -> str:
        """Generate rate limiting key for request"""
        # Try to get user ID from authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Import here to avoid circular imports
                from .auth_enhanced import verify_token
                from fastapi.security import HTTPAuthorizationCredentials

                credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth_header.split(" ")[1])

                token_data = await verify_token(credentials)
                if token_data and token_data.user_id:
                    return f"user:{token_data.user_id}:{request.url.path}"
            except BaseException:
                pass  # Fall back to IP-based limiting

        # Fall back to IP-based rate limiting
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}:{request.url.path}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _create_rate_limit_response(self, rate_info: Dict[str, Any]) -> JSONResponse:
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_info['limit']} per {rate_info['window']} seconds",
                "retry_after": rate_info["reset"] - int(time.time()),
                "limit": rate_info["limit"],
                "remaining": rate_info["remaining"],
                "reset": rate_info["reset"],
            },
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["reset"] - int(time.time())),
            },
        )

    def _add_rate_limit_headers(self, response: Response, rate_info: Dict[str, Any]):
        """Add rate limit headers to response"""
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])


# Decorator for specific endpoint rate limiting


def rate_limit(requests: int, window: int, cost: int = 1):
    """Decorator for custom rate limiting on specific endpoints"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request found, proceed without rate limiting
                return await func(*args, **kwargs)

            # Generate rate key
            middleware = RateLimitMiddleware(None)
            rate_key = await middleware._generate_rate_key(request)

            # Check rate limit
            is_limited, rate_info = await rate_limit_manager.is_rate_limited(rate_key, requests, window, cost)

            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Limit: {requests} per {window} seconds",
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset"]),
                        "Retry-After": str(rate_info["reset"] - int(time.time())),
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Rate limiting utilities


async def check_rate_limit(key: str, limit: int, window: int, cost: int = 1) -> Dict[str, Any]:
    """Check rate limit status"""
    is_limited, rate_info = await rate_limit_manager.is_rate_limited(key, limit, window, cost)

    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit} per {window} seconds",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]),
                "Retry-After": str(rate_info["reset"] - int(time.time())),
            },
        )

    return rate_info


async def get_rate_limit_status(key: str, limit: int, window: int) -> Dict[str, Any]:
    """Get current rate limit status without incrementing"""
    return await rate_limit_manager.get_rate_info(key, limit, window)


# Initialization function


async def initialize_rate_limiting(redis_url: str = "redis://localhost:6379"):
    """Initialize rate limiting system"""
    global rate_limit_manager
    rate_limit_manager = RateLimitManager(redis_url)
    await rate_limit_manager.initialize()


# Cleanup function


async def cleanup_rate_limiting():
    """Cleanup rate limiting resources"""
    if rate_limit_manager:
        await rate_limit_manager.close()


# Rate limit bypass for testing
_rate_limit_bypass = False


def set_rate_limit_bypass(bypass: bool):
    """Enable/disable rate limit bypass for testing"""
    global _rate_limit_bypass
    _rate_limit_bypass = bypass


def is_rate_limit_bypassed() -> bool:
    """Check if rate limiting is bypassed"""
    return _rate_limit_bypass
