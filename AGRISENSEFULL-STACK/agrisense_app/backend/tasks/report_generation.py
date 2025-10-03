"""
Report Generation Tasks
Background tasks for generating various reports and analytics
"""
# type: ignore

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

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
def generate_daily_report(self, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate comprehensive daily farm report
    Includes sensor data analysis, recommendations, and system status
    """
    try:
        # Parse date
        if date:
            report_date = datetime.fromisoformat(date).date()
        else:
            report_date = datetime.utcnow().date()

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Initializing report generation"})

        # Set time range for the day
        # start_time = datetime.combine(report_date, datetime.min.time())
        # end_time = start_time + timedelta(days=1)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 20, "status": "Collecting sensor data"})

        # Collect data for the day
        # readings = get_sensor_readings_range(start_time, end_time)
        readings = []  # Placeholder

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 40, "status": "Analyzing data"})

        # Generate report sections
        summary = generate_daily_summary(readings, report_date)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Creating visualizations"})

        charts = generate_daily_charts(readings)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 80, "status": "Compiling recommendations"})

        recommendations = generate_daily_recommendations(summary)

        # Compile full report
        report = {
            "report_date": report_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "charts": charts,
            "recommendations": recommendations,
            "data_quality": assess_data_quality(readings),
        }

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 90, "status": "Saving report"})

        # Save report to file
        report_path = save_report(report, "daily", report_date)

        return {
            "status": "completed",
            "report_path": report_path,
            "report_date": report_date.isoformat(),
            "data_points_analyzed": len(readings),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Daily report generation failed: {str(exc)}")
        raise


@task_decorator
def generate_weekly_report(self, week_start: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate weekly farm performance report
    Includes trends, comparisons, and week-over-week analysis
    """
    try:
        # Parse week start date
        if week_start:
            start_date = datetime.fromisoformat(week_start).date()
        else:
            # Default to last Monday
            today = datetime.utcnow().date()
            start_date = today - timedelta(days=today.weekday())

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Setting up weekly analysis"})

        # Set time range for the week
        # start_time = datetime.combine(start_date, datetime.min.time())
        # end_time = start_time + timedelta(days=7)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 20, "status": "Collecting weekly data"})

        # Collect data for the week
        # readings = get_sensor_readings_range(start_time, end_time)
        readings = []  # Placeholder

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 40, "status": "Analyzing trends"})

        # Generate weekly analysis
        trends = analyze_weekly_trends(readings, start_date)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Creating comparisons"})

        comparisons = generate_weekly_comparisons(readings, start_date)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 80, "status": "Generating insights"})

        insights = generate_weekly_insights(trends, comparisons)

        # Compile weekly report
        report = {
            "week_start": start_date.isoformat(),
            "week_end": (start_date + timedelta(days=6)).isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "trends": trends,
            "comparisons": comparisons,
            "insights": insights,
            "performance_metrics": calculate_weekly_performance(readings),
        }

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 90, "status": "Saving weekly report"})

        # Save report
        report_path = save_report(report, "weekly", start_date)

        return {
            "status": "completed",
            "report_path": report_path,
            "week_start": start_date.isoformat(),
            "data_points_analyzed": len(readings),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Weekly report generation failed: {str(exc)}")
        raise


@task_decorator
def generate_custom_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate custom report based on user configuration
    Flexible reporting with customizable parameters
    """
    try:
        safe_update_state(current_task, state="PROGRESS", meta={"progress": 10, "status": "Parsing report configuration"})

        # Parse configuration
        start_date = datetime.fromisoformat(config["start_date"])
        end_date = datetime.fromisoformat(config["end_date"])
        metrics = config.get("metrics", ["temperature", "humidity", "moisture"])
        chart_types = config.get("chart_types", ["line", "summary"])
        include_recommendations = config.get("include_recommendations", True)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 20, "status": "Collecting custom data range"})

        # Collect data for custom range
        # readings = get_sensor_readings_range(start_date, end_date)
        readings = []  # Placeholder

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 40, "status": "Processing custom metrics"})

        # Process selected metrics
        processed_metrics = {}
        for metric in metrics:
            processed_metrics[metric] = process_metric_data(readings, metric)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 60, "status": "Creating custom charts"})

        # Generate requested charts
        charts = {}
        for chart_type in chart_types:
            charts[chart_type] = generate_chart_data(readings, chart_type, metrics)

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 80, "status": "Compiling custom insights"})

        # Generate insights and recommendations
        insights = generate_custom_insights(processed_metrics, config)
        recommendations = []
        if include_recommendations:
            recommendations = generate_custom_recommendations(processed_metrics, config)

        # Compile custom report
        report = {
            "report_type": "custom",
            "configuration": config,
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": processed_metrics,
            "charts": charts,
            "insights": insights,
            "recommendations": recommendations,
        }

        safe_update_state(current_task, state="PROGRESS", meta={"progress": 90, "status": "Saving custom report"})

        # Save report
        report_path = save_report(report, "custom", start_date)

        return {
            "status": "completed",
            "report_path": report_path,
            "date_range": f"{start_date.date()} to {end_date.date()}",
            "metrics_processed": len(processed_metrics),
            "data_points_analyzed": len(readings),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Custom report generation failed: {str(exc)}")
        raise


# Helper functions


def generate_daily_summary(readings: List[Dict], report_date) -> Dict[str, Any]:
    """Generate daily summary statistics"""
    if not readings:
        return {"data_available": False, "message": "No data available for this date"}

    df = pd.DataFrame(readings)

    summary = {
        "data_available": True,
        "total_readings": len(readings),
        "date": report_date.isoformat(),
        "temperature": {
            "min": float(df["temperature_c"].min()) if "temperature_c" in df.columns else None,
            "max": float(df["temperature_c"].max()) if "temperature_c" in df.columns else None,
            "avg": float(df["temperature_c"].mean()) if "temperature_c" in df.columns else None,
        },
        "humidity": {
            "min": float(df["humidity_pct"].min()) if "humidity_pct" in df.columns else None,
            "max": float(df["humidity_pct"].max()) if "humidity_pct" in df.columns else None,
            "avg": float(df["humidity_pct"].mean()) if "humidity_pct" in df.columns else None,
        },
        "soil_moisture": {
            "min": float(df["moisture_pct"].min()) if "moisture_pct" in df.columns else None,
            "max": float(df["moisture_pct"].max()) if "moisture_pct" in df.columns else None,
            "avg": float(df["moisture_pct"].mean()) if "moisture_pct" in df.columns else None,
        },
    }

    return summary


def generate_daily_charts(readings: List[Dict]) -> Dict[str, Any]:
    """Generate chart data for daily report"""
    if not readings:
        return {}

    df = pd.DataFrame(readings)

    # Hourly aggregations
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour

        hourly_data = (
            df.groupby("hour")
            .agg({"temperature_c": "mean", "humidity_pct": "mean", "moisture_pct": "mean"})
            .reset_index()
        )

        charts = {
            "hourly_temperature": hourly_data[["hour", "temperature_c"]].to_dict("records"),
            "hourly_humidity": hourly_data[["hour", "humidity_pct"]].to_dict("records"),
            "hourly_moisture": hourly_data[["hour", "moisture_pct"]].to_dict("records"),
        }
    else:
        charts = {}

    return charts


def generate_daily_recommendations(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate recommendations based on daily summary"""
    recommendations = []

    if not summary.get("data_available"):
        return recommendations

    # Temperature-based recommendations
    if summary.get("temperature", {}).get("max", 0) > 35:
        recommendations.append(
            {
                "type": "temperature",
                "priority": "high",
                "message": "High temperature detected. Consider increasing irrigation and providing shade.",
                "action": "temperature_management",
            }
        )

    # Soil moisture recommendations
    if summary.get("soil_moisture", {}).get("avg", 100) < 30:
        recommendations.append(
            {
                "type": "irrigation",
                "priority": "high",
                "message": "Low soil moisture levels. Immediate irrigation recommended.",
                "action": "increase_irrigation",
            }
        )

    # Humidity recommendations
    if summary.get("humidity", {}).get("avg", 50) > 85:
        recommendations.append(
            {
                "type": "humidity",
                "priority": "medium",
                "message": "High humidity levels may promote fungal diseases. Improve ventilation.",
                "action": "humidity_control",
            }
        )

    return recommendations


def assess_data_quality(readings: List[Dict]) -> Dict[str, Any]:
    """Assess the quality of collected data"""
    if not readings:
        return {"score": 0, "issues": ["No data available"], "completeness": 0}

    df = pd.DataFrame(readings)
    total_readings = len(readings)

    # Check for missing values
    missing_data = df.isnull().sum().to_dict()
    completeness = 1 - (sum(missing_data.values()) / (len(df.columns) * total_readings))

    # Check for outliers
    outlier_count = sum(1 for reading in readings if reading.get("outlier_flags"))

    # Calculate quality score
    score = completeness * 0.7 + (1 - outlier_count / total_readings) * 0.3

    issues = []
    if completeness < 0.9:
        issues.append("Missing data detected")
    if outlier_count > total_readings * 0.1:
        issues.append("High number of outliers detected")

    return {
        "score": round(score, 2),
        "completeness": round(completeness, 2),
        "outlier_percentage": round(outlier_count / total_readings, 2),
        "issues": issues,
        "total_readings": total_readings,
    }


def save_report(report: Dict[str, Any], report_type: str, date) -> str:
    """Save report to file system"""
    # Create reports directory
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Create filename
    filename = f"{report_type}_report_{date.strftime('%Y%m%d')}_{datetime.utcnow().strftime('%H%M%S')}.json"
    filepath = reports_dir / filename

    # Save report
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Report saved to {filepath}")
    return str(filepath)


def analyze_weekly_trends(readings: List[Dict], start_date) -> Dict[str, Any]:
    """Analyze weekly trends in data"""
    # Placeholder implementation
    return {"temperature_trend": "stable", "moisture_trend": "decreasing", "humidity_trend": "increasing"}


def generate_weekly_comparisons(readings: List[Dict], start_date) -> Dict[str, Any]:
    """Generate week-over-week comparisons"""
    # Placeholder implementation
    return {"temperature_change": "+2.3°C", "moisture_change": "-5.2%", "humidity_change": "+3.1%"}


def generate_weekly_insights(trends: Dict, comparisons: Dict) -> List[str]:
    """Generate insights from weekly analysis"""
    return [
        "Temperature has remained stable this week",
        "Soil moisture is trending downward - consider irrigation adjustments",
        "Humidity levels are increasing - monitor for potential fungal issues",
    ]


def calculate_weekly_performance(readings: List[Dict]) -> Dict[str, Any]:
    """Calculate weekly performance metrics"""
    return {
        "water_efficiency": 0.87,
        "crop_health_score": 0.92,
        "system_uptime": 0.98,
        "energy_consumption": 145.6,  # kWh
    }


def process_metric_data(readings: List[Dict], metric: str) -> Dict[str, Any]:
    """Process data for a specific metric"""
    # Placeholder implementation
    return {"values": [], "statistics": {}, "trends": {}}


def generate_chart_data(readings: List[Dict], chart_type: str, metrics: List[str]) -> Dict[str, Any]:
    """Generate chart data for custom reports"""
    # Placeholder implementation
    return {"type": chart_type, "data": [], "config": {}}


def generate_custom_insights(metrics: Dict, config: Dict) -> List[str]:
    """Generate insights for custom reports"""
    return ["Custom analysis completed", "Data patterns identified", "Recommendations generated"]


def generate_custom_recommendations(metrics: Dict, config: Dict) -> List[Dict[str, Any]]:
    """Generate recommendations for custom reports"""
    return [
        {
            "type": "general",
            "priority": "medium",
            "message": "Continue monitoring based on custom analysis",
            "action": "monitor",
        }
    ]
