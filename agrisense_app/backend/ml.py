import os
from typing import Any, Dict, Optional
class RuleBasedFallback:
    """
    Rule-based fallback when ML is disabled
    """
    def predict_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        # Use the rule-based engine
        from .core.engine import RecoEngine  # Local import to avoid circular dependency

        engine = RecoEngine()
        return engine.recommend(reading)


def model_loader() -> Any:
    """
    Load ML models based on environment configuration
    Returns:
        A model object or RuleBasedFallback if ML is disabled
    """
    _disable_ml = str(os.getenv("AGRISENSE_DISABLE_ML", "0")).lower() in ("1", "true", "yes")
    if _disable_ml:
        return RuleBasedFallback()
    
    # TODO: Implement actual model loading
    # For now, we return the rule-based fallback
    return RuleBasedFallback()


def predict_reading(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict using the loaded model
    Args:
        reading: Sensor reading dictionary
    Returns:
        Prediction dictionary
    """
    model = model_loader()
    return model.predict_reading(reading)


def is_ml_enabled() -> bool:
    """
    Check if ML is enabled
    Returns:
        bool: True if ML is enabled, False otherwise
    """
    _disable_ml = str(os.getenv("AGRISENSE_DISABLE_ML", "0")).lower() in ("1", "true", "yes")
    return not _disable_ml
