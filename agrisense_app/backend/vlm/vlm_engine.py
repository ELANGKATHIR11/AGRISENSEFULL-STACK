"""
Vision Language Model (VLM) Engine for AgriSense
Coordinates disease detection and weed management for Indian crops
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from .disease_detector import DiseaseDetector, DiseaseDetectionResult
from .weed_detector import WeedDetector, WeedDetectionResult
from .crop_database import (
    get_crop_info,
    list_all_crops,
    search_crops_by_category,
    INDIAN_CROPS_DB
)

logger = logging.getLogger(__name__)


@dataclass
class VLMAnalysisResult:
    """Comprehensive VLM analysis result"""
    analysis_type: str  # "disease", "weed", or "comprehensive"
    crop_name: str
    disease_analysis: Optional[Dict[str, Any]] = None
    weed_analysis: Optional[Dict[str, Any]] = None
    combined_recommendations: Optional[List[str]] = None
    priority_actions: Optional[List[str]] = None
    estimated_time_to_action: Optional[str] = None
    cost_estimate: Optional[Dict[str, Any]] = None
    success_probability: float = 0.0


class VLMEngine:
    """
    Main VLM Engine
    Provides unified interface for disease and weed detection
    """
    
    def __init__(
        self,
        disease_model_path: Optional[str] = None,
        weed_model_path: Optional[str] = None,
        use_ml: bool = True
    ):
        """
        Initialize VLM Engine
        
        Args:
            disease_model_path: Path to disease detection model
            weed_model_path: Path to weed detection model
            use_ml: Whether to use ML models (fallback to rule-based if False)
        """
        self.disease_detector = DiseaseDetector(disease_model_path, use_ml)
        self.weed_detector = WeedDetector(weed_model_path, use_ml)
        self.supported_crops = list(INDIAN_CROPS_DB.keys())
        
        logger.info(f"VLM Engine initialized with {len(self.supported_crops)} crops")
    
    def analyze_disease(
        self,
        image_path: Union[str, bytes],
        crop_name: str,
        expected_diseases: Optional[List[str]] = None,
        include_cost_estimate: bool = False
    ) -> VLMAnalysisResult:
        """
        Analyze plant image for diseases
        
        Args:
            image_path: Path to image or image bytes
            crop_name: Name of the crop
            expected_diseases: Optional list of diseases to check
            include_cost_estimate: Whether to include treatment cost estimate
        
        Returns:
            VLMAnalysisResult with disease analysis
        """
        try:
            # Perform disease detection
            disease_result = self.disease_detector.detect_disease(
                image_path,
                crop_name,
                expected_diseases
            )
            
            # Convert to dict
            disease_dict = asdict(disease_result)
            
            # Generate priority actions
            priority_actions = self._generate_disease_priority_actions(disease_result)
            
            # Estimate time to action
            time_to_action = self._estimate_disease_time_to_action(disease_result.severity.value)
            
            # Cost estimate if requested
            cost_estimate = None
            if include_cost_estimate:
                cost_estimate = self._estimate_treatment_cost(disease_result)
            
            # Success probability
            success_prob = self._calculate_disease_treatment_success(disease_result)
            
            return VLMAnalysisResult(
                analysis_type="disease",
                crop_name=crop_name,
                disease_analysis=disease_dict,
                weed_analysis=None,
                combined_recommendations=disease_result.treatment_recommendations,
                priority_actions=priority_actions,
                estimated_time_to_action=time_to_action,
                cost_estimate=cost_estimate,
                success_probability=success_prob
            )
            
        except Exception as e:
            logger.error(f"Disease analysis failed: {e}")
            raise
    
    def analyze_weeds(
        self,
        image_path: Union[str, bytes],
        crop_name: str,
        growth_stage: Optional[str] = None,
        preferred_control: Optional[str] = None,
        include_cost_estimate: bool = False
    ) -> VLMAnalysisResult:
        """
        Analyze field image for weeds
        
        Args:
            image_path: Path to image or image bytes
            crop_name: Name of the crop
            growth_stage: Current crop growth stage
            preferred_control: Preferred control method (chemical/organic/mechanical)
            include_cost_estimate: Whether to include control cost estimate
        
        Returns:
            VLMAnalysisResult with weed analysis
        """
        try:
            # Perform weed detection
            from .weed_detector import ControlMethod
            control_method = None
            if preferred_control:
                control_method = ControlMethod(preferred_control.lower())
            
            weed_result = self.weed_detector.detect_weeds(
                image_path,
                crop_name,
                growth_stage,
                control_method
            )
            
            # Convert to dict
            weed_dict = asdict(weed_result)
            
            # Generate priority actions
            priority_actions = self._generate_weed_priority_actions(weed_result)
            
            # Estimate time to action
            time_to_action = self._estimate_weed_time_to_action(weed_result.priority_level)
            
            # Get combined recommendations
            combined_recs = self._combine_weed_recommendations(weed_result)
            
            # Cost estimate if requested
            cost_estimate = None
            if include_cost_estimate:
                cost_estimate = self._estimate_weed_control_cost(weed_result)
            
            # Success probability
            success_prob = self._calculate_weed_control_success(weed_result)
            
            return VLMAnalysisResult(
                analysis_type="weed",
                crop_name=crop_name,
                disease_analysis=None,
                weed_analysis=weed_dict,
                combined_recommendations=combined_recs,
                priority_actions=priority_actions,
                estimated_time_to_action=time_to_action,
                cost_estimate=cost_estimate,
                success_probability=success_prob
            )
            
        except Exception as e:
            logger.error(f"Weed analysis failed: {e}")
            raise
    
    def analyze_comprehensive(
        self,
        plant_image_path: Union[str, bytes],
        field_image_path: Union[str, bytes],
        crop_name: str,
        growth_stage: Optional[str] = None,
        include_cost_estimate: bool = False
    ) -> VLMAnalysisResult:
        """
        Comprehensive analysis - both disease and weeds
        
        Args:
            plant_image_path: Close-up plant image for disease detection
            field_image_path: Field image for weed detection
            crop_name: Name of the crop
            growth_stage: Current crop growth stage
            include_cost_estimate: Whether to include cost estimates
        
        Returns:
            VLMAnalysisResult with both disease and weed analysis
        """
        try:
            # Disease detection
            disease_result = self.disease_detector.detect_disease(
                plant_image_path,
                crop_name
            )
            
            # Weed detection
            weed_result = self.weed_detector.detect_weeds(
                field_image_path,
                crop_name,
                growth_stage
            )
            
            # Convert to dicts
            disease_dict = asdict(disease_result)
            weed_dict = asdict(weed_result)
            
            # Combine recommendations
            combined_recs = self._merge_recommendations(disease_result, weed_result)
            
            # Combined priority actions
            priority_actions = self._merge_priority_actions(disease_result, weed_result)
            
            # Time to action (most urgent)
            disease_time = self._estimate_disease_time_to_action(disease_result.severity.value)
            weed_time = self._estimate_weed_time_to_action(weed_result.priority_level)
            time_to_action = min(disease_time, weed_time, key=lambda x: self._time_priority(x))
            
            # Combined cost estimate
            cost_estimate = None
            if include_cost_estimate:
                disease_cost = self._estimate_treatment_cost(disease_result)
                weed_cost = self._estimate_weed_control_cost(weed_result)
                cost_estimate = self._merge_cost_estimates(disease_cost, weed_cost)
            
            # Overall success probability
            disease_success = self._calculate_disease_treatment_success(disease_result)
            weed_success = self._calculate_weed_control_success(weed_result)
            overall_success = (disease_success + weed_success) / 2
            
            return VLMAnalysisResult(
                analysis_type="comprehensive",
                crop_name=crop_name,
                disease_analysis=disease_dict,
                weed_analysis=weed_dict,
                combined_recommendations=combined_recs,
                priority_actions=priority_actions,
                estimated_time_to_action=time_to_action,
                cost_estimate=cost_estimate,
                success_probability=overall_success
            )
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            raise
    
    def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed crop information"""
        crop = get_crop_info(crop_name)
        if crop:
            return {
                "name": crop.name,
                "scientific_name": crop.scientific_name,
                "category": crop.category,
                "growth_stages": crop.growth_stages,
                "optimal_conditions": crop.optimal_conditions,
                "regional_importance": crop.regional_importance,
                "common_diseases": [d.name for d in crop.common_diseases],
                "common_weeds": [w.name for w in crop.common_weeds]
            }
        return None
    
    def list_supported_crops(self, category: Optional[str] = None) -> List[str]:
        """List all supported crops, optionally filtered by category"""
        if category:
            crops = search_crops_by_category(category)
            return [crop.name for crop in crops]
        return list_all_crops()
    
    def get_disease_library(self, crop_name: str) -> List[Dict[str, Any]]:
        """Get all diseases for a crop"""
        from .crop_database import get_diseases_for_crop
        diseases = get_diseases_for_crop(crop_name)
        return [
            {
                "name": d.name,
                "scientific_name": d.scientific_name,
                "symptoms": d.symptoms,
                "causes": d.causes,
                "treatment": d.treatment,
                "prevention": d.prevention,
                "affected_parts": d.affected_parts
            }
            for d in diseases
        ]
    
    def get_weed_library(self, crop_name: str) -> List[Dict[str, Any]]:
        """Get all weeds for a crop"""
        from .crop_database import get_weeds_for_crop
        weeds = get_weeds_for_crop(crop_name)
        return [
            {
                "name": w.name,
                "scientific_name": w.scientific_name,
                "characteristics": w.characteristics,
                "control_methods": w.control_methods,
                "competition_impact": w.competition_impact,
                "growth_stage_vulnerability": w.growth_stage_vulnerability
            }
            for w in weeds
        ]
    
    def _generate_disease_priority_actions(self, result: DiseaseDetectionResult) -> List[str]:
        """Generate priority actions for disease"""
        actions = []
        
        if result.urgent_action_required:
            actions.append("🚨 URGENT: Immediate treatment required")
            actions.append("1. Isolate affected plants if possible")
            actions.append("2. Apply recommended fungicide/treatment within 24 hours")
            actions.append("3. Monitor surrounding plants daily")
        else:
            if result.severity.value in ["moderate", "severe"]:
                actions.append("⚠️ Schedule treatment within 2-3 days")
                actions.append("Monitor disease spread daily")
            else:
                actions.append("ℹ️ Monitor and apply preventive measures")
        
        # Add first treatment recommendation
        if result.treatment_recommendations:
            actions.append(f"Primary treatment: {result.treatment_recommendations[0]}")
        
        return actions
    
    def _generate_weed_priority_actions(self, result: WeedDetectionResult) -> List[str]:
        """Generate priority actions for weeds"""
        actions = []
        
        if result.priority_level == "critical":
            actions.append("🚨 CRITICAL: Immediate weed control required")
            actions.append("1. Stop weed seed production - remove flowering weeds")
            actions.append("2. Apply control measures within 24-48 hours")
        elif result.priority_level == "high":
            actions.append("⚠️ HIGH: Schedule weed control within 3-5 days")
            actions.append("Prevent further spread and seed production")
        elif result.priority_level == "medium":
            actions.append("ℹ️ MEDIUM: Plan control measures within 1-2 weeks")
        else:
            actions.append("✓ LOW: Continue monitoring, preventive measures")
        
        # Add timing recommendation
        if result.best_control_timing:
            actions.append(f"Best timing: {result.best_control_timing[0]}")
        
        return actions
    
    def _estimate_disease_time_to_action(self, severity: str) -> str:
        """Estimate time window for disease treatment"""
        time_map = {
            "critical": "Immediate (0-24 hours)",
            "severe": "Urgent (1-2 days)",
            "moderate": "Soon (3-5 days)",
            "mild": "Within week (5-7 days)",
            "healthy": "No action needed"
        }
        return time_map.get(severity, "As soon as possible")
    
    def _estimate_weed_time_to_action(self, priority: str) -> str:
        """Estimate time window for weed control"""
        time_map = {
            "critical": "Immediate (0-48 hours)",
            "high": "Urgent (3-5 days)",
            "medium": "Within 1-2 weeks",
            "low": "Within 2-4 weeks",
            "none": "No action needed"
        }
        return time_map.get(priority, "As soon as practical")
    
    def _time_priority(self, time_str: str) -> int:
        """Convert time string to priority number (lower = more urgent)"""
        if "immediate" in time_str.lower() or "0-24" in time_str:
            return 1
        elif "urgent" in time_str.lower() or "1-2" in time_str or "0-48" in time_str:
            return 2
        elif "soon" in time_str.lower() or "3-5" in time_str:
            return 3
        elif "week" in time_str.lower():
            return 4
        else:
            return 5
    
    def _merge_recommendations(
        self,
        disease_result: DiseaseDetectionResult,
        weed_result: WeedDetectionResult
    ) -> List[str]:
        """Merge disease and weed recommendations"""
        combined = []
        
        # Disease recommendations first if urgent
        if disease_result.urgent_action_required:
            combined.append("=== DISEASE TREATMENT (URGENT) ===")
            combined.extend(disease_result.treatment_recommendations[:3])
        
        # Weed recommendations
        if weed_result.priority_level in ["critical", "high"]:
            combined.append("=== WEED CONTROL (HIGH PRIORITY) ===")
            # Get integrated recommendations
            integrated = weed_result.control_recommendations.get("integrated", [])
            combined.extend(integrated[:3])
        
        # Add remaining disease recommendations
        if not disease_result.urgent_action_required and disease_result.disease_name != "Unknown/Healthy":
            combined.append("=== DISEASE TREATMENT ===")
            combined.extend(disease_result.treatment_recommendations[:2])
        
        # Add remaining weed recommendations
        if weed_result.priority_level not in ["critical", "high", "none"]:
            combined.append("=== WEED CONTROL ===")
            integrated = weed_result.control_recommendations.get("integrated", [])
            combined.extend(integrated[:2])
        
        return combined
    
    def _merge_priority_actions(
        self,
        disease_result: DiseaseDetectionResult,
        weed_result: WeedDetectionResult
    ) -> List[str]:
        """Merge priority actions from both analyses"""
        disease_actions = self._generate_disease_priority_actions(disease_result)
        weed_actions = self._generate_weed_priority_actions(weed_result)
        
        # Interleave based on urgency
        all_actions = []
        
        if disease_result.urgent_action_required:
            all_actions.extend(disease_actions[:3])
        
        if weed_result.priority_level == "critical":
            all_actions.extend(weed_actions[:3])
        
        # Add remaining
        all_actions.extend(disease_actions[3:])
        all_actions.extend(weed_actions[3:])
        
        return all_actions[:10]  # Limit to top 10
    
    def _estimate_treatment_cost(self, result: DiseaseDetectionResult) -> Dict[str, float]:
        """Estimate disease treatment cost (INR per acre)"""
        base_costs = {
            "fungicide": 800.0,
            "application": 200.0,
            "labor": 300.0
        }
        
        # Severity multiplier
        multipliers = {
            "mild": 0.5,
            "moderate": 1.0,
            "severe": 1.5,
            "critical": 2.0
        }
        
        multiplier = multipliers.get(result.severity.value, 1.0)
        
        return {
            "fungicide_cost": base_costs["fungicide"] * multiplier,
            "application_cost": base_costs["application"],
            "labor_cost": base_costs["labor"],
            "total_per_acre": sum(base_costs.values()) * multiplier,
            "currency": "INR"
        }
    
    def _estimate_weed_control_cost(self, result: WeedDetectionResult) -> Dict[str, float]:
        """Estimate weed control cost (INR per acre)"""
        # Base costs for different methods
        method_costs = {
            "chemical": 600.0,
            "mechanical": 800.0,
            "organic": 400.0,
            "manual": 1200.0
        }
        
        # Coverage multiplier
        coverage_multiplier = min(result.weed_coverage_percentage / 30.0, 2.0)
        
        # Use most recommended method
        primary_method = "chemical"  # Default
        if result.control_recommendations.get("organic"):
            primary_method = "organic"
        
        base_cost = method_costs[primary_method]
        
        return {
            "control_method_cost": base_cost * coverage_multiplier,
            "application_cost": 150.0,
            "labor_cost": 250.0 * coverage_multiplier,
            "total_per_acre": (base_cost + 150 + 250) * coverage_multiplier,
            "currency": "INR"
        }
    
    def _merge_cost_estimates(
        self,
        disease_cost: Optional[Dict[str, float]],
        weed_cost: Optional[Dict[str, float]]
    ) -> Dict[str, float]:
        """Merge cost estimates"""
        combined = {
            "disease_treatment": disease_cost.get("total_per_acre", 0) if disease_cost else 0,
            "weed_control": weed_cost.get("total_per_acre", 0) if weed_cost else 0,
            "total_per_acre": 0,
            "currency": "INR"
        }
        combined["total_per_acre"] = combined["disease_treatment"] + combined["weed_control"]
        return combined
    
    def _calculate_disease_treatment_success(self, result: DiseaseDetectionResult) -> float:
        """Calculate probability of successful disease treatment"""
        base_success = 0.85
        
        # Reduce based on severity
        severity_penalty = {
            "mild": 0.0,
            "moderate": 0.1,
            "severe": 0.2,
            "critical": 0.3
        }
        
        penalty = severity_penalty.get(result.severity.value, 0.1)
        
        # Increase based on confidence
        confidence_bonus = result.confidence * 0.1
        
        return min(base_success - penalty + confidence_bonus, 0.95)
    
    def _calculate_weed_control_success(self, result: WeedDetectionResult) -> float:
        """Calculate probability of successful weed control"""
        base_success = 0.90
        
        # Reduce based on infestation
        infestation_penalty = {
            "none": 0.0,
            "low": 0.05,
            "moderate": 0.15,
            "high": 0.25,
            "severe": 0.35
        }
        
        penalty = infestation_penalty.get(result.infestation_level.value, 0.1)
        
        return max(base_success - penalty, 0.50)
    
    def _combine_weed_recommendations(self, result: WeedDetectionResult) -> List[str]:
        """Combine weed recommendations from all methods"""
        combined = []
        
        # Add integrated first
        if result.control_recommendations.get("integrated"):
            combined.extend(result.control_recommendations["integrated"])
        
        # Add from preferred method
        for method in ["organic", "chemical", "mechanical"]:
            if result.control_recommendations.get(method):
                combined.extend(result.control_recommendations[method][:2])
        
        return list(set(combined))  # Remove duplicates
    
    def export_results(self, result: VLMAnalysisResult, output_path: str):
        """Export analysis results to JSON file"""
        try:
            result_dict = asdict(result)
            with open(output_path, 'w') as f:
                json.dump(result_dict, f, indent=2)
            logger.info(f"Results exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise
