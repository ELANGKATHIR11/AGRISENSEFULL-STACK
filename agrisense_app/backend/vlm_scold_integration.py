"""
SCOLD VLM Integration for Disease and Weed Detection

This module provides integration with SCOLD (Scene-Centric Object Localization and Detection)
Vision Language Model for agricultural disease and weed management.

Supports:
- Disease detection in plant images
- Weed detection and classification
- Localization of affected areas
- Severity assessment
- Treatment recommendations

Environment Variables:
    VLM_ENABLE_SCOLD: Enable SCOLD VLM (default: true)
    SCOLD_BASE_URL: SCOLD API endpoint (default: http://localhost:8001)
    SCOLD_TIMEOUT: Request timeout in seconds (default: 30)
    SCOLD_CONFIDENCE_THRESHOLD: Min confidence for detections (default: 0.5)
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


def _get_scold_config() -> tuple[str, int, float]:
    """Get SCOLD VLM configuration from environment variables."""
    base_url = os.getenv("SCOLD_BASE_URL", "http://localhost:8001").rstrip("/")
    timeout = int(os.getenv("SCOLD_TIMEOUT", "30"))
    confidence_threshold = float(os.getenv("SCOLD_CONFIDENCE_THRESHOLD", "0.5"))
    return base_url, timeout, confidence_threshold


def _image_to_base64(image_data: Any) -> str:
    """Convert image to base64 string."""
    if isinstance(image_data, str):
        # File path
        with open(image_data, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    elif isinstance(image_data, bytes):
        return base64.b64encode(image_data).decode('utf-8')
    elif isinstance(image_data, Image.Image):
        buf = io.BytesIO()
        image_data.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    else:
        raise TypeError(f"Unsupported image type: {type(image_data)}")


def _is_scold_available() -> bool:
    """Check if SCOLD VLM server is accessible."""
    try:
        import requests
        
        base_url, timeout, _ = _get_scold_config()
        response = requests.get(
            f"{base_url}/health",
            timeout=timeout / 2
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"SCOLD availability check failed: {e}")
        return False


def detect_disease_with_scold(
    image_data: Any,
    crop_type: str = "unknown",
    timeout_s: float = None
) -> Optional[Dict[str, Any]]:
    """
    Detect plant diseases using SCOLD VLM.
    
    Args:
        image_data: PIL Image, bytes, or file path
        crop_type: Type of crop (optional, for context)
        timeout_s: Request timeout in seconds
        
    Returns:
        Dict with:
        - disease_detected: bool
        - diseases: List[{name, confidence, bounding_box, severity}]
        - recommendations: List[str]
        - timestamp: str
        - raw_response: dict
        
    Returns None if SCOLD unavailable
    """
    try:
        import requests
        
        base_url, config_timeout, conf_threshold = _get_scold_config()
        timeout = timeout_s or config_timeout
        
        if not _is_scold_available():
            logger.warning(f"SCOLD server not available at {base_url}")
            return None
        
        # Convert image to base64
        image_b64 = _image_to_base64(image_data)
        
        logger.debug(f"Detecting diseases with SCOLD for crop: {crop_type}")
        t0 = time.time()
        
        # Call SCOLD API
        response = requests.post(
            f"{base_url}/api/detect/disease",
            json={
                "image": image_b64,
                "crop_type": crop_type,
                "confidence_threshold": conf_threshold,
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.warning(f"SCOLD API error: {response.status_code}")
            return None
        
        elapsed = time.time() - t0
        data = response.json()
        
        logger.info(f"Disease detection completed in {elapsed:.2f}s")
        
        # Process response
        diseases = []
        if data.get("detections"):
            for detection in data.get("detections", []):
                disease_name = detection.get("class_name", "Unknown")
                confidence = detection.get("confidence", 0.0)
                
                # Filter by confidence threshold
                if confidence < conf_threshold:
                    continue
                
                # Calculate severity from confidence
                if confidence > 0.9:
                    severity = "critical"
                elif confidence > 0.7:
                    severity = "high"
                elif confidence > 0.5:
                    severity = "moderate"
                else:
                    severity = "low"
                
                diseases.append({
                    "name": disease_name,
                    "confidence": round(confidence, 3),
                    "severity": severity,
                    "bounding_box": detection.get("bbox"),
                    "area_percentage": detection.get("area_percentage", 0),
                })
        
        # Generate recommendations
        recommendations = _get_disease_treatment_recommendations(
            [d["name"] for d in diseases],
            crop_type
        )
        
        return {
            "disease_detected": len(diseases) > 0,
            "diseases": diseases,
            "crop_type": crop_type,
            "recommendations": recommendations,
            "detection_count": len(diseases),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time_ms": round(elapsed * 1000),
            "model": "SCOLD VLM",
            "raw_response": data,
        }
        
    except ImportError:
        logger.warning("requests library not installed for SCOLD support")
        return None
    except Exception as e:
        logger.error(f"SCOLD disease detection failed: {e}")
        return None


def detect_weeds_with_scold(
    image_data: Any,
    crop_type: str = "unknown",
    timeout_s: float = None
) -> Optional[Dict[str, Any]]:
    """
    Detect weeds using SCOLD VLM.
    
    Args:
        image_data: PIL Image, bytes, or file path
        crop_type: Type of crop (optional, for context)
        timeout_s: Request timeout in seconds
        
    Returns:
        Dict with:
        - weeds_detected: bool
        - weeds: List[{name, confidence, bounding_box, coverage_percentage}]
        - severity: str (low, moderate, high, critical)
        - treatment_options: List[str]
        - timestamp: str
        
    Returns None if SCOLD unavailable
    """
    try:
        import requests
        
        base_url, config_timeout, conf_threshold = _get_scold_config()
        timeout = timeout_s or config_timeout
        
        if not _is_scold_available():
            logger.warning(f"SCOLD server not available at {base_url}")
            return None
        
        # Convert image to base64
        image_b64 = _image_to_base64(image_data)
        
        logger.debug(f"Detecting weeds with SCOLD for crop: {crop_type}")
        t0 = time.time()
        
        # Call SCOLD API
        response = requests.post(
            f"{base_url}/api/detect/weed",
            json={
                "image": image_b64,
                "crop_type": crop_type,
                "confidence_threshold": conf_threshold,
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.warning(f"SCOLD API error: {response.status_code}")
            return None
        
        elapsed = time.time() - t0
        data = response.json()
        
        logger.info(f"Weed detection completed in {elapsed:.2f}s")
        
        # Process response
        weeds = []
        total_coverage = 0.0
        
        if data.get("detections"):
            for detection in data.get("detections", []):
                weed_name = detection.get("class_name", "Unknown Weed")
                confidence = detection.get("confidence", 0.0)
                coverage = detection.get("area_percentage", 0)
                
                # Filter by confidence threshold
                if confidence < conf_threshold:
                    continue
                
                weeds.append({
                    "name": weed_name,
                    "confidence": round(confidence, 3),
                    "coverage_percentage": round(coverage, 1),
                    "bounding_box": detection.get("bbox"),
                    "class_id": detection.get("class_id"),
                })
                total_coverage += coverage
        
        # Determine overall severity
        if total_coverage > 50:
            severity = "critical"
        elif total_coverage > 30:
            severity = "high"
        elif total_coverage > 10:
            severity = "moderate"
        else:
            severity = "low"
        
        # Get treatment options
        treatment_options = _get_weed_treatment_recommendations(
            [w["name"] for w in weeds],
            severity,
            crop_type
        )
        
        return {
            "weeds_detected": len(weeds) > 0,
            "weeds": weeds,
            "crop_type": crop_type,
            "total_coverage_percentage": round(total_coverage, 1),
            "severity": severity,
            "treatment_options": treatment_options,
            "detection_count": len(weeds),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time_ms": round(elapsed * 1000),
            "model": "SCOLD VLM",
            "raw_response": data,
        }
        
    except ImportError:
        logger.warning("requests library not installed for SCOLD support")
        return None
    except Exception as e:
        logger.error(f"SCOLD weed detection failed: {e}")
        return None


def _get_disease_treatment_recommendations(
    diseases: List[str],
    crop_type: str = "unknown"
) -> List[str]:
    """Generate treatment recommendations for detected diseases."""
    
    disease_treatments = {
        "powdery mildew": [
            "Apply sulfur-based fungicide",
            "Ensure good air circulation",
            "Reduce humidity",
            "Remove infected leaves"
        ],
        "leaf spot": [
            "Apply copper fungicide",
            "Remove infected leaves",
            "Avoid overhead watering",
            "Maintain proper spacing"
        ],
        "blight": [
            "Apply fungicide containing chlorothalonil",
            "Remove infected plants immediately",
            "Improve drainage",
            "Avoid working in wet conditions"
        ],
        "rust": [
            "Apply sulfur or rust-specific fungicide",
            "Remove infected leaves",
            "Improve air circulation",
            "Reduce humidity levels"
        ],
        "wilt": [
            "Remove infected plant",
            "Improve soil drainage",
            "Rotate crops",
            "Sanitize equipment"
        ]
    }
    
    recommendations = []
    for disease in diseases:
        disease_lower = disease.lower()
        if disease_lower in disease_treatments:
            recommendations.extend(disease_treatments[disease_lower])
        else:
            # Generic recommendation
            recommendations.append(f"Consult agricultural extension for {disease}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)
    
    return unique_recs[:5]  # Return top 5


def _get_weed_treatment_recommendations(
    weeds: List[str],
    severity: str = "low",
    crop_type: str = "unknown"
) -> List[str]:
    """Generate treatment recommendations for detected weeds."""
    
    weed_treatments = {
        "bermuda grass": [
            "Use glyphosate herbicide",
            "Manual removal for small areas",
            "Mulching to prevent growth"
        ],
        "crabgrass": [
            "Apply pre-emergent herbicide early spring",
            "Post-emergent herbicide in summer",
            "Maintain dense crop coverage"
        ],
        "chickweed": [
            "Hand pull in moist soil",
            "Apply selective herbicide",
            "Use pre-emergent before germination"
        ],
        "dandelion": [
            "Manual removal with root extraction",
            "Targeted herbicide application",
            "Repeated removal to exhaust root reserves"
        ],
        "thistle": [
            "Cut below soil line regularly",
            "Apply herbicide to fresh cuts",
            "Remove before seed production"
        ]
    }
    
    recommendations = []
    
    # Add severity-based recommendations
    if severity == "critical":
        recommendations.append("URGENT: Immediate weed management required")
        recommendations.append("Consider herbicide application")
    elif severity == "high":
        recommendations.append("Schedule weed management within 1-2 weeks")
    
    # Add specific weed treatments
    for weed in weeds:
        weed_lower = weed.lower()
        if weed_lower in weed_treatments:
            recommendations.extend(weed_treatments[weed_lower])
    
    # Add general recommendations
    if severity in ["high", "critical"]:
        recommendations.append("Monitor area regularly for new growth")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)
    
    return unique_recs[:6]  # Return top 6


def scold_vlm_status() -> Dict[str, Any]:
    """
    Get status of SCOLD VLM integration.
    
    Returns:
        Dict with availability and configuration info
    """
    base_url, timeout, conf_threshold = _get_scold_config()
    available = _is_scold_available()
    
    return {
        "available": available,
        "base_url": base_url,
        "timeout": timeout,
        "confidence_threshold": conf_threshold,
        "model": "SCOLD VLM",
        "features": ["disease_detection", "weed_detection", "localization"],
        "status": "ready" if available else "unavailable"
    }


# Initialize logging
logger.info("SCOLD VLM integration initialized")
logger.debug(f"Configuration: base_url={_get_scold_config()[0]}, timeout={_get_scold_config()[1]}s")
