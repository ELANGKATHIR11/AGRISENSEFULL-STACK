#!/usr/bin/env python3
"""
Enhanced Weed Detection Implementation
Provides better crop vs weed classification using image analysis
"""

import base64
import io
import numpy as np
from PIL import Image, ImageStat
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartWeedDetector:
    """Smart weed detector that can distinguish between crops and weeds"""
    
    def __init__(self):
        """Initialize the smart weed detector"""
        self.crop_characteristics = {
            'organization_score_threshold': 0.3,  # Crops tend to be more organized
            'green_intensity_threshold': 0.6,     # Healthy crops are more green
            'pattern_regularity_threshold': 0.4,  # Crops show more regular patterns
        }
        
        self.weed_characteristics = {
            'color_diversity_threshold': 0.5,     # Weeds show more color variation
            'randomness_threshold': 0.6,          # Weeds are more random
            'yellow_brown_ratio_threshold': 0.3,  # Weeds often have yellow/brown
        }
    
    def analyze_image(self, image_data: str, crop_type: str = "unknown") -> Dict[str, Any]:
        """
        Analyze image to detect if it contains crops or weeds
        
        Args:
            image_data: Base64 encoded image data
            crop_type: Type of crop being analyzed
            
        Returns:
            Analysis results with crop vs weed classification
        """
        try:
            # Decode image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_array = np.array(image)
            
            # Perform analysis
            analysis_result = self._perform_comprehensive_analysis(image_array, image)
            
            # Classify as crop or weed field
            classification = self._classify_crop_vs_weed(analysis_result)
            
            # Generate appropriate response
            return self._generate_response(classification, analysis_result, crop_type)
            
        except Exception as e:
            logger.error(f"Smart weed analysis failed: {e}")
            return self._generate_error_response(str(e))
    
    def _perform_comprehensive_analysis(self, image_array: np.ndarray, image: Image.Image) -> Dict[str, Any]:
        """Perform comprehensive image analysis"""
        
        # Color analysis
        color_stats = self._analyze_colors(image_array)
        
        # Pattern analysis
        pattern_stats = self._analyze_patterns(image_array)
        
        # Organization analysis
        organization_stats = self._analyze_organization(image_array)
        
        # Green health analysis
        green_health = self._analyze_green_health(image_array)
        
        return {
            'color_stats': color_stats,
            'pattern_stats': pattern_stats,
            'organization_stats': organization_stats,
            'green_health': green_health,
            'image_size': image_array.shape
        }
    
    def _analyze_colors(self, image_array: np.ndarray) -> Dict[str, float]:
        """Analyze color distribution in the image"""
        # Convert to different color spaces for analysis
        r, g, b = image_array[:,:,0], image_array[:,:,1], image_array[:,:,2]
        
        # Calculate color statistics
        green_dominance = np.mean(g) / (np.mean(r) + np.mean(g) + np.mean(b) + 1e-6)
        
        # Calculate color diversity (higher = more varied colors like weeds)
        color_std = np.std([np.std(r), np.std(g), np.std(b)])
        color_diversity = color_std / 255.0
        
        # Yellow/brown detection (common in weeds)
        yellow_mask = (r > 150) & (g > 150) & (b < 100)
        brown_mask = (r > 100) & (r < 200) & (g > 50) & (g < 150) & (b < 100)
        yellow_brown_ratio = (np.sum(yellow_mask) + np.sum(brown_mask)) / image_array.size
        
        return {
            'green_dominance': float(green_dominance),
            'color_diversity': float(color_diversity),
            'yellow_brown_ratio': float(yellow_brown_ratio)
        }
    
    def _analyze_patterns(self, image_array: np.ndarray) -> Dict[str, float]:
        """Analyze spatial patterns in the image"""
        # Convert to grayscale for pattern analysis
        gray = np.mean(image_array, axis=2)
        
        # Calculate edge density (crops often have more regular edges)
        edges = np.abs(np.gradient(gray, axis=0)) + np.abs(np.gradient(gray, axis=1))
        edge_regularity = 1.0 - (np.std(edges) / (np.mean(edges) + 1e-6))
        
        # Calculate spatial frequency (crops often show periodic patterns)
        fft = np.fft.fft2(gray)
        fft_magnitude = np.abs(fft)
        low_freq_energy = np.sum(fft_magnitude[:gray.shape[0]//4, :gray.shape[1]//4])
        total_energy = np.sum(fft_magnitude)
        pattern_regularity = low_freq_energy / (total_energy + 1e-6)
        
        return {
            'edge_regularity': float(edge_regularity),
            'pattern_regularity': float(pattern_regularity)
        }
    
    def _analyze_organization(self, image_array: np.ndarray) -> Dict[str, float]:
        """Analyze spatial organization (crops vs random weed growth)"""
        # Convert to grayscale
        gray = np.mean(image_array, axis=2)
        
        # Analyze row-like patterns (crops often grow in rows)
        horizontal_variance = np.var(np.mean(gray, axis=1))
        vertical_variance = np.var(np.mean(gray, axis=0))
        
        # Higher variance indicates more organized structure
        organization_score = (horizontal_variance + vertical_variance) / (2 * 255**2)
        
        # Calculate uniformity (crops tend to be more uniform)
        local_std = np.std(gray)
        global_mean = np.mean(gray)
        uniformity = 1.0 - (local_std / (global_mean + 1e-6))
        
        return {
            'organization_score': float(organization_score),
            'uniformity': float(uniformity)
        }
    
    def _analyze_green_health(self, image_array: np.ndarray) -> Dict[str, float]:
        """Analyze green health indicators"""
        r, g, b = image_array[:,:,0], image_array[:,:,1], image_array[:,:,2]
        
        # Calculate green intensity
        green_intensity = np.mean(g) / 255.0
        
        # Calculate vegetation index (NDVI-like)
        green_red_ratio = np.mean(g) / (np.mean(r) + 1e-6)
        
        # Health uniformity (healthy crops more uniform)
        green_uniformity = 1.0 - (np.std(g) / (np.mean(g) + 1e-6))
        
        return {
            'green_intensity': float(green_intensity),
            'green_red_ratio': float(green_red_ratio),
            'green_uniformity': float(green_uniformity)
        }
    
    def _classify_crop_vs_weed(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Classify whether the image shows crops or weeds"""
        
        # Extract analysis metrics
        color_stats = analysis_result['color_stats']
        pattern_stats = analysis_result['pattern_stats'] 
        org_stats = analysis_result['organization_stats']
        green_health = analysis_result['green_health']
        
        # Scoring system
        crop_score = 0.0
        weed_score = 0.0
        
        # Color-based scoring
        if color_stats['green_dominance'] > self.crop_characteristics['green_intensity_threshold']:
            crop_score += 2.0
        else:
            weed_score += 1.0
            
        if color_stats['color_diversity'] > self.weed_characteristics['color_diversity_threshold']:
            weed_score += 2.0
        else:
            crop_score += 1.0
            
        if color_stats['yellow_brown_ratio'] > self.weed_characteristics['yellow_brown_ratio_threshold']:
            weed_score += 2.0
        else:
            crop_score += 1.0
        
        # Pattern-based scoring
        if pattern_stats['pattern_regularity'] > self.crop_characteristics['pattern_regularity_threshold']:
            crop_score += 2.0
        else:
            weed_score += 1.0
        
        # Organization-based scoring
        if org_stats['organization_score'] > self.crop_characteristics['organization_score_threshold']:
            crop_score += 2.0
        else:
            weed_score += 1.0
            
        if org_stats['uniformity'] > 0.5:
            crop_score += 1.0
        else:
            weed_score += 1.0
        
        # Green health scoring
        if green_health['green_intensity'] > self.crop_characteristics['green_intensity_threshold']:
            crop_score += 1.5
        else:
            weed_score += 1.0
            
        if green_health['green_uniformity'] > 0.6:
            crop_score += 1.0
        else:
            weed_score += 1.0
        
        # Final classification
        total_score = crop_score + weed_score
        crop_confidence = crop_score / total_score if total_score > 0 else 0.5
        weed_confidence = weed_score / total_score if total_score > 0 else 0.5
        
        classification = "crop_field" if crop_score > weed_score else "weedy_field"
        confidence = max(crop_confidence, weed_confidence)
        
        return {
            'classification': classification,
            'confidence': float(confidence),
            'crop_score': float(crop_score),
            'weed_score': float(weed_score),
            'crop_confidence': float(crop_confidence),
            'weed_confidence': float(weed_confidence)
        }
    
    def _generate_response(self, classification: Dict[str, Any], analysis_result: Dict[str, Any], crop_type: str) -> Dict[str, Any]:
        """Generate appropriate response based on classification"""
        
        timestamp = datetime.now().isoformat()
        
        base_response = {
            "timestamp": timestamp,
            "crop_type": crop_type,
            "detection_confidence": classification['confidence'],
            "model_used": "smart_image_analysis",
            "classification_result": classification['classification']
        }
        
        if classification['classification'] == "crop_field":
            # This looks like a healthy crop field
            base_response.update({
                "analysis_summary": {
                    "field_type": "Crop Field Detected",
                    "weed_presence": "Minimal to None",
                    "crop_health": "Good" if analysis_result['green_health']['green_intensity'] > 0.6 else "Moderate",
                    "organization": "Well Organized" if analysis_result['organization_stats']['organization_score'] > 0.3 else "Moderate",
                    "assessment": "This appears to be a well-maintained crop field with minimal weed pressure"
                },
                "management_recommendations": {
                    "immediate_actions": [
                        "Continue current maintenance practices",
                        "Monitor for early weed emergence", 
                        "Maintain field organization"
                    ],
                    "treatment_priority": "Low",
                    "preventive_measures": [
                        "Regular field monitoring",
                        "Maintain crop density",
                        "Consider preventive herbicide if needed"
                    ]
                }
            })
        else:
            # This looks like a weedy field
            weed_severity = "High" if classification['weed_confidence'] > 0.7 else "Moderate"
            
            base_response.update({
                "analysis_summary": {
                    "field_type": "Weedy Field Detected", 
                    "weed_presence": f"{weed_severity} Weed Pressure",
                    "weed_diversity": "High" if analysis_result['color_stats']['color_diversity'] > 0.5 else "Moderate",
                    "pattern": "Random/Chaotic Growth Pattern",
                    "assessment": f"This field shows {weed_severity.lower()} weed infestation requiring management attention"
                },
                "management_recommendations": {
                    "immediate_actions": [
                        "Implement weed control strategy",
                        "Consider selective herbicide application",
                        "Assess economic threshold for treatment"
                    ],
                    "treatment_priority": weed_severity,
                    "herbicide_options": [
                        "Post-emergent selective herbicide",
                        "Spot treatment for heavy areas",
                        "Consider cultural control methods"
                    ],
                    "timing": "Immediate action recommended" if weed_severity == "High" else "Plan treatment within 1-2 weeks"
                }
            })
        
        return base_response
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": error_message,
            "analysis_summary": {"status": "Analysis failed"},
            "management_recommendations": {
                "immediate_actions": ["Please try uploading the image again"]
            }
        }

# Global instance
smart_detector = SmartWeedDetector()