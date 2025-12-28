"""
Disease Detection Engine using Computer Vision
Analyzes plant images to identify diseases and provides treatment recommendations
"""

import os
import io
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import cv2
    import numpy as np
    from PIL import Image
    import torch
    import torchvision.transforms as transforms
    from torchvision import models
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    logging.warning("CV dependencies not available. Disease detection will use rule-based analysis.")

from .crop_database import get_crop_info, get_diseases_for_crop, Disease

logger = logging.getLogger(__name__)


class DiseaseSeverity(str, Enum):
    """Disease severity levels"""
    HEALTHY = "healthy"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class DiseaseDetectionResult:
    """Result of disease detection"""
    crop_name: str
    disease_name: Optional[str]
    confidence: float
    severity: DiseaseSeverity
    affected_area_percentage: float
    symptoms_detected: List[str]
    treatment_recommendations: List[str]
    prevention_tips: List[str]
    image_analysis: Dict[str, Any]
    urgent_action_required: bool


class DiseaseDetector:
    """
    Disease Detection Engine
    Uses computer vision and rule-based analysis to identify plant diseases
    """
    
    def __init__(self, model_path: Optional[str] = None, use_ml: bool = True):
        """
        Initialize disease detector
        
        Args:
            model_path: Path to trained disease detection model
            use_ml: Whether to use ML models (if available)
        """
        self.use_ml = use_ml and CV_AVAILABLE
        self.model = None
        self.device = None
        
        if self.use_ml:
            self._initialize_model(model_path)
        
        # Color ranges for disease symptom detection (HSV)
        self.symptom_colors = {
            "yellow_spots": {"lower": np.array([20, 40, 40]), "upper": np.array([40, 255, 255])},
            "brown_spots": {"lower": np.array([10, 30, 20]), "upper": np.array([25, 200, 100])},
            "white_patches": {"lower": np.array([0, 0, 180]), "upper": np.array([180, 30, 255])},
            "black_spots": {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 50])},
            "rust_colored": {"lower": np.array([0, 100, 100]), "upper": np.array([15, 255, 255])},
        }
    
    def _initialize_model(self, model_path: Optional[str]):
        """Initialize ML model for disease detection"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            if model_path and os.path.exists(model_path):
                # Load custom trained model
                self.model = torch.load(model_path, map_location=self.device)
            else:
                # Use pre-trained ResNet50 as feature extractor
                self.model = models.resnet50(pretrained=True)
                self.model.eval()
            
            self.model.to(self.device)
            logger.info(f"Disease detection model initialized on {self.device}")
            
            # Define image transforms
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            self.use_ml = False
    
    def detect_disease(
        self,
        image_path: str,
        crop_name: str,
        expected_diseases: Optional[List[str]] = None
    ) -> DiseaseDetectionResult:
        """
        Detect disease from plant image
        
        Args:
            image_path: Path to plant image or image bytes
            crop_name: Name of the crop
            expected_diseases: List of diseases to check for (optional)
        
        Returns:
            DiseaseDetectionResult with detection details
        """
        try:
            # Load image
            if isinstance(image_path, (bytes, io.BytesIO)):
                image = Image.open(io.BytesIO(image_path) if isinstance(image_path, bytes) else image_path)
            else:
                image = Image.open(image_path)
            
            # Convert to RGB
            image_rgb = image.convert("RGB")
            image_cv = cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
            
            # Perform image analysis
            image_analysis = self._analyze_image(image_cv)
            
            # Get crop information
            crop_info = get_crop_info(crop_name)
            if not crop_info:
                raise ValueError(f"Crop '{crop_name}' not found in database")
            
            # Detect symptoms
            symptoms_detected, severity, affected_percentage = self._detect_symptoms(
                image_cv, image_analysis
            )
            
            # Match disease based on symptoms
            disease_match, confidence = self._match_disease(
                crop_info,
                symptoms_detected,
                severity,
                expected_diseases
            )
            
            # Generate recommendations
            treatment_recs = []
            prevention_tips = []
            urgent = False
            
            if disease_match:
                treatment_recs = disease_match.treatment
                prevention_tips = disease_match.prevention
                urgent = severity in [DiseaseSeverity.SEVERE, DiseaseSeverity.CRITICAL]
            else:
                # Provide general recommendations
                treatment_recs = [
                    "Remove affected plant parts",
                    "Improve air circulation",
                    "Avoid overhead watering",
                    "Apply balanced fertilizer",
                    "Consult local agricultural extension"
                ]
                prevention_tips = [
                    "Use disease-free seeds",
                    "Practice crop rotation",
                    "Maintain field sanitation",
                    "Monitor plants regularly"
                ]
            
            return DiseaseDetectionResult(
                crop_name=crop_name,
                disease_name=disease_match.name if disease_match else "Unknown/Healthy",
                confidence=confidence,
                severity=severity,
                affected_area_percentage=affected_percentage,
                symptoms_detected=symptoms_detected,
                treatment_recommendations=treatment_recs,
                prevention_tips=prevention_tips,
                image_analysis=image_analysis,
                urgent_action_required=urgent
            )
            
        except Exception as e:
            logger.error(f"Disease detection failed: {e}")
            raise
    
    def _analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze image characteristics
        
        Args:
            image: OpenCV image (BGR format)
        
        Returns:
            Dictionary with image analysis metrics
        """
        analysis = {}
        
        try:
            # Calculate basic metrics
            height, width = image.shape[:2]
            analysis["resolution"] = {"width": width, "height": height}
            
            # Color analysis
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            analysis["mean_hue"] = float(np.mean(hsv_image[:, :, 0]))
            analysis["mean_saturation"] = float(np.mean(hsv_image[:, :, 1]))
            analysis["mean_value"] = float(np.mean(hsv_image[:, :, 2]))
            
            # Green vegetation index (healthy plant indicator)
            green_ratio = self._calculate_green_ratio(image)
            analysis["green_ratio"] = float(green_ratio)
            analysis["vegetation_health"] = "good" if green_ratio > 0.3 else "poor"
            
            # Texture analysis (disease indicator)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            analysis["texture_variance"] = float(laplacian_var)
            analysis["texture_quality"] = "uniform" if laplacian_var < 100 else "varied"
            
            # Spot detection
            spots_detected = self._detect_spots(image)
            analysis["spots_count"] = len(spots_detected)
            analysis["spots_locations"] = spots_detected
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _calculate_green_ratio(self, image: np.ndarray) -> float:
        """Calculate ratio of green pixels (healthy vegetation indicator)"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define green color range
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        # Create mask
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Calculate ratio
        green_pixels = np.sum(green_mask > 0)
        total_pixels = image.shape[0] * image.shape[1]
        
        return green_pixels / total_pixels if total_pixels > 0 else 0.0
    
    def _detect_spots(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect disease spots/lesions in image"""
        spots = []
        
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect spots of different colors
            for spot_type, color_range in self.symptom_colors.items():
                mask = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 50:  # Minimum spot size
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            
                            spots.append({
                                "type": spot_type,
                                "area": float(area),
                                "center": {"x": cx, "y": cy},
                                "severity": "high" if area > 500 else "medium" if area > 200 else "low"
                            })
        
        except Exception as e:
            logger.error(f"Spot detection failed: {e}")
        
        return spots
    
    def _detect_symptoms(
        self,
        image: np.ndarray,
        image_analysis: Dict[str, Any]
    ) -> Tuple[List[str], DiseaseSeverity, float]:
        """
        Detect disease symptoms from image analysis
        
        Returns:
            (symptoms_list, severity, affected_percentage)
        """
        symptoms = []
        
        # Analyze spots
        spots = image_analysis.get("spots_locations", [])
        total_spot_area = sum(spot["area"] for spot in spots)
        image_area = image_analysis["resolution"]["width"] * image_analysis["resolution"]["height"]
        affected_percentage = (total_spot_area / image_area * 100) if image_area > 0 else 0
        
        # Detect specific symptoms based on spots
        spot_types = set(spot["type"] for spot in spots)
        
        if "yellow_spots" in spot_types:
            symptoms.append("Yellowing of leaves")
        if "brown_spots" in spot_types:
            symptoms.append("Brown spots or lesions")
        if "white_patches" in spot_types:
            symptoms.append("White powdery patches")
        if "black_spots" in spot_types:
            symptoms.append("Black spots or necrosis")
        if "rust_colored" in spot_types:
            symptoms.append("Rust-colored pustules")
        
        # Check vegetation health
        if image_analysis.get("green_ratio", 1.0) < 0.2:
            symptoms.append("Severe chlorosis or wilting")
        elif image_analysis.get("green_ratio", 1.0) < 0.3:
            symptoms.append("Leaf discoloration")
        
        # Check texture (disease often causes texture changes)
        if image_analysis.get("texture_variance", 0) > 200:
            symptoms.append("Irregular leaf texture")
        
        # Determine severity
        if affected_percentage > 50 or len(symptoms) >= 4:
            severity = DiseaseSeverity.CRITICAL
        elif affected_percentage > 30 or len(symptoms) >= 3:
            severity = DiseaseSeverity.SEVERE
        elif affected_percentage > 15 or len(symptoms) >= 2:
            severity = DiseaseSeverity.MODERATE
        elif affected_percentage > 5 or len(symptoms) >= 1:
            severity = DiseaseSeverity.MILD
        else:
            severity = DiseaseSeverity.HEALTHY
        
        return symptoms, severity, affected_percentage
    
    def _match_disease(
        self,
        crop_info,
        symptoms_detected: List[str],
        severity: DiseaseSeverity,
        expected_diseases: Optional[List[str]] = None
    ) -> Tuple[Optional[Disease], float]:
        """
        Match detected symptoms to known diseases
        
        Returns:
            (matched_disease, confidence_score)
        """
        if severity == DiseaseSeverity.HEALTHY:
            return None, 1.0
        
        diseases = crop_info.common_diseases
        if expected_diseases:
            diseases = [d for d in diseases if d.name in expected_diseases]
        
        best_match = None
        best_score = 0.0
        
        for disease in diseases:
            # Calculate symptom match score
            disease_symptoms = set(s.lower() for s in disease.symptoms)
            detected_symptoms = set(s.lower() for s in symptoms_detected)
            
            # Count matching keywords
            matches = 0
            for detected in detected_symptoms:
                for disease_symptom in disease_symptoms:
                    if any(word in disease_symptom for word in detected.split()):
                        matches += 1
                        break
            
            # Calculate score (0-1)
            if len(disease_symptoms) > 0:
                score = matches / max(len(disease_symptoms), len(detected_symptoms))
            else:
                score = 0.0
            
            if score > best_score:
                best_score = score
                best_match = disease
        
        # Confidence threshold
        confidence = min(best_score * 0.9, 0.95)  # Cap at 95%
        
        return best_match, confidence
    
    def batch_detect(
        self,
        image_paths: List[str],
        crop_name: str
    ) -> List[DiseaseDetectionResult]:
        """
        Detect diseases in multiple images
        
        Args:
            image_paths: List of image paths
            crop_name: Name of the crop
        
        Returns:
            List of detection results
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.detect_disease(image_path, crop_name)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                continue
        
        return results
    
    def get_disease_summary(
        self,
        results: List[DiseaseDetectionResult]
    ) -> Dict[str, Any]:
        """
        Generate summary from multiple detection results
        
        Args:
            results: List of detection results
        
        Returns:
            Summary statistics
        """
        if not results:
            return {}
        
        diseases_found = {}
        total_confidence = 0.0
        urgent_count = 0
        
        for result in results:
            if result.disease_name and result.disease_name != "Unknown/Healthy":
                diseases_found[result.disease_name] = diseases_found.get(result.disease_name, 0) + 1
            total_confidence += result.confidence
            if result.urgent_action_required:
                urgent_count += 1
        
        return {
            "total_images": len(results),
            "unique_diseases": len(diseases_found),
            "diseases_distribution": diseases_found,
            "average_confidence": total_confidence / len(results),
            "urgent_cases": urgent_count,
            "requires_immediate_action": urgent_count > 0
        }
