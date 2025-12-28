"""
SCOLD VLM Service Integration for AgriSense
=============================================

Provides a unified interface to the locally deployed SCOLD VLM model.
Handles disease detection, weed identification, and crop health assessment.

Key Features:
-------------
- Local SCOLD model inference (offline-capable)
- Image preprocessing and normalization
- Agricultural domain-specific prompts
- Bounding box detection for precision agriculture
- Fallback mechanisms when model unavailable

Environment Variables:
----------------------
    SCOLD_BASE_URL: Base URL for SCOLD VLM server (default: http://localhost:8001)
    SCOLD_MODEL_PATH: Path to SCOLD model files
    SCOLD_CONFIDENCE_THRESHOLD: Minimum confidence for detections (default: 0.6)
    SCOLD_TIMEOUT: Request timeout in seconds (default: 30)
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration & Types
# ============================================================================

class SCOLDAnalysisType(str, Enum):
    """Types of agricultural analysis supported by SCOLD VLM"""
    DISEASE_DETECTION = "disease_detection"
    WEED_IDENTIFICATION = "weed_identification"
    CROP_HEALTH_ASSESSMENT = "crop_health"
    PEST_DETECTION = "pest_detection"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    GENERAL_PLANT_ANALYSIS = "general"


@dataclass
class SCOLDDetection:
    """Single detection result from SCOLD VLM"""
    label: str
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # x1, y1, x2, y2
    attributes: Dict[str, Any] = None
    severity: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SCOLDAnalysisResult:
    """Complete analysis result from SCOLD VLM"""
    analysis_type: SCOLDAnalysisType
    detections: List[SCOLDDetection]
    overall_confidence: float
    summary: str
    recommendations: List[str]
    metadata: Dict[str, Any]
    processing_time_ms: float
    model_version: str = "SCOLD-1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'analysis_type': self.analysis_type.value,
            'detections': [
                {
                    'label': d.label,
                    'confidence': d.confidence,
                    'bounding_box': d.bounding_box,
                    'attributes': d.attributes or {},
                    'severity': d.severity,
                    'description': d.description
                }
                for d in self.detections
            ],
            'overall_confidence': self.overall_confidence,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'metadata': self.metadata,
            'processing_time_ms': self.processing_time_ms,
            'model_version': self.model_version
        }


# ============================================================================
# SCOLD VLM Service
# ============================================================================

class SCOLDVLMService:
    """
    Service wrapper for SCOLD VLM model integration
    
    Provides high-level API for agricultural image analysis using
    the locally deployed SCOLD vision-language model.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.6,
        timeout: int = 30
    ):
        """
        Initialize SCOLD VLM service
        
        Args:
            base_url: SCOLD server URL (default: http://localhost:8001)
            model_path: Local path to SCOLD model files
            confidence_threshold: Minimum confidence for detections
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "SCOLD_BASE_URL", 
            "http://localhost:8001"
        )
        self.model_path = model_path or os.getenv(
            "SCOLD_MODEL_PATH",
            str(Path(__file__).parent.parent.parent / "AI_Models" / "scold")
        )
        self.confidence_threshold = float(
            os.getenv("SCOLD_CONFIDENCE_THRESHOLD", str(confidence_threshold))
        )
        self.timeout = int(os.getenv("SCOLD_TIMEOUT", str(timeout)))
        
        self._model_loaded = False
        self._check_availability()
        
        logger.info(
            f"🔬 SCOLD VLM Service initialized: "
            f"Available={'✅' if self._model_loaded else '❌'} "
            f"URL={self.base_url}"
        )
    
    def _check_availability(self):
        """Check if SCOLD model is available"""
        try:
            import requests
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            self._model_loaded = response.status_code == 200
        except Exception as e:
            logger.warning(f"SCOLD VLM not available: {e}")
            self._model_loaded = False
    
    # ========================================================================
    # Disease Detection
    # ========================================================================
    
    def detect_disease(
        self,
        image_data: Union[str, bytes, Image.Image],
        crop_type: Optional[str] = None,
        return_bounding_boxes: bool = True
    ) -> SCOLDAnalysisResult:
        """
        Detect plant diseases using SCOLD VLM
        
        Args:
            image_data: Image file path, bytes, or PIL Image
            crop_type: Type of crop (e.g., 'tomato', 'wheat')
            return_bounding_boxes: Include bounding boxes for affected areas
            
        Returns:
            SCOLDAnalysisResult with disease detections
        """
        prompt = self._build_disease_prompt(crop_type)
        
        return self._analyze_image(
            image_data=image_data,
            prompt=prompt,
            analysis_type=SCOLDAnalysisType.DISEASE_DETECTION,
            return_bounding_boxes=return_bounding_boxes,
            context={'crop_type': crop_type}
        )
    
    def _build_disease_prompt(self, crop_type: Optional[str] = None) -> str:
        """Build disease detection prompt for SCOLD VLM"""
        if crop_type:
            return (
                f"Analyze this {crop_type} plant image for diseases. "
                f"Identify any diseases, their severity (mild/moderate/severe), "
                f"affected plant parts, and estimated coverage percentage. "
                f"Provide specific disease names and treatment recommendations."
            )
        else:
            return (
                "Analyze this plant image for diseases. "
                "Identify any diseases, their severity, affected plant parts, "
                "and provide treatment recommendations."
            )
    
    # ========================================================================
    # Weed Identification
    # ========================================================================
    
    def identify_weeds(
        self,
        image_data: Union[str, bytes, Image.Image],
        crop_type: Optional[str] = None,
        return_bounding_boxes: bool = True
    ) -> SCOLDAnalysisResult:
        """
        Identify weeds in agricultural field images
        
        Args:
            image_data: Image file path, bytes, or PIL Image
            crop_type: Type of crop being grown
            return_bounding_boxes: Include bounding boxes for weed locations
            
        Returns:
            SCOLDAnalysisResult with weed identifications
        """
        prompt = self._build_weed_prompt(crop_type)
        
        return self._analyze_image(
            image_data=image_data,
            prompt=prompt,
            analysis_type=SCOLDAnalysisType.WEED_IDENTIFICATION,
            return_bounding_boxes=return_bounding_boxes,
            context={'crop_type': crop_type}
        )
    
    def _build_weed_prompt(self, crop_type: Optional[str] = None) -> str:
        """Build weed identification prompt for SCOLD VLM"""
        if crop_type:
            return (
                f"Identify weeds in this {crop_type} field image. "
                f"For each weed: provide common name, scientific name if possible, "
                f"precise location, coverage percentage, and management recommendations. "
                f"Distinguish between weeds and the {crop_type} crop plants."
            )
        else:
            return (
                "Identify weeds in this agricultural field image. "
                "For each weed: provide common name, location, coverage percentage, "
                "and management recommendations."
            )
    
    # ========================================================================
    # Crop Health Assessment
    # ========================================================================
    
    def assess_crop_health(
        self,
        image_data: Union[str, bytes, Image.Image],
        crop_type: Optional[str] = None
    ) -> SCOLDAnalysisResult:
        """
        Assess overall crop health
        
        Args:
            image_data: Image file path, bytes, or PIL Image
            crop_type: Type of crop
            
        Returns:
            SCOLDAnalysisResult with health assessment
        """
        prompt = self._build_health_prompt(crop_type)
        
        return self._analyze_image(
            image_data=image_data,
            prompt=prompt,
            analysis_type=SCOLDAnalysisType.CROP_HEALTH_ASSESSMENT,
            return_bounding_boxes=False,
            context={'crop_type': crop_type}
        )
    
    def _build_health_prompt(self, crop_type: Optional[str] = None) -> str:
        """Build crop health assessment prompt"""
        if crop_type:
            return (
                f"Assess the overall health of this {crop_type} crop. "
                f"Evaluate: leaf color, growth stage, signs of stress, "
                f"nutrient deficiency, pest damage, disease symptoms. "
                f"Provide a health score (0-100) and recommendations."
            )
        else:
            return (
                "Assess the overall health of crops in this image. "
                "Evaluate leaf color, growth, stress signs, and provide "
                "a health score and recommendations."
            )
    
    # ========================================================================
    # Core Analysis Engine
    # ========================================================================
    
    def _analyze_image(
        self,
        image_data: Union[str, bytes, Image.Image],
        prompt: str,
        analysis_type: SCOLDAnalysisType,
        return_bounding_boxes: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> SCOLDAnalysisResult:
        """
        Core image analysis using SCOLD VLM
        
        Args:
            image_data: Image to analyze
            prompt: Analysis prompt for VLM
            analysis_type: Type of analysis
            return_bounding_boxes: Include bounding boxes
            context: Additional context information
            
        Returns:
            SCOLDAnalysisResult
        """
        start_time = time.time()
        
        if not self._model_loaded:
            logger.warning("SCOLD VLM not available, using fallback")
            return self._fallback_analysis(analysis_type, context)
        
        try:
            import requests
            
            # Convert image to base64
            image_b64 = self._image_to_base64(image_data)
            
            # Build request payload
            payload = {
                "image": image_b64,
                "prompt": prompt,
                "confidence_threshold": self.confidence_threshold,
                "return_bounding_boxes": return_bounding_boxes,
                "context": context or {}
            }
            
            # Call SCOLD VLM API
            response = requests.post(
                f"{self.base_url}/api/analyze",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse response into structured result
            detections = self._parse_detections(result.get("detections", []))
            
            processing_time = (time.time() - start_time) * 1000
            
            return SCOLDAnalysisResult(
                analysis_type=analysis_type,
                detections=detections,
                overall_confidence=result.get("confidence", 0.0),
                summary=result.get("summary", "No summary available"),
                recommendations=result.get("recommendations", []),
                metadata={
                    **result.get("metadata", {}),
                    'scold_model': result.get("model_version", "unknown"),
                    'context': context or {}
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"SCOLD VLM analysis failed: {e}")
            processing_time = (time.time() - start_time) * 1000
            return self._fallback_analysis(analysis_type, context, processing_time)
    
    def _parse_detections(self, raw_detections: List[Dict]) -> List[SCOLDDetection]:
        """Parse raw detections into structured format"""
        detections = []
        
        for det in raw_detections:
            detection = SCOLDDetection(
                label=det.get("label", "Unknown"),
                confidence=det.get("confidence", 0.0),
                bounding_box=det.get("bounding_box"),
                attributes=det.get("attributes", {}),
                severity=det.get("severity"),
                description=det.get("description")
            )
            
            # Only include detections above threshold
            if detection.confidence >= self.confidence_threshold:
                detections.append(detection)
        
        return detections
    
    def _fallback_analysis(
        self,
        analysis_type: SCOLDAnalysisType,
        context: Optional[Dict[str, Any]] = None,
        processing_time_ms: float = 0.0
    ) -> SCOLDAnalysisResult:
        """Fallback analysis when SCOLD unavailable"""
        return SCOLDAnalysisResult(
            analysis_type=analysis_type,
            detections=[],
            overall_confidence=0.0,
            summary="SCOLD VLM model is currently unavailable. Please ensure the model server is running.",
            recommendations=[
                "Start SCOLD VLM server: Navigate to AI_Models/scold and run the server",
                "Check SCOLD_BASE_URL environment variable",
                "Verify model files are present in AI_Models/scold directory"
            ],
            metadata={
                'error': 'SCOLD VLM unavailable',
                'context': context or {},
                'fallback': True
            },
            processing_time_ms=processing_time_ms
        )
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _image_to_base64(self, image_data: Union[str, bytes, Image.Image]) -> str:
        """Convert various image formats to base64"""
        if isinstance(image_data, str):
            # File path
            with open(image_data, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        elif isinstance(image_data, bytes):
            return base64.b64encode(image_data).decode('utf-8')
        elif isinstance(image_data, Image.Image):
            buffer = io.BytesIO()
            image_data.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        else:
            raise ValueError(f"Unsupported image type: {type(image_data)}")
    
    def is_available(self) -> bool:
        """Check if SCOLD VLM is available"""
        return self._model_loaded
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "scold_available": self._model_loaded,
            "base_url": self.base_url,
            "model_path": self.model_path,
            "confidence_threshold": self.confidence_threshold,
            "timeout": self.timeout
        }


# ============================================================================
# Global Instance & Convenience Functions
# ============================================================================

_scold_service_instance: Optional[SCOLDVLMService] = None


def get_scold_service() -> SCOLDVLMService:
    """Get or create global SCOLD VLM service instance"""
    global _scold_service_instance
    if _scold_service_instance is None:
        _scold_service_instance = SCOLDVLMService()
    return _scold_service_instance


def analyze_disease_with_scold(
    image_data: Union[str, bytes, Image.Image],
    crop_type: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for disease detection"""
    service = get_scold_service()
    result = service.detect_disease(image_data, crop_type)
    return result.to_dict()


def analyze_weeds_with_scold(
    image_data: Union[str, bytes, Image.Image],
    crop_type: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for weed identification"""
    service = get_scold_service()
    result = service.identify_weeds(image_data, crop_type)
    return result.to_dict()


def assess_health_with_scold(
    image_data: Union[str, bytes, Image.Image],
    crop_type: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for crop health assessment"""
    service = get_scold_service()
    result = service.assess_crop_health(image_data, crop_type)
    return result.to_dict()
