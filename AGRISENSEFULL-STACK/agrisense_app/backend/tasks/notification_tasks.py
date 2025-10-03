"""
Notification Tasks
Background tasks for sending alerts, notifications, and communications
"""
# type: ignore

import logging
import smtplib
import json
from datetime import datetime
from typing import Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

try:
    from celery import current_task  # type: ignore
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    current_task = None  # type: ignore

from ..celery_config import celery_app, CELERY_AVAILABLE

logger = logging.getLogger(__name__)


# Conditional task decorators
def task_decorator(func):
    """Decorator that conditionally applies Celery task decoration"""
    if CELERY_AVAILABLE and celery_app:
        return celery_app.task(bind=True)(func)
    return func


def safe_update_state(task_instance, **kwargs):
    """Safely update task state if Celery is available"""
    if CELERY_AVAILABLE and task_instance and hasattr(task_instance, 'update_state'):
        task_instance.update_state(**kwargs)


@task_decorator
def send_email_notification(
    self, recipient: str, subject: str, content: str, notification_type: str = "general"
) -> Dict[str, Any]:
    """
    Send email notification to specified recipient
    Handle various types of email notifications
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 20, "status": "Preparing email"})

        # Email configuration
        smtp_server = os.getenv("SMTP_SERVER", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        sender_email = os.getenv("SENDER_EMAIL", "noreply@agrisense.com")

        # Create email message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject

        # Add content based on type
        if notification_type == "alert":
            html_content = create_alert_email_template(content)
        elif notification_type == "report":
            html_content = create_report_email_template(content)
        else:
            html_content = create_general_email_template(content)

        msg.attach(MIMEText(html_content, "html"))

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Sending email"})

        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_username and smtp_password:
                    server.starttls()
                    server.login(smtp_username, smtp_password)

                server.send_message(msg)

            email_sent = True
            error_message = None
        except Exception as e:
            email_sent = False
            error_message = str(e)
            logger.error(f"Failed to send email: {error_message}")

        result = {
            "status": "completed" if email_sent else "failed",
            "recipient": recipient,
            "subject": subject,
            "notification_type": notification_type,
            "sent": email_sent,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if email_sent:
            logger.info(f"Email sent successfully to {recipient}")

        return result

    except Exception as exc:
        logger.error(f"Email notification failed: {str(exc)}")
        raise


@task_decorator
def send_batch_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send multiple notifications in batch
    Efficient processing of multiple notification requests
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Processing batch notifications"})

        total_notifications = len(notifications)
        results = []
        successful_sends = 0
        failed_sends = 0

        for i, notification in enumerate(notifications):
            progress = 10 + (i / total_notifications) * 80
            safe_update_state(current_task,   # type: ignore
                state="PROGRESS",
                meta={"progress": progress, "status": f"Sending notification {i+1}/{total_notifications}"},
            )

            try:
                # Determine notification type and send accordingly
                if notification["type"] == "email":
                    result = send_single_email(notification)
                elif notification["type"] == "sms":
                    result = send_single_sms(notification)
                elif notification["type"] == "push":
                    result = send_single_push_notification(notification)
                else:
                    result = {"status": "failed", "error": f"Unknown notification type: {notification['type']}"}

                results.append(result)

                if result.get("status") == "completed":
                    successful_sends += 1
                else:
                    failed_sends += 1

            except Exception as e:
                results.append({"status": "failed", "error": str(e), "notification": notification})
                failed_sends += 1

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 95, "status": "Finalizing batch"})

        batch_result = {
            "status": "completed",
            "total_notifications": total_notifications,
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "success_rate": successful_sends / total_notifications if total_notifications > 0 else 0,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Batch notifications completed: {successful_sends}/{total_notifications} successful")
        return batch_result

    except Exception as exc:
        logger.error(f"Batch notifications failed: {str(exc)}")
        raise


@task_decorator
def send_alert_notification(self, alert_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
    """
    Send alert notifications to multiple recipients
    Handle urgent system or farm alerts
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Preparing alert notification"})

        alert_type = alert_data.get("type", "general")
        severity = alert_data.get("severity", "medium")
        message = alert_data.get("message", "System alert")
        location = alert_data.get("location", "Unknown")
        timestamp = alert_data.get("timestamp", datetime.utcnow().isoformat())

        # Create alert subject and content
        subject = f"[{severity.upper()}] AgriSense Alert: {alert_type}"

        alert_content = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "location": location,
            "timestamp": timestamp,
            "action_required": alert_data.get("action_required", False),
        }

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 30, "status": "Sending alert notifications"})

        # Send notifications based on severity
        notification_results = []

        for recipient in recipients:
            try:
                # Always send email for alerts
                email_result = send_email_notification.delay(
                    recipient=recipient, subject=subject, content=json.dumps(alert_content), notification_type="alert"
                ).get()

                notification_results.append({"recipient": recipient, "type": "email", "result": email_result})

                # Send SMS for high severity alerts
                if severity == "high":
                    sms_result = send_sms_alert(recipient, alert_content)
                    notification_results.append({"recipient": recipient, "type": "sms", "result": sms_result})

            except Exception as e:
                notification_results.append(
                    {"recipient": recipient, "type": "email", "result": {"status": "failed", "error": str(e)}}
                )

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 80, "status": "Logging alert"})

        # Log alert to database/file
        log_alert_notification(alert_data, notification_results)

        result = {
            "status": "completed",
            "alert_type": alert_type,
            "severity": severity,
            "recipients_count": len(recipients),
            "notifications_sent": len(notification_results),
            "notification_results": notification_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Alert notification sent: {alert_type} to {len(recipients)} recipients")
        return result

    except Exception as exc:
        logger.error(f"Alert notification failed: {str(exc)}")
        raise


@task_decorator
def send_scheduled_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send scheduled report via email
    Automated delivery of daily/weekly/monthly reports
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Preparing scheduled report"})

        report_type = report_config.get("type", "daily")
        recipients = report_config.get("recipients", [])
        include_charts = report_config.get("include_charts", True)
        format_type = report_config.get("format", "html")

        if not recipients:
            return {"status": "failed", "error": "No recipients specified for report"}

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 30, "status": "Generating report content"})

        # Generate report content (this would integrate with report generation tasks)
        report_content = generate_report_content(report_type, include_charts, format_type)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Sending report emails"})

        # Send report to each recipient
        sent_results = []
        for recipient in recipients:
            try:
                subject = f"AgriSense {report_type.title()} Report - {datetime.utcnow().strftime('%Y-%m-%d')}"

                email_result = send_email_notification.delay(
                    recipient=recipient, subject=subject, content=report_content, notification_type="report"
                ).get()

                sent_results.append(
                    {
                        "recipient": recipient,
                        "status": email_result.get("status"),
                        "sent": email_result.get("sent", False),
                    }
                )

            except Exception as e:
                sent_results.append({"recipient": recipient, "status": "failed", "error": str(e)})

        successful_sends = sum(1 for result in sent_results if result.get("status") == "completed")

        result = {
            "status": "completed",
            "report_type": report_type,
            "total_recipients": len(recipients),
            "successful_sends": successful_sends,
            "failed_sends": len(recipients) - successful_sends,
            "sent_results": sent_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Scheduled report sent: {report_type} to {successful_sends}/{len(recipients)} recipients")
        return result

    except Exception as exc:
        logger.error(f"Scheduled report failed: {str(exc)}")
        raise


@task_decorator
def send_maintenance_reminder(self, maintenance_data: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
    """
    Send maintenance reminder notifications
    Automated reminders for system maintenance tasks
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 20, "status": "Preparing maintenance reminder"})

        task_name = maintenance_data.get("task_name", "System Maintenance")
        due_date = maintenance_data.get("due_date")
        priority = maintenance_data.get("priority", "medium")
        description = maintenance_data.get("description", "Scheduled maintenance task")

        subject = f"Maintenance Reminder: {task_name}"

        reminder_content = {
            "task_name": task_name,
            "due_date": due_date,
            "priority": priority,
            "description": description,
            "reminder_sent": datetime.utcnow().isoformat(),
        }

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Sending reminders"})

        # Send reminders to recipients
        reminder_results = []
        for recipient in recipients:
            try:
                email_result = send_email_notification.delay(
                    recipient=recipient,
                    subject=subject,
                    content=json.dumps(reminder_content),
                    notification_type="maintenance",
                ).get()

                reminder_results.append(
                    {
                        "recipient": recipient,
                        "status": email_result.get("status"),
                        "sent": email_result.get("sent", False),
                    }
                )

            except Exception as e:
                reminder_results.append({"recipient": recipient, "status": "failed", "error": str(e)})

        successful_reminders = sum(1 for result in reminder_results if result.get("status") == "completed")

        result = {
            "status": "completed",
            "task_name": task_name,
            "due_date": due_date,
            "priority": priority,
            "total_recipients": len(recipients),
            "successful_reminders": successful_reminders,
            "reminder_results": reminder_results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Maintenance reminder sent: {task_name} to {successful_reminders}/{len(recipients)} recipients")
        return result

    except Exception as exc:
        logger.error(f"Maintenance reminder failed: {str(exc)}")
        raise


# Helper functions


def send_single_email(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send a single email notification"""
    try:
        return send_email_notification.delay(
            recipient=notification["recipient"],
            subject=notification["subject"],
            content=notification["content"],
            notification_type=notification.get("notification_type", "general"),
        ).get()
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def send_single_sms(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send a single SMS notification"""
    # Placeholder implementation
    # In production, this would integrate with SMS service (Twilio, AWS SNS, etc.)
    return {
        "status": "completed",
        "recipient": notification["recipient"],
        "message": notification["content"][:160],  # SMS character limit
        "timestamp": datetime.utcnow().isoformat(),
    }


def send_single_push_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send a single push notification"""
    # Placeholder implementation
    # In production, this would integrate with push notification service (FCM, APNs, etc.)
    return {
        "status": "completed",
        "recipient": notification["recipient"],
        "title": notification.get("title", "AgriSense"),
        "body": notification["content"],
        "timestamp": datetime.utcnow().isoformat(),
    }


def send_sms_alert(recipient: str, alert_content: Dict[str, Any]) -> Dict[str, Any]:
    """Send SMS alert for high severity notifications"""
    # Placeholder implementation
    sms_message = f"ALERT: {alert_content['message']} - {alert_content['location']}"
    return {
        "status": "completed",
        "recipient": recipient,
        "message": sms_message[:160],
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_alert_email_template(content: str) -> str:
    """Create HTML email template for alerts"""
    alert_data = json.loads(content)

    severity_colors = {"low": "#28a745", "medium": "#ffc107", "high": "#dc3545"}

    color = severity_colors.get(alert_data.get("severity", "medium"), "#ffc107")

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">AgriSense Alert</h1>
            <h2 style="margin: 10px 0 0 0;">{alert_data.get('severity', 'MEDIUM').upper()} PRIORITY</h2>
        </div>
        <div style="padding: 20px; background-color: #f8f9fa;">
            <h3>Alert Details</h3>
            <p><strong>Type:</strong> {alert_data.get('type', 'General')}</p>
            <p><strong>Location:</strong> {alert_data.get('location', 'Unknown')}</p>
            <p><strong>Message:</strong> {alert_data.get('message', 'No message')}</p>
            <p><strong>Time:</strong> {alert_data.get('timestamp', 'Unknown')}</p>
            {f"<p><strong>Action Required:</strong> Yes</p>" if alert_data.get('action_required') else ""}
        </div>
        <div style="padding: 20px; text-align: center; background-color: #e9ecef;">
            <p>This is an automated alert from your AgriSense system.</p>
        </div>
    </body>
    </html>
    """


def create_report_email_template(content: str) -> str:
    """Create HTML email template for reports"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">AgriSense Report</h1>
        </div>
        <div style="padding: 20px;">
            {content}
        </div>
        <div style="padding: 20px; text-align: center; background-color: #e9ecef;">
            <p>Generated by AgriSense - Smart Farming Solutions</p>
        </div>
    </body>
    </html>
    """


def create_general_email_template(content: str) -> str:
    """Create HTML email template for general notifications"""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0;">AgriSense Notification</h1>
        </div>
        <div style="padding: 20px;">
            <p>{content}</p>
        </div>
        <div style="padding: 20px; text-align: center; background-color: #e9ecef;">
            <p>This is an automated notification from your AgriSense system.</p>
        </div>
    </body>
    </html>
    """


def log_alert_notification(alert_data: Dict[str, Any], notification_results: List[Dict]) -> None:
    """Log alert notification to database or file"""
    # This would log to actual database
    logger.info(f"Alert logged: {alert_data.get('type')} - {len(notification_results)} notifications sent")


def generate_report_content(report_type: str, include_charts: bool, format_type: str) -> str:
    """Generate report content for email"""
    # This would integrate with actual report generation
    return f"""
    <h2>{report_type.title()} Farm Report</h2>
    <p>Here is your automated {report_type} report from AgriSense.</p>

    <h3>Summary</h3>
    <ul>
        <li>System Status: Operational</li>
        <li>Active Sensors: 24</li>
        <li>Water Usage: 1,247L</li>
        <li>Crop Health: 95%</li>
    </ul>

    <h3>Recommendations</h3>
    <ul>
        <li>Continue current irrigation schedule</li>
        <li>Monitor Zone 2 for moisture levels</li>
        <li>Weather forecast looks favorable</li>
    </ul>

    <p>For detailed analytics, please visit your AgriSense dashboard.</p>
    """
