"""
Hardware-Optimized Performance Middleware
Optimized for Intel Core Ultra 9 275HX (32 threads) + RTX 5060 (8GB)

This middleware:
1. Monitors CPU/GPU utilization per request
2. Implements intelligent caching strategies
3. Tracks performance metrics
4. Provides load balancing hints
"""

import time
import logging
import psutil
import os
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# GPU monitoring (optional)
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logger.warning("GPUtil not available - GPU monitoring disabled")


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Monitors request processing time, CPU, memory, and GPU usage.
    Adds performance headers to responses and logs slow requests.
    """
    
    def __init__(
        self,
        app,
        slow_request_threshold: float = 1.0,
        enable_gpu_monitoring: bool = True,
        log_all_requests: bool = False
    ):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.enable_gpu_monitoring = enable_gpu_monitoring and GPU_AVAILABLE
        self.log_all_requests = log_all_requests
        
        # Process object for efficient CPU monitoring
        self.process = psutil.Process()
        
        # Request counter
        self.request_count = 0
        self.slow_request_count = 0
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}-{self.request_count}"
        self.request_count += 1
        
        # Get system stats before request
        try:
            cpu_percent_before = self.process.cpu_percent(interval=0.01)
            memory_before = self.process.memory_info()
        except Exception as e:
            logger.warning(f"Failed to get process stats: {e}")
            cpu_percent_before = 0.0
            memory_before = None
        
        # Get GPU stats (if available)
        gpu_load_before = 0.0
        gpu_memory_used = 0
        if self.enable_gpu_monitoring:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_load_before = gpus[0].load * 100
                    gpu_memory_used = gpus[0].memoryUsed
            except Exception as e:
                logger.debug(f"GPU monitoring failed: {e}")
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error with context
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {process_time:.3f}s - {str(e)}"
            )
            raise
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        try:
            cpu_percent_after = self.process.cpu_percent(interval=0.01)
            memory_after = self.process.memory_info()
            
            # Calculate deltas
            cpu_delta = max(0, cpu_percent_after - cpu_percent_before)
            memory_delta_mb = 0
            if memory_before and memory_after:
                memory_delta_mb = (memory_after.rss - memory_before.rss) / 1024 / 1024
        except Exception as e:
            logger.warning(f"Failed to calculate metrics: {e}")
            cpu_delta = 0.0
            memory_delta_mb = 0.0
        
        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-CPU-Usage"] = f"{cpu_delta:.1f}"
        response.headers["X-Memory-Delta-MB"] = f"{memory_delta_mb:.2f}"
        
        if self.enable_gpu_monitoring and gpu_load_before > 0:
            response.headers["X-GPU-Usage"] = f"{gpu_load_before:.1f}"
            response.headers["X-GPU-Memory-MB"] = f"{gpu_memory_used}"
        
        # Log slow requests
        is_slow = process_time > self.slow_request_threshold
        if is_slow or self.log_all_requests:
            self.slow_request_count += is_slow
            log_func = logger.warning if is_slow else logger.info
            
            log_func(
                f"{'⚠️ SLOW' if is_slow else 'ℹ️'} Request: "
                f"{request.method} {request.url.path} | "
                f"Time: {process_time:.3f}s | "
                f"CPU: {cpu_delta:.1f}% | "
                f"Memory: {memory_delta_mb:+.2f}MB | "
                f"Status: {response.status_code}"
            )
        
        return response


class IntelligentCachingMiddleware(BaseHTTPMiddleware):
    """
    Caches GET requests based on URL and query parameters.
    Optimized for high-frequency sensor data requests.
    """
    
    def __init__(
        self,
        app,
        cache_ttl: int = 300,  # 5 minutes default
        max_cache_size: int = 1000,
        cache_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        
        # Paths to cache (None = cache all GET requests)
        self.cache_paths = cache_paths or [
            "/api/sensors",
            "/api/analytics",
            "/api/recommendations",
            "/api/weather"
        ]
        
        # Simple in-memory cache
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def _should_cache(self, request: Request) -> bool:
        """Determine if request should be cached"""
        if request.method != "GET":
            return False
        
        # Check if path matches cache patterns
        path = request.url.path
        if not any(path.startswith(pattern) for pattern in self.cache_paths):
            return False
        
        return True
    
    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        return f"{request.url.path}?{request.url.query}"
    
    def _is_cache_valid(self, cached_time: datetime) -> bool:
        """Check if cached entry is still valid"""
        return (datetime.now() - cached_time).total_seconds() < self.cache_ttl
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""
        
        # Check if should cache
        if not self._should_cache(request):
            return await call_next(request)
        
        cache_key = self._get_cache_key(request)
        
        # Check cache
        if cache_key in self._cache:
            cached_response, cached_time = self._cache[cache_key]
            
            if self._is_cache_valid(cached_time):
                # Cache hit!
                self._cache_hits += 1
                
                # Create response from cached data
                response = JSONResponse(
                    content=cached_response,
                    headers={
                        "X-Cache": "HIT",
                        "X-Cache-Age": f"{(datetime.now() - cached_time).total_seconds():.1f}"
                    }
                )
                return response
            else:
                # Cache expired
                del self._cache[cache_key]
        
        # Cache miss - process request
        self._cache_misses += 1
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200 and hasattr(response, 'body'):
            # Limit cache size
            if len(self._cache) >= self.max_cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            # Store in cache
            try:
                # Note: This is simplified. In production, use proper async caching
                # library like aiocache or Redis
                import json
                response_body = response.body.decode() if isinstance(response.body, bytes) else response.body
                self._cache[cache_key] = (json.loads(response_body), datetime.now())
            except Exception as e:
                logger.debug(f"Failed to cache response: {e}")
        
        response.headers["X-Cache"] = "MISS"
        response.headers["X-Cache-Hits"] = str(self._cache_hits)
        response.headers["X-Cache-Misses"] = str(self._cache_misses)
        
        return response


class LoadBalancingHintsMiddleware(BaseHTTPMiddleware):
    """
    Provides load balancing hints based on current system load.
    Useful for horizontal scaling decisions.
    """
    
    def __init__(
        self,
        app,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0
    ):
        super().__init__(app)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add load balancing hints to response"""
        
        # Get current system load
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Process request
        response = await call_next(request)
        
        # Add load hints
        response.headers["X-System-CPU"] = f"{cpu_percent:.1f}"
        response.headers["X-System-Memory"] = f"{memory.percent:.1f}"
        
        # Set overload flag if thresholds exceeded
        if cpu_percent > self.cpu_threshold or memory.percent > self.memory_threshold:
            response.headers["X-System-Overload"] = "true"
            response.headers["Retry-After"] = "5"  # Suggest retry after 5s
        
        return response


