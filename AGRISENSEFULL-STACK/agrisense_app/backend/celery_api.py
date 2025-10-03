"""
Celery API Integration
FastAPI endpoints for managing background tasks
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional, cast
from pydantic import BaseModel
from datetime import datetime
import logging

from .celery_config import celery_app, TaskResult, get_active_tasks, get_worker_stats, validate_celery_config
from .tasks.data_processing import process_sensor_data_batch, process_individual_reading, aggregate_sensor_data
from .tasks.report_generation import generate_daily_report, generate_weekly_report, generate_custom_report
from .tasks.scheduled_tasks import system_health_check, update_weather_cache, backup_database
from .tasks.ml_tasks import retrain_models, batch_model_inference, model_performance_evaluation
from .tasks.notification_tasks import send_email_notification, send_alert_notification

from .auth_enhanced import AdminGuard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["background-tasks"])


# Pydantic models
class TaskSubmissionResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    progress: Optional[Dict[str, Any]] = None


class CustomReportRequest(BaseModel):
    start_date: str
    end_date: str
    metrics: List[str] = ["temperature", "humidity", "moisture"]
    chart_types: List[str] = ["line", "summary"]
    include_recommendations: bool = True


class AlertNotificationRequest(BaseModel):
    alert_type: str
    severity: str = "medium"
    message: str
    location: str = "Farm"
    action_required: bool = False
    recipients: List[str]


class EmailNotificationRequest(BaseModel):
    recipient: str
    subject: str
    content: str
    notification_type: str = "general"


# Data Processing Endpoints
@router.post("/data/process-batch", response_model=TaskSubmissionResponse)
async def submit_batch_processing(batch_size: int = 100, admin_guard: AdminGuard = Depends()):
    """Submit batch sensor data processing task"""
    try:
        task = process_sensor_data_batch.delay(batch_size=batch_size)
        logger.info(f"Batch processing task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message=f"Batch processing task submitted with batch size {batch_size}"
        )
    except Exception as e:
        logger.error(f"Failed to submit batch processing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/process-reading", response_model=TaskSubmissionResponse)
async def submit_reading_processing(reading_data: Dict[str, Any], admin_guard: AdminGuard = Depends()):
    """Submit individual sensor reading processing task"""
    try:
        task = process_individual_reading.delay(reading_data)
        logger.info(f"Individual reading processing task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message="Individual reading processing task submitted"
        )
    except Exception as e:
        logger.error(f"Failed to submit reading processing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/aggregate", response_model=TaskSubmissionResponse)
async def submit_data_aggregation(time_period: str = "1h", admin_guard: AdminGuard = Depends()):
    """Submit data aggregation task"""
    try:
        task = aggregate_sensor_data.delay(time_period=time_period)
        logger.info(f"Data aggregation task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message=f"Data aggregation task submitted for period {time_period}"
        )
    except Exception as e:
        logger.error(f"Failed to submit data aggregation task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Report Generation Endpoints
@router.post("/reports/daily", response_model=TaskSubmissionResponse)
async def submit_daily_report(date: Optional[str] = None, admin_guard: AdminGuard = Depends()):
    """Submit daily report generation task"""
    try:
        task = generate_daily_report.delay(date=date)
        logger.info(f"Daily report task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message=f"Daily report generation task submitted for {date or 'today'}"
        )
    except Exception as e:
        logger.error(f"Failed to submit daily report task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/weekly", response_model=TaskSubmissionResponse)
async def submit_weekly_report(week_start: Optional[str] = None, admin_guard: AdminGuard = Depends()):
    """Submit weekly report generation task"""
    try:
        task = generate_weekly_report.delay(week_start=week_start)
        logger.info(f"Weekly report task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Weekly report generation task submitted for week starting {week_start or 'this week'}",
        )
    except Exception as e:
        logger.error(f"Failed to submit weekly report task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/custom", response_model=TaskSubmissionResponse)
async def submit_custom_report(config: CustomReportRequest, admin_guard: AdminGuard = Depends()):
    """Submit custom report generation task"""
    try:
        task = generate_custom_report.delay(config.dict())
        logger.info(f"Custom report task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Custom report generation task submitted for {config.start_date} to {config.end_date}",
        )
    except Exception as e:
        logger.error(f"Failed to submit custom report task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ML Tasks Endpoints
@router.post("/ml/retrain", response_model=TaskSubmissionResponse)
async def submit_model_retraining(model_types: Optional[List[str]] = None, admin_guard: AdminGuard = Depends()):
    """Submit model retraining task"""
    try:
        task = retrain_models.delay(model_types=model_types)
        logger.info(f"Model retraining task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Model retraining task submitted for {model_types or 'all models'}",
        )
    except Exception as e:
        logger.error(f"Failed to submit model retraining task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/batch-inference", response_model=TaskSubmissionResponse)
async def submit_batch_inference(
    readings: List[Dict[str, Any]], model_type: str = "recommendation", admin_guard: AdminGuard = Depends()
):
    """Submit batch ML inference task"""
    try:
        task = batch_model_inference.delay(readings=readings, model_type=model_type)
        logger.info(f"Batch inference task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Batch inference task submitted for {len(readings)} readings using {model_type} model",
        )
    except Exception as e:
        logger.error(f"Failed to submit batch inference task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/evaluate", response_model=TaskSubmissionResponse)
async def submit_model_evaluation(model_type: str, evaluation_period: str = "7d", admin_guard: AdminGuard = Depends()):
    """Submit model performance evaluation task"""
    try:
        task = model_performance_evaluation.delay(model_type=model_type, evaluation_period=evaluation_period)
        logger.info(f"Model evaluation task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Model evaluation task submitted for {model_type} over {evaluation_period}",
        )
    except Exception as e:
        logger.error(f"Failed to submit model evaluation task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Notification Endpoints
@router.post("/notifications/email", response_model=TaskSubmissionResponse)
async def submit_email_notification(notification: EmailNotificationRequest, admin_guard: AdminGuard = Depends()):
    """Submit email notification task"""
    try:
        task = send_email_notification.delay(
            recipient=notification.recipient,
            subject=notification.subject,
            content=notification.content,
            notification_type=notification.notification_type,
        )
        logger.info(f"Email notification task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Email notification task submitted to {notification.recipient}",
        )
    except Exception as e:
        logger.error(f"Failed to submit email notification task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/alert", response_model=TaskSubmissionResponse)
async def submit_alert_notification(alert: AlertNotificationRequest, admin_guard: AdminGuard = Depends()):
    """Submit alert notification task"""
    try:
        alert_data = {
            "type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "location": alert.location,
            "action_required": alert.action_required,
            "timestamp": datetime.utcnow().isoformat(),
        }

        task = send_alert_notification.delay(alert_data=alert_data, recipients=alert.recipients)
        logger.info(f"Alert notification task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id,
            status="submitted",
            message=f"Alert notification task submitted to {len(alert.recipients)} recipients",
        )
    except Exception as e:
        logger.error(f"Failed to submit alert notification task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# System Tasks Endpoints
@router.post("/system/health-check", response_model=TaskSubmissionResponse)
async def submit_health_check(admin_guard: AdminGuard = Depends()):
    """Submit system health check task"""
    try:
        task = system_health_check.delay()
        logger.info(f"Health check task submitted: {task.id}")

        return TaskSubmissionResponse(task_id=task.id, status="submitted", message="System health check task submitted")
    except Exception as e:
        logger.error(f"Failed to submit health check task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/backup", response_model=TaskSubmissionResponse)
async def submit_database_backup(backup_type: str = "incremental", admin_guard: AdminGuard = Depends()):
    """Submit database backup task"""
    try:
        task = backup_database.delay(backup_type=backup_type)
        logger.info(f"Database backup task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message=f"Database backup task submitted ({backup_type})"
        )
    except Exception as e:
        logger.error(f"Failed to submit backup task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system/weather-update", response_model=TaskSubmissionResponse)
async def submit_weather_update(admin_guard: AdminGuard = Depends()):
    """Submit weather cache update task"""
    try:
        task = update_weather_cache.delay()
        logger.info(f"Weather update task submitted: {task.id}")

        return TaskSubmissionResponse(
            task_id=task.id, status="submitted", message="Weather cache update task submitted"
        )
    except Exception as e:
        logger.error(f"Failed to submit weather update task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Task Management Endpoints
@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    try:
        task_result = TaskResult(task_id)
        task_info = task_result.info

        # Get progress information if available
        if celery_app:
            celery_result = celery_app.AsyncResult(task_id)  # type: ignore
            progress = None
            if celery_result.state == "PROGRESS":
                progress = celery_result.info
        else:
            progress = None

        return TaskStatusResponse(
            task_id=task_id, status=task_info["status"], result=task_info["result"], progress=progress
        )
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str, terminate: bool = False, admin_guard: AdminGuard = Depends()):
    """Cancel a running task"""
    try:
        task_result = TaskResult(task_id)
        task_result.revoke(terminate=terminate)

        logger.info(f"Task {task_id} cancelled (terminate={terminate})")

        return {
            "task_id": task_id,
            "status": "cancelled",
            "terminated": terminate,
            "message": f"Task {task_id} has been cancelled",
        }
    except Exception as e:
        logger.error(f"Failed to cancel task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_tasks_list():
    """Get list of active tasks"""
    try:
        active_tasks = get_active_tasks()
        return {"status": "success", "active_tasks": active_tasks, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get active tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers")
async def get_worker_statistics():
    """Get Celery worker statistics"""
    try:
        worker_stats = get_worker_stats()
        return {"status": "success", "worker_stats": worker_stats, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to get worker stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_celery_health():
    """Get Celery system health status"""
    try:
        config_status = validate_celery_config()
        return {
            "status": "healthy" if config_status["broker_healthy"] else "unhealthy",
            "celery_config": config_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get Celery health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Scheduled task management
@router.get("/scheduled")
async def get_scheduled_tasks():
    """Get list of scheduled (beat) tasks"""
    try:
        if not celery_app:
            return {
                "scheduled_tasks": [],
                "message": "Celery not available"
            }
        
        beat_schedule = celery_app.conf.beat_schedule if celery_app else None
        
        if not beat_schedule or not hasattr(beat_schedule, 'items'):
            return {
                "scheduled_tasks": [],
                "message": "No scheduled tasks configured"
            }

        scheduled_tasks = []
        for task_name, task_config in beat_schedule.items():  # type: ignore
            scheduled_tasks.append(
                {
                    "name": task_name,
                    "task": task_config["task"],
                    "schedule": str(task_config["schedule"]),
                    "enabled": True,  # You could add logic to check if task is enabled
                }
            )

        return {
            "status": "success",
            "scheduled_tasks": scheduled_tasks,
            "total_scheduled": len(scheduled_tasks),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Bulk task operations
@router.post("/bulk/process-readings", response_model=TaskSubmissionResponse)
async def submit_bulk_reading_processing(readings: List[Dict[str, Any]], admin_guard: AdminGuard = Depends()):
    """Submit multiple reading processing tasks"""
    try:
        task_ids = []
        for reading in readings:
            task = process_individual_reading.delay(reading)
            task_ids.append(task.id)

        logger.info(f"Bulk reading processing submitted: {len(task_ids)} tasks")

        return TaskSubmissionResponse(
            task_id=",".join(task_ids),  # Return comma-separated task IDs
            status="submitted",
            message=f"Bulk reading processing submitted: {len(task_ids)} tasks",
        )
    except Exception as e:
        logger.error(f"Failed to submit bulk reading processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
