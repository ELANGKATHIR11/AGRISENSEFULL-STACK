"""
Prometheus metrics collection for AgriSense backend
Provides comprehensive monitoring and observability
"""

import time
import psutil
import asyncio
import logging

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CollectorRegistry  # type: ignore
    PROMETHEUS_AVAILABLE = True
    RegistryType = CollectorRegistry
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock Prometheus classes
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def info(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    class MockRegistry:
        def __init__(self, *args, **kwargs):
            pass
    Counter = Histogram = Gauge = Info = MockMetric
    CollectorRegistry = MockRegistry
    RegistryType = MockRegistry
    def generate_latest(*args, **kwargs):
        return b"# Mock metrics\n"

try:
    from fastapi import Request
    from fastapi.middleware.base import BaseHTTPMiddleware as _BaseHTTPMiddleware  # type: ignore
    FASTAPI_AVAILABLE = True
    RequestType = Request
    BaseHTTPMiddleware = _BaseHTTPMiddleware
except ImportError:
    FASTAPI_AVAILABLE = False
    RequestType = None
    
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app

logger = logging.getLogger(__name__)

# Create custom registry for cleaner metrics
agrisense_registry = CollectorRegistry()  # type: ignore

# Application Info
app_info = Info("agrisense_app_info", "AgriSense application information", registry=agrisense_registry)  # type: ignore

# HTTP Metrics
http_requests_total = Counter(
    "agrisense_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=agrisense_registry,  # type: ignore
)

http_request_duration_seconds = Histogram(
    "agrisense_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=agrisense_registry,  # type: ignore
)

http_request_size_bytes = Histogram(
    "agrisense_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=agrisense_registry,  # type: ignore
)

http_response_size_bytes = Histogram(
    "agrisense_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=agrisense_registry,  # type: ignore
)

# Business Logic Metrics
sensor_readings_total = Counter(
    "agrisense_sensor_readings_total",
    "Total sensor readings processed",
    ["sensor_type", "source"],
    registry=agrisense_registry,  # type: ignore
)

recommendations_generated_total = Counter(
    "agrisense_recommendations_generated_total",
    "Total recommendations generated",
    ["crop_type", "model_used"],
    registry=agrisense_registry,  # type: ignore
)

irrigation_events_total = Counter(
    "agrisense_irrigation_events_total",
    "Total irrigation events triggered",
    ["trigger_type"],
    registry=agrisense_registry,  # type: ignore
)

alerts_generated_total = Counter(
    "agrisense_alerts_generated_total",
    "Total alerts generated",
    ["alert_type", "severity"],
    registry=agrisense_registry,  # type: ignore
)

# ML Model Metrics
ml_inference_duration_seconds = Histogram(
    "agrisense_ml_inference_duration_seconds",
    "ML model inference duration in seconds",
    ["model_name", "model_version"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=agrisense_registry,  # type: ignore
)

ml_predictions_total = Counter(
    "agrisense_ml_predictions_total",
    "Total ML predictions made",
    ["model_name", "model_version", "status"],
    registry=agrisense_registry,  # type: ignore
)

# Database Metrics
db_queries_total = Counter(
    "agrisense_db_queries_total",
    "Total database queries",
    ["operation", "table", "status"],
    registry=agrisense_registry,  # type: ignore
)

db_query_duration_seconds = Histogram(
    "agrisense_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=agrisense_registry,  # type: ignore
)

db_connections_active = Gauge(
    "agrisense_db_connections_active", "Number of active database connections", registry=agrisense_registry  # type: ignore
)

# Cache Metrics
cache_operations_total = Counter(
    "agrisense_cache_operations_total",
    "Total cache operations",
    ["operation", "cache_type", "status"],
    registry=agrisense_registry,  # type: ignore
)

cache_hit_ratio = Gauge("agrisense_cache_hit_ratio", "Cache hit ratio", ["cache_type"], registry=agrisense_registry)  # type: ignore

# WebSocket Metrics
websocket_connections_active = Gauge(
    "agrisense_websocket_connections_active", "Number of active WebSocket connections", registry=agrisense_registry  # type: ignore
)

websocket_messages_total = Counter(
    "agrisense_websocket_messages_total",
    "Total WebSocket messages",
    ["direction", "message_type"],
    registry=agrisense_registry,  # type: ignore
)

# System Metrics
system_cpu_usage = Gauge(
    "agrisense_system_cpu_usage_percent", "System CPU usage percentage", registry=agrisense_registry  # type: ignore
)

system_memory_usage = Gauge(
    "agrisense_system_memory_usage_bytes", "System memory usage in bytes", registry=agrisense_registry  # type: ignore
)

system_memory_available = Gauge(
    "agrisense_system_memory_available_bytes", "System available memory in bytes", registry=agrisense_registry  # type: ignore
)

system_disk_usage = Gauge(
    "agrisense_system_disk_usage_bytes", "System disk usage in bytes", ["device"], registry=agrisense_registry  # type: ignore
)

# Application Metrics
app_uptime_seconds = Gauge("agrisense_app_uptime_seconds", "Application uptime in seconds", registry=agrisense_registry)  # type: ignore

app_version_info = Info("agrisense_app_version", "Application version information", registry=agrisense_registry)  # type: ignore

# Task Queue Metrics (for Celery integration)
task_queue_size = Gauge(
    "agrisense_task_queue_size", "Number of tasks in queue", ["queue_name"], registry=agrisense_registry  # type: ignore
)

tasks_processed_total = Counter(
    "agrisense_tasks_processed_total", "Total tasks processed", ["task_name", "status"], registry=agrisense_registry  # type: ignore
)

task_duration_seconds = Histogram(
    "agrisense_task_duration_seconds",
    "Task execution duration in seconds",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0],
    registry=agrisense_registry,  # type: ignore
)


class MetricsMiddleware:
    """Middleware to collect HTTP metrics"""
    
    def __init__(self, app):
        self.app = app

    async def dispatch(self, request, call_next):
        if not FASTAPI_AVAILABLE or not PROMETHEUS_AVAILABLE:
            return await call_next(request)
            
        start_time = time.time()
        method = request.method

        # Get endpoint pattern (remove path parameters)
        endpoint = str(request.url.path)

        # Get request size
        content_length = request.headers.get("content-length")
        if content_length:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(int(content_length))

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Record response time
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            # Record response size
            if hasattr(response, "headers") and "content-length" in response.headers:
                http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(
                    int(response.headers["content-length"])
                )

        except Exception as e:
            status_code = 500
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # Record total requests
            http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        return response


class MetricsCollector:
    """Collects and manages application metrics"""

    def __init__(self):
        self.start_time = time.time()
        self._setup_app_info()

    def _setup_app_info(self):
        """Setup application information metrics"""
        app_info.info({"name": "AgriSense", "version": "2.0.0", "environment": "production", "component": "backend"})

        app_version_info.info({"version": "2.0.0", "commit": "unknown", "build_date": "unknown"})

    def record_sensor_reading(self, sensor_type: str, source: str = "api"):
        """Record a sensor reading"""
        sensor_readings_total.labels(sensor_type=sensor_type, source=source).inc()

    def record_recommendation(self, crop_type: str, model_used: str = "rule_based"):
        """Record a recommendation generation"""
        recommendations_generated_total.labels(crop_type=crop_type, model_used=model_used).inc()

    def record_irrigation_event(self, trigger_type: str):
        """Record an irrigation event"""
        irrigation_events_total.labels(trigger_type=trigger_type).inc()

    def record_alert(self, alert_type: str, severity: str = "medium"):
        """Record an alert generation"""
        alerts_generated_total.labels(alert_type=alert_type, severity=severity).inc()

    def record_ml_inference(
        self, model_name: str, duration: float, model_version: str = "latest", status: str = "success"
    ):
        """Record ML model inference"""
        ml_inference_duration_seconds.labels(model_name=model_name, model_version=model_version).observe(duration)

        ml_predictions_total.labels(model_name=model_name, model_version=model_version, status=status).inc()

    def record_db_query(self, operation: str, table: str, duration: float, status: str = "success"):
        """Record database query"""
        db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)

        db_queries_total.labels(operation=operation, table=table, status=status).inc()

    def update_db_connections(self, count: int):
        """Update active database connections count"""
        db_connections_active.set(count)

    def record_cache_operation(self, operation: str, cache_type: str, status: str = "hit"):
        """Record cache operation"""
        cache_operations_total.labels(operation=operation, cache_type=cache_type, status=status).inc()

    def update_cache_hit_ratio(self, cache_type: str, ratio: float):
        """Update cache hit ratio"""
        cache_hit_ratio.labels(cache_type=cache_type).set(ratio)

    def update_websocket_connections(self, count: int):
        """Update active WebSocket connections count"""
        websocket_connections_active.set(count)

    def record_websocket_message(self, direction: str, message_type: str):
        """Record WebSocket message"""
        websocket_messages_total.labels(direction=direction, message_type=message_type).inc()

    def record_task(self, task_name: str, duration: float, status: str = "success"):
        """Record background task execution"""
        task_duration_seconds.labels(task_name=task_name).observe(duration)
        tasks_processed_total.labels(task_name=task_name, status=status).inc()

    def update_task_queue_size(self, queue_name: str, size: int):
        """Update task queue size"""
        task_queue_size.labels(queue_name=queue_name).set(size)

    async def collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                system_cpu_usage.set(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.used)
                system_memory_available.set(memory.available)

                # Disk usage
                disk = psutil.disk_usage("/")
                system_disk_usage.labels(device="/").set(disk.used)

                # App uptime
                uptime = time.time() - self.start_time
                app_uptime_seconds.set(uptime)

                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(agrisense_registry).decode("utf-8")


# Global metrics collector instance
metrics = MetricsCollector()

# Health check metrics
health_check_status = Gauge(
    "agrisense_health_check_status",
    "Health check status (1 = healthy, 0 = unhealthy)",
    ["component"],
    registry=agrisense_registry,  # type: ignore
)


def record_health_check(component: str, healthy: bool):
    """Record health check status"""
    health_check_status.labels(component=component).set(1 if healthy else 0)


# Context managers for timing
class time_metric:
    """Context manager for timing operations"""

    def __init__(self, metric, **labels):
        self.metric = metric
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metric.labels(**self.labels).observe(duration)


# Decorator for automatic metric collection
def track_time(metric, **labels):
    """Decorator to automatically track function execution time"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with time_metric(metric, **labels):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            with time_metric(metric, **labels):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