# ============================================================================
# Performance Utilities
# ============================================================================

@lru_cache(maxsize=1)
def get_hardware_info():
    """Get hardware information (cached)"""
    info = {
        "cpu_count": os.cpu_count() or 1,
        "cpu_count_physical": psutil.cpu_count(logical=False) or 1,
        "total_memory_gb": psutil.virtual_memory().total / (1024 ** 3),
    }
    
    if GPU_AVAILABLE:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                info["gpu_name"] = gpus[0].name
                info["gpu_memory_gb"] = gpus[0].memoryTotal / 1024
        except Exception:
            pass
    
    return info


def get_system_metrics():
    """Get current system metrics"""
    metrics = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "cpu_per_core": psutil.cpu_percent(interval=0.1, percpu=True),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used_gb": psutil.virtual_memory().used / (1024 ** 3),
        "memory_available_gb": psutil.virtual_memory().available / (1024 ** 3),
        "disk_usage_percent": psutil.disk_usage('/').percent,
    }
    
    if GPU_AVAILABLE:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                metrics["gpu_load_percent"] = gpu.load * 100
                metrics["gpu_memory_percent"] = gpu.memoryUtil * 100
                metrics["gpu_memory_used_mb"] = gpu.memoryUsed
                metrics["gpu_temperature_c"] = gpu.temperature
        except Exception as e:
            logger.debug(f"GPU metrics unavailable: {e}")
    
    return metrics


async def warmup_models():
    """
    Warmup ML models by running dummy predictions.
    This loads models into memory and optimizes CUDA kernels.
    """
    logger.info("🔥 Warming up ML models...")
    
    # Import models (adjust based on your structure)
    try:
        # Example: Warm up disease detection model
        from agrisense_app.backend.core.engine import RecoEngine
        
        engine = RecoEngine()
        
        # Run dummy predictions
        dummy_data = {
            "temperature": 25.0,
            "humidity": 60.0,
            "soil_moisture": 40.0,
            "ph": 6.5,
            "N": 30.0,
            "P": 20.0,
            "K": 25.0
        }
        
        # This will load models into memory
        _ = engine.get_recommendations(dummy_data)
        
        logger.info("✅ Model warmup complete")
    except Exception as e:
        logger.warning(f"Model warmup failed (models will load on first request): {e}")


# ============================================================================
# Example FastAPI Integration
# ============================================================================

"""
To use these middlewares in your FastAPI app:

from agrisense_app.backend.middleware.performance import (
    PerformanceMonitoringMiddleware,
    IntelligentCachingMiddleware,
    LoadBalancingHintsMiddleware,
    warmup_models
)

app = FastAPI()

# Add middleware (order matters - last added is first executed)
app.add_middleware(LoadBalancingHintsMiddleware)
app.add_middleware(IntelligentCachingMiddleware, cache_ttl=300, max_cache_size=1000)
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=1.0)

@app.on_event("startup")
async def startup():
    await warmup_models()

@app.get("/api/health")
async def health():
    from agrisense_app.backend.middleware.performance import get_system_metrics
    return {
        "status": "healthy",
        "metrics": get_system_metrics()
    }
"""
