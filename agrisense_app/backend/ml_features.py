import numpy as np
from typing import Dict, Any, List

def preprocess_reading(reading: Dict[str, Any]) -> np.ndarray:
    """
    Preprocess sensor reading for ML models
    Args:
        reading: Sensor reading dictionary
    Returns:
        np.ndarray: Preprocessed features
    """
    # Feature extraction and normalization
    features = [
        reading.get("moisture_pct", 0.0),
        reading.get("temperature_c", 0.0),
        reading.get("ec_dS_m", 0.0),
        reading.get("ph", 6.5),
        {"sand": 0, "loam": 1, "clay": 2}.get(reading.get("soil_type", "loam").lower(), 1),
        reading.get("crop_kc", 1.0)
    ]
    return np.array(features)


def create_time_series_features(readings: List[Dict[str, Any]]) -> np.ndarray:
    """
    Create time-series features from a sequence of readings
    Args:
        readings: List of sensor readings
    Returns:
        np.ndarray: Time-series features
    """
    # TODO: Implement time-series feature engineering
    return np.array([preprocess_reading(r) for r in readings])
