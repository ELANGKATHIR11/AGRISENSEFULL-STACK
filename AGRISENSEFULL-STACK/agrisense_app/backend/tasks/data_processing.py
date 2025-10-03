"""
Data Processing Tasks
Background tasks for sensor data processing, validation, and analysis
"""
# type: ignore

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

try:
    from celery import current_task  # type: ignore
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    current_task = None  # type: ignore

from ..celery_config import celery_app, CELERY_AVAILABLE
from ..core.engine import RecoEngine

if isinstance(current_task, list):
    current_task = None

logger = logging.getLogger(__name__)


# Conditional task decorators
def task_decorator(func):
    """Decorator that conditionally applies Celery task decoration"""
    if CELERY_AVAILABLE and celery_app:
        return celery_app.task(bind=True)(func)
    else:
        # Return a wrapper that makes the function look like a Celery task
        def wrapper(*args, **kwargs):
            # Skip 'self' parameter if present 
            if args and hasattr(args[0], 'request'):
                return func(*args, **kwargs)
            else:
                return func(None, *args, **kwargs)
        wrapper.delay = lambda *args, **kwargs: wrapper(*args, **kwargs)
        wrapper.apply_async = lambda *args, **kwargs: wrapper(*args, **kwargs)
        return wrapper


def safe_update_task_state(state, meta):  # type: ignore
    """Safely update task state if current_task is available"""
    if current_task and hasattr(current_task, 'update_state') and not isinstance(current_task, list):
        try:
            current_task.update_state(state=state, meta=meta)  # type: ignore
        except Exception:
            pass


@task_decorator
def process_sensor_data_batch(self, batch_size: int = 100) -> Dict[str, Any]:
    """
    Process a batch of recent sensor readings
    Apply data validation, outlier detection, and feature engineering
    """
    try:
        # Update task progress
        safe_update_task_state("PROGRESS", {"progress": 10, "status": "Starting data processing"})

        # Get recent unprocessed sensor readings
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)  # Process last hour of data

        safe_update_task_state("PROGRESS", {"progress": 20, "status": "Fetching sensor data"})

        # This would be replaced with actual database query
        readings = []  # get_sensor_readings_range(start_time, end_time, limit=batch_size)

        if not readings:
            return {"status": "completed", "processed_count": 0, "message": "No new data to process"}

        processed_count = 0
        anomalies_detected = 0

        for i, reading in enumerate(readings):
            safe_update_task_state(
                "PROGRESS",
                {"progress": 20 + (i / len(readings)) * 60, "status": f"Processing reading {i+1}/{len(readings)}"}
            )

            # Data validation and cleaning
            cleaned_reading = validate_and_clean_reading(reading)

            # Outlier detection
            if detect_outlier(cleaned_reading):
                anomalies_detected += 1
                logger.warning(f"Anomaly detected in reading {reading.get('id', 'unknown')}")

            # Feature engineering
            engineer_features(cleaned_reading)

            # Store processed data
            # store_processed_reading(enhanced_reading)

            processed_count += 1

        safe_update_task_state("PROGRESS", {"progress": 90, "status": "Finalizing processing"})

        # Generate processing summary
        summary = {
            "status": "completed",
            "processed_count": processed_count,
            "anomalies_detected": anomalies_detected,
            "processing_time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Processed {processed_count} sensor readings with {anomalies_detected} anomalies")
        return summary

    except Exception as exc:
        logger.error(f"Data processing failed: {str(exc)}")
        self.retry(countdown=60, exc=exc)
        return {"status": "failed", "error": str(exc), "timestamp": datetime.utcnow().isoformat()}


@task_decorator
def process_individual_reading(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single sensor reading
    Real-time processing for immediate feedback
    """
    try:
        safe_update_task_state("PROGRESS", {"progress": 25, "status": "Validating reading"})

        # Validate reading
        validated_reading = validate_and_clean_reading(reading_data)

        safe_update_task_state("PROGRESS", {"progress": 50, "status": "Analyzing data"})

        # Feature engineering
        enhanced_reading = engineer_features(validated_reading)

        safe_update_task_state("PROGRESS", {"progress": 75, "status": "Generating insights"})

        # Generate recommendations
        reco_engine = RecoEngine()
        recommendations = reco_engine.recommend(enhanced_reading)

        result = {
            "status": "completed",
            "original_reading": reading_data,
            "processed_reading": enhanced_reading,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return result

    except Exception as exc:
        logger.error(f"Individual reading processing failed: {str(exc)}")
        raise


@task_decorator
def aggregate_sensor_data(self, time_period: str = "1h") -> Dict[str, Any]:
    """
    Aggregate sensor data over specified time periods
    Create summary statistics and trends
    """
    try:
        safe_update_task_state("PROGRESS", {"progress": 10, "status": "Setting up aggregation"})

        # Parse time period
        period_mapping = {
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "1d": timedelta(days=1),
        }

        if time_period not in period_mapping:
            raise ValueError(f"Invalid time period: {time_period}")

        delta = period_mapping[time_period]
        end_time = datetime.utcnow()
        start_time = end_time - delta

        safe_update_task_state("PROGRESS", {"progress": 30, "status": "Fetching data"})

        # Get readings for the time period
        # readings = get_sensor_readings_range(start_time, end_time)
        readings = []  # Placeholder

        if not readings:
            return {"status": "completed", "aggregated_data": {}, "message": "No data available for aggregation"}

        safe_update_task_state("PROGRESS", {"progress": 60, "status": "Computing aggregations"})

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(readings)

        # Compute aggregations
        aggregations = {
            "temperature": {
                "min": float(df["temperature_c"].min()) if "temperature_c" in df.columns else None,
                "max": float(df["temperature_c"].max()) if "temperature_c" in df.columns else None,
                "mean": float(df["temperature_c"].mean()) if "temperature_c" in df.columns else None,
                "std": float(df["temperature_c"].std()) if "temperature_c" in df.columns else None,
            },
            "humidity": {
                "min": float(df["humidity_pct"].min()) if "humidity_pct" in df.columns else None,
                "max": float(df["humidity_pct"].max()) if "humidity_pct" in df.columns else None,
                "mean": float(df["humidity_pct"].mean()) if "humidity_pct" in df.columns else None,
                "std": float(df["humidity_pct"].std()) if "humidity_pct" in df.columns else None,
            },
            "soil_moisture": {
                "min": float(df["moisture_pct"].min()) if "moisture_pct" in df.columns else None,
                "max": float(df["moisture_pct"].max()) if "moisture_pct" in df.columns else None,
                "mean": float(df["moisture_pct"].mean()) if "moisture_pct" in df.columns else None,
                "std": float(df["moisture_pct"].std()) if "moisture_pct" in df.columns else None,
            },
            "data_points": len(df),
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "period": time_period},
        }

        safe_update_task_state("PROGRESS", {"progress": 90, "status": "Finalizing results"})

        return {"status": "completed", "aggregated_data": aggregations, "timestamp": datetime.utcnow().isoformat()}

    except Exception as exc:
        logger.error(f"Data aggregation failed: {str(exc)}")
        raise


# Helper functions


def validate_and_clean_reading(reading: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean sensor reading data"""
    cleaned = reading.copy()

    # Temperature validation (reasonable range for agriculture)
    if "temperature_c" in cleaned:
        temp = cleaned["temperature_c"]
        if temp < -40 or temp > 60:
            logger.warning(f"Temperature out of range: {temp}°C")
            cleaned["temperature_c_original"] = temp
            cleaned["temperature_c"] = max(-40, min(60, temp))  # Clamp to range

    # Humidity validation (0-100%)
    if "humidity_pct" in cleaned:
        humidity = cleaned["humidity_pct"]
        if humidity < 0 or humidity > 100:
            logger.warning(f"Humidity out of range: {humidity}%")
            cleaned["humidity_pct_original"] = humidity
            cleaned["humidity_pct"] = max(0, min(100, humidity))

    # Soil moisture validation (0-100%)
    if "moisture_pct" in cleaned:
        moisture = cleaned["moisture_pct"]
        if moisture < 0 or moisture > 100:
            logger.warning(f"Soil moisture out of range: {moisture}%")
            cleaned["moisture_pct_original"] = moisture
            cleaned["moisture_pct"] = max(0, min(100, moisture))

    # Add validation timestamp
    cleaned["validated_at"] = datetime.utcnow().isoformat()

    return cleaned


def detect_outlier(reading: Dict[str, Any]) -> bool:
    """Detect if reading is an outlier using simple statistical methods"""
    # This is a simplified outlier detection
    # In production, you'd use more sophisticated methods

    outlier_flags = []

    # Temperature outlier detection
    if "temperature_c" in reading:
        temp = reading["temperature_c"]
        # Consider extreme temperatures as outliers
        if temp < -20 or temp > 45:
            outlier_flags.append("temperature_extreme")

    # Humidity outlier detection
    if "humidity_pct" in reading:
        humidity = reading["humidity_pct"]
        # Very low or very high humidity
        if humidity < 10 or humidity > 95:
            outlier_flags.append("humidity_extreme")

    # Add outlier flags to reading
    if outlier_flags:
        reading["outlier_flags"] = outlier_flags
        return True

    return False


def engineer_features(reading: Dict[str, Any]) -> Dict[str, Any]:
    """Engineer additional features from sensor reading"""
    enhanced = reading.copy()

    # Calculate derived features
    if "temperature_c" in enhanced and "humidity_pct" in enhanced:
        temp_c = enhanced["temperature_c"]
        humidity = enhanced["humidity_pct"]

        # Heat index calculation (simplified)
        if temp_c >= 26.7:  # 80°F
            heat_index = -42.379 + 2.04901523 * temp_c + 10.14333127 * humidity
            enhanced["heat_index_c"] = heat_index

        # Dew point calculation (simplified)
        dew_point = temp_c - ((100 - humidity) / 5)
        enhanced["dew_point_c"] = dew_point

        # Vapor pressure deficit
        vpd = 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3)) * (1 - humidity / 100)
        enhanced["vpd_kpa"] = vpd

    # Stress indicators
    stress_indicators = []

    if "moisture_pct" in enhanced:
        moisture = enhanced["moisture_pct"]
        if moisture < 30:
            stress_indicators.append("drought_stress")
        elif moisture > 80:
            stress_indicators.append("waterlog_stress")

    if "temperature_c" in enhanced:
        temp = enhanced["temperature_c"]
        if temp > 35:
            stress_indicators.append("heat_stress")
        elif temp < 5:
            stress_indicators.append("cold_stress")

    enhanced["stress_indicators"] = stress_indicators
    enhanced["stress_level"] = len(stress_indicators)

    # Add feature engineering timestamp
    enhanced["features_engineered_at"] = datetime.utcnow().isoformat()

    return enhanced
