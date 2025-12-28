"""
Celery Configuration and Setup
Background task processing with Redis broker
"""

import os
from typing import Dict, Any
import logging

try:
    from celery import Celery  # type: ignore
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery instance
if CELERY_AVAILABLE and Celery:
    celery_app = Celery(  # type: ignore
        "agrisense_tasks",
        broker=CELERY_BROKER_URL,
        backend=CELERY_RESULT_BACKEND,
        include=[
            "agrisense_app.backend.tasks.data_processing",
            "agrisense_app.backend.tasks.report_generation",
            "agrisense_app.backend.tasks.scheduled_tasks",
            "agrisense_app.backend.tasks.ml_tasks",
        "agrisense_app.backend.tasks.notification_tasks",
    ],
)

    # Celery configuration
    celery_app.conf.update(
        # Task routing
        task_routes={
            "agrisense_app.backend.tasks.data_processing.*": {"queue": "data_processing"},
            "agrisense_app.backend.tasks.report_generation.*": {"queue": "reports"},
            "agrisense_app.backend.tasks.scheduled_tasks.*": {"queue": "scheduled"},
            "agrisense_app.backend.tasks.ml_tasks.*": {"queue": "ml_inference"},
            "agrisense_app.backend.tasks.notification_tasks.*": {"queue": "notifications"},
        },
        # Task serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Task execution
        task_track_started=True,
        task_time_limit=300,  # 5 minutes default timeout
        task_soft_time_limit=240,  # 4 minutes soft timeout
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_persistent=True,
        # Worker settings
        worker_max_tasks_per_child=1000,
        worker_max_memory_per_child=200000,  # 200MB
        # Beat scheduler settings
        beat_schedule={
            "process-sensor-data": {
                "task": "agrisense_app.backend.tasks.data_processing.process_sensor_data_batch",
                "schedule": 300.0,  # Every 5 minutes
            },
            "generate-daily-report": {
                "task": "agrisense_app.backend.tasks.report_generation.generate_daily_report",
                "schedule": 86400.0,  # Daily at midnight
            },
            "cleanup-old-data": {
                "task": "agrisense_app.backend.tasks.scheduled_tasks.cleanup_old_sensor_data",
                "schedule": 3600.0,  # Hourly
            },
            "check-system-health": {
                "task": "agrisense_app.backend.tasks.scheduled_tasks.system_health_check",
                "schedule": 600.0,  # Every 10 minutes
            },
            "update-weather-cache": {
                "task": "agrisense_app.backend.tasks.scheduled_tasks.update_weather_cache",
                "schedule": 1800.0,  # Every 30 minutes
            },
            "retrain-ml-models": {
                "task": "agrisense_app.backend.tasks.ml_tasks.retrain_models",
                "schedule": 604800.0,  # Weekly
            },
        },
        beat_schedule_filename="celerybeat-schedule",
    )
else:
    # Fallback when Celery is not available
    celery_app = None
    logger.warning("Celery is not available. Background tasks will not work.")


# Task retry configuration
if CELERY_AVAILABLE and celery_app:
    @celery_app.task(bind=True)
    def debug_task(self):
        """Debug task to test Celery setup"""
        print(f"Request: {self.request!r}")
        return {"status": "success", "message": "Celery is working correctly"}


    # Health check task
    @celery_app.task
    def health_check():
        """Simple health check task"""
        return {"status": "healthy", "timestamp": str(os.popen("date").read().strip()), "worker_id": os.getpid()}


# Task status monitoring
class TaskResult:
    """Task result wrapper with status tracking"""

    def __init__(self, task_id: str, celery_app=None):  # type: ignore
        self.task_id = task_id
        self.celery_app = celery_app or globals().get('celery_app')  # type: ignore

    @property
    def status(self) -> str:  # type: ignore
        """Get task status"""
        if self.celery_app:
            result = self.celery_app.AsyncResult(self.task_id)  # type: ignore
            return result.status  # type: ignore
        return "UNAVAILABLE"

    @property
    def result(self):  # type: ignore
        """Get task result"""
        if self.celery_app:
            result = self.celery_app.AsyncResult(self.task_id)  # type: ignore
            return result.result  # type: ignore
        return None

    @property
    def info(self) -> Dict[str, Any]:  # type: ignore
        """Get task info"""
        if self.celery_app:
            result = self.celery_app.AsyncResult(self.task_id)  # type: ignore
            return {
                "task_id": self.task_id,
                "status": result.status,  # type: ignore
                "result": result.result,  # type: ignore
                "traceback": result.traceback,  # type: ignore
                "successful": result.successful(),  # type: ignore
                "failed": result.failed(),  # type: ignore
            }
        return {"task_id": self.task_id, "status": "UNAVAILABLE"}

    def revoke(self, terminate: bool = False):  # type: ignore
        """Revoke/cancel task"""
        if self.celery_app:
            self.celery_app.control.revoke(self.task_id, terminate=terminate)  # type: ignore


# Utility functions for task management
def get_active_tasks() -> Dict[str, Any]:  # type: ignore
    """Get list of active tasks"""
    if CELERY_AVAILABLE and celery_app:
        inspect = celery_app.control.inspect()  # type: ignore
        return {
        "active": inspect.active(),
        "scheduled": inspect.scheduled(),
        "reserved": inspect.reserved(),
    }
    return {"active": {}, "scheduled": {}, "reserved": {}}


def get_worker_stats() -> Dict[str, Any]:
    """Get worker statistics"""
    if CELERY_AVAILABLE and celery_app:
        inspect = celery_app.control.inspect()
        return {
            "stats": inspect.stats(),
            "registered_tasks": inspect.registered(),
            "ping": inspect.ping(),
        }
    return {"stats": {}, "registered_tasks": {}, "ping": {}}


def purge_queue(queue_name: str) -> int:
    """Purge all tasks from a queue"""
    if CELERY_AVAILABLE and celery_app:
        return celery_app.control.purge()
    return 0


# Error handling and monitoring
if CELERY_AVAILABLE and celery_app:
    @celery_app.task(bind=True)
    def task_failure_handler(self, task_id: str, error: str, traceback: str):
        """Handle task failures"""
        logger.error(f"Task {task_id} failed: {error}")
        logger.error(f"Traceback: {traceback}")

        # Here you could add notification logic, save to database, etc.
        return {
            "status": "failure_handled",
            "task_id": task_id,
            "error": error,
            "timestamp": str(os.popen("date").read().strip()),
        }


# Configuration validation
def validate_celery_config() -> Dict[str, Any]:
    """Validate Celery configuration"""
    if not CELERY_AVAILABLE or not celery_app:
        return {
            "broker_url": CELERY_BROKER_URL,
            "result_backend": CELERY_RESULT_BACKEND,
            "broker_healthy": False,
            "broker_error": "Celery not available",
            "queues": [],
            "workers_available": 0,
        }
    
    try:
        # Test broker connection
        broker_connection = celery_app.connection()
        broker_connection.ensure_connection()
        broker_healthy = True
        broker_connection.close()
        broker_error = None
    except Exception as e:
        broker_healthy = False
        broker_error = str(e)

    return {
        "broker_url": CELERY_BROKER_URL,
        "result_backend": CELERY_RESULT_BACKEND,
        "broker_healthy": broker_healthy,
        "broker_error": broker_error,
        "queues": list(celery_app.conf.task_routes.values()),
        "workers_available": len(celery_app.control.inspect().ping() or {}),
    }


if __name__ == "__main__":
    # Start Celery worker
    if CELERY_AVAILABLE and celery_app:
        celery_app.start()
    else:
        print("Celery is not available. Cannot start worker.")
