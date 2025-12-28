"""
Weed Detection and Management Engine
Identifies weeds and provides control recommendations
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import cv2
    import numpy as np
    from PIL import Image
    import torch
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    logging.warning("CV dependencies not available. Weed detection will use rule-based analysis.")

from .crop_database import get_crop_info, get_weeds_for_crop, Weed

logger = logging.getLogger(__name__)


class WeedInfestationLevel(str, Enum):
    """Weed infestation severity"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class ControlMethod(str, Enum):
    """Weed control methods"""
    CHEMICAL = "chemical"
    ORGANIC = "organic"
    MECHANICAL = "mechanical"
    INTEGRATED = "integrated"


@dataclass
class WeedDetectionResult:
    """Result of weed detection"""
    crop_name: str
    weeds_identified: List[str]
    infestation_level: WeedInfestationLevel
    weed_coverage_percentage: float
    control_recommendations: Dict[str, List[str]]  # method -> recommendations
    priority_level: str  # low, medium, high, critical
    estimated_yield_impact: str
    best_control_timing: List[str]
    image_analysis: Dict[str, Any]
    multiple_weeds_detected: bool


class WeedDetector:
    """
    Weed Detection and Management Engine
    Uses computer vision to identify weeds and provides control strategies
    """
    
    def __init__(self, model_path: Optional[str] = None, use_ml: bool = True):
        """
        Initialize weed detector
        
        Args:
            model_path: Path to trained weed detection model
            use_ml: Whether to use ML models (if available)
        """
        self.use_ml = use_ml and CV_AVAILABLE
        self.model = None
        
        if self.use_ml and model_path:
            self._initialize_model(model_path)
        
        # Weed vs crop discrimination features
        self.weed_features = {
            "leaf_shape": ["broad", "narrow", "oval", "serrated", "lobed"],
            "growth_pattern": ["prostrate", "erect", "climbing", "spreading"],
            "leaf_color": ["dark_green", "light_green", "purple_tinted", "gray_green"],
        }
    
    def _initialize_model(self, model_path: str):
        """Initialize ML model for weed detection"""
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = torch.load(model_path, map_location=self.device)
            self.model.eval()
            self.model.to(self.device)
            logger.info(f"Weed detection model initialized on {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            self.use_ml = False
    
    def detect_weeds(
        self,
        image_path: str,
        crop_name: str,
        growth_stage: Optional[str] = None,
        preferred_control: Optional[ControlMethod] = None
    ) -> WeedDetectionResult:
        """
        Detect weeds from field image
        
        Args:
            image_path: Path to field image
            crop_name: Name of the crop
            growth_stage: Current crop growth stage
            preferred_control: Preferred control method (chemical/organic/mechanical)
        
        Returns:
            WeedDetectionResult with detection details and recommendations
        """
        try:
            # Load image
            if isinstance(image_path, (bytes)):
                import io
                image = Image.open(io.BytesIO(image_path))
            else:
                image = Image.open(image_path)
            
            image_rgb = image.convert("RGB")
            image_cv = cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
            
            # Analyze image
            image_analysis = self._analyze_field_image(image_cv)
            
            # Get crop information
            crop_info = get_crop_info(crop_name)
            if not crop_info:
                raise ValueError(f"Crop '{crop_name}' not found in database")
            
            # Detect weed presence
            weed_coverage = image_analysis.get("weed_coverage_percentage", 0.0)
            infestation_level = self._classify_infestation(weed_coverage)
            
            # Identify specific weeds
            weeds_identified = self._identify_weeds(
                crop_info,
                image_analysis,
                growth_stage
            )
            
            # Generate control recommendations
            control_recs = self._generate_recommendations(
                crop_info,
                weeds_identified,
                infestation_level,
                growth_stage,
                preferred_control
            )
            
            # Assess priority
            priority = self._assess_priority(infestation_level, growth_stage)
            
            # Estimate yield impact
            yield_impact = self._estimate_yield_impact(infestation_level, weeds_identified)
            
            # Determine best control timing
            timing = self._get_control_timing(growth_stage, weeds_identified)
            
            return WeedDetectionResult(
                crop_name=crop_name,
                weeds_identified=[w.name for w in weeds_identified],
                infestation_level=infestation_level,
                weed_coverage_percentage=weed_coverage,
                control_recommendations=control_recs,
                priority_level=priority,
                estimated_yield_impact=yield_impact,
                best_control_timing=timing,
                image_analysis=image_analysis,
                multiple_weeds_detected=len(weeds_identified) > 1
            )
            
        except Exception as e:
            logger.error(f"Weed detection failed: {e}")
            raise
    
    def _analyze_field_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze field image for weed presence
        
        Args:
            image: OpenCV image (BGR format)
        
        Returns:
            Image analysis metrics
        """
        analysis = {}
        
        try:
            height, width = image.shape[:2]
            analysis["resolution"] = {"width": width, "height": height}
            
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Segment vegetation
            vegetation_mask = self._segment_vegetation(hsv)
            vegetation_pixels = np.sum(vegetation_mask > 0)
            total_pixels = height * width
            
            analysis["vegetation_coverage"] = float(vegetation_pixels / total_pixels)
            
            # Detect non-uniform growth patterns (weed indicator)
            uniformity_score = self._calculate_uniformity(image)
            analysis["uniformity_score"] = float(uniformity_score)
            
            # Estimate weed coverage (non-uniform vegetation)
            if uniformity_score < 0.7:  # Low uniformity suggests weeds
                weed_estimate = analysis["vegetation_coverage"] * (1 - uniformity_score)
            else:
                weed_estimate = 0.0
            
            analysis["weed_coverage_percentage"] = float(weed_estimate * 100)
            
            # Detect different plant types by color/texture
            plant_clusters = self._detect_plant_clusters(image)
            analysis["distinct_plant_types"] = len(plant_clusters)
            analysis["plant_clusters"] = plant_clusters
            
            # Spatial distribution analysis
            distribution = self._analyze_spatial_distribution(vegetation_mask)
            analysis["weed_distribution"] = distribution
            
        except Exception as e:
            logger.error(f"Field image analysis failed: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _segment_vegetation(self, hsv_image: np.ndarray) -> np.ndarray:
        """Segment vegetation from background"""
        # Green vegetation range (both light and dark green)
        lower_green1 = np.array([25, 30, 30])
        upper_green1 = np.array([90, 255, 255])
        
        mask = cv2.inRange(hsv_image, lower_green1, upper_green1)
        
        # Morphological operations to clean mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask
    
    def _calculate_uniformity(self, image: np.ndarray) -> float:
        """Calculate uniformity of vegetation (uniform crop vs mixed weeds)"""
        try:
            # Convert to LAB color space for better color analysis
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Calculate color variance
            l_std = np.std(lab[:, :, 0])
            a_std = np.std(lab[:, :, 1])
            b_std = np.std(lab[:, :, 2])
            
            # Combined variance (higher = less uniform)
            total_variance = (l_std + a_std + b_std) / 3
            
            # Normalize to 0-1 score (lower variance = more uniform)
            uniformity = max(0, 1 - (total_variance / 50))
            
            return uniformity
        except:
            return 0.5  # Default moderate uniformity
    
    def _detect_plant_clusters(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect distinct plant type clusters"""
        clusters = []
        
        try:
            # Use K-means clustering on vegetation pixels
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            vegetation_mask = self._segment_vegetation(hsv)
            
            # Extract vegetation pixels
            vegetation_pixels = image[vegetation_mask > 0]
            
            if len(vegetation_pixels) > 100:
                from sklearn.cluster import KMeans
                
                # Cluster by color
                n_clusters = min(5, len(vegetation_pixels) // 100)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                labels = kmeans.fit_predict(vegetation_pixels)
                
                # Analyze each cluster
                for i in range(n_clusters):
                    cluster_size = np.sum(labels == i)
                    cluster_color = kmeans.cluster_centers_[i]
                    
                    clusters.append({
                        "cluster_id": int(i),
                        "size": int(cluster_size),
                        "percentage": float(cluster_size / len(vegetation_pixels) * 100),
                        "avg_color_bgr": cluster_color.tolist()
                    })
        except ImportError:
            # sklearn not available, use simple method
            logger.warning("sklearn not available for clustering")
        except Exception as e:
            logger.error(f"Plant clustering failed: {e}")
        
        return clusters
    
    def _analyze_spatial_distribution(self, vegetation_mask: np.ndarray) -> str:
        """Analyze spatial distribution of vegetation"""
        try:
            # Divide image into grid
            h, w = vegetation_mask.shape
            grid_size = 4
            cell_h, cell_w = h // grid_size, w // grid_size
            
            cell_coverages = []
            for i in range(grid_size):
                for j in range(grid_size):
                    cell = vegetation_mask[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    coverage = np.sum(cell > 0) / (cell_h * cell_w)
                    cell_coverages.append(coverage)
            
            # Calculate variance
            variance = np.var(cell_coverages)
            
            if variance < 0.01:
                return "uniform"
            elif variance < 0.05:
                return "mostly_uniform"
            elif variance < 0.1:
                return "patchy"
            else:
                return "highly_variable"
        except:
            return "unknown"
    
    def _classify_infestation(self, weed_coverage: float) -> WeedInfestationLevel:
        """Classify weed infestation level based on coverage"""
        if weed_coverage < 5:
            return WeedInfestationLevel.NONE
        elif weed_coverage < 15:
            return WeedInfestationLevel.LOW
        elif weed_coverage < 30:
            return WeedInfestationLevel.MODERATE
        elif weed_coverage < 50:
            return WeedInfestationLevel.HIGH
        else:
            return WeedInfestationLevel.SEVERE
    
    def _identify_weeds(
        self,
        crop_info,
        image_analysis: Dict[str, Any],
        growth_stage: Optional[str]
    ) -> List[Weed]:
        """Identify specific weed types"""
        identified_weeds = []
        
        # Get common weeds for this crop
        common_weeds = crop_info.common_weeds
        
        # Filter by growth stage vulnerability if provided
        if growth_stage:
            common_weeds = [
                w for w in common_weeds
                if "all_stages" in [s.lower().replace(" ", "_") for s in w.growth_stage_vulnerability]
                or growth_stage.lower() in [s.lower().replace(" ", "_") for s in w.growth_stage_vulnerability]
            ]
        
        # If multiple plant types detected, likely multiple weeds
        plant_types = image_analysis.get("distinct_plant_types", 1)
        
        if plant_types > 2:
            # Multiple weed species likely
            identified_weeds = common_weeds[:min(plant_types - 1, len(common_weeds))]
        elif plant_types == 2:
            # Single weed species likely
            identified_weeds = common_weeds[:1] if common_weeds else []
        
        # If no weeds identified but coverage detected, return most common weed
        if not identified_weeds and image_analysis.get("weed_coverage_percentage", 0) > 5:
            identified_weeds = common_weeds[:1] if common_weeds else []
        
        return identified_weeds
    
    def _generate_recommendations(
        self,
        crop_info,
        weeds: List[Weed],
        infestation_level: WeedInfestationLevel,
        growth_stage: Optional[str],
        preferred_control: Optional[ControlMethod]
    ) -> Dict[str, List[str]]:
        """Generate weed control recommendations"""
        recommendations = {
            "chemical": [],
            "organic": [],
            "mechanical": [],
            "integrated": []
        }
        
        if infestation_level == WeedInfestationLevel.NONE:
            recommendations["integrated"] = [
                "Continue regular monitoring",
                "Maintain crop vigor with proper nutrition",
                "Practice preventive measures"
            ]
            return recommendations
        
        # Collect methods from identified weeds
        for weed in weeds:
            for method, controls in weed.control_methods.items():
                recommendations[method].extend(controls)
        
        # Remove duplicates
        for method in recommendations:
            recommendations[method] = list(set(recommendations[method]))
        
        # Add general recommendations based on infestation level
        if infestation_level in [WeedInfestationLevel.HIGH, WeedInfestationLevel.SEVERE]:
            recommendations["integrated"].extend([
                "Immediate action required - consider integrated approach",
                "Combine mechanical and chemical control if needed",
                "Increase monitoring frequency to weekly"
            ])
        
        # Add growth stage specific recommendations
        if growth_stage:
            if "early" in growth_stage.lower() or "seedling" in growth_stage.lower():
                recommendations["integrated"].append(
                    "Critical stage - weeds most competitive now, prioritize control"
                )
            elif "flowering" in growth_stage.lower():
                recommendations["integrated"].append(
                    "Avoid chemicals near flowering to protect pollinators"
                )
        
        # Prioritize preferred method
        if preferred_control:
            method_key = preferred_control.value
            if recommendations[method_key]:
                recommendations[method_key].insert(0, f"✓ Recommended: {method_key.title()} control")
        
        return recommendations
    
    def _assess_priority(
        self,
        infestation_level: WeedInfestationLevel,
        growth_stage: Optional[str]
    ) -> str:
        """Assess control priority level"""
        if infestation_level == WeedInfestationLevel.SEVERE:
            return "critical"
        elif infestation_level == WeedInfestationLevel.HIGH:
            return "high"
        elif infestation_level == WeedInfestationLevel.MODERATE:
            # Higher priority in early growth stages
            if growth_stage and ("early" in growth_stage.lower() or "seedling" in growth_stage.lower()):
                return "high"
            return "medium"
        elif infestation_level == WeedInfestationLevel.LOW:
            return "low"
        else:
            return "none"
    
    def _estimate_yield_impact(
        self,
        infestation_level: WeedInfestationLevel,
        weeds: List[Weed]
    ) -> str:
        """Estimate potential yield impact"""
        if infestation_level == WeedInfestationLevel.NONE:
            return "Negligible (0-2%)"
        elif infestation_level == WeedInfestationLevel.LOW:
            return "Low (5-10%)"
        elif infestation_level == WeedInfestationLevel.MODERATE:
            return "Moderate (15-25%)"
        elif infestation_level == WeedInfestationLevel.HIGH:
            # Check if any weeds are highly competitive
            if any("severe" in w.competition_impact.lower() for w in weeds):
                return "High (30-50%)"
            return "High (25-35%)"
        else:  # SEVERE
            return "Severe (40-70% or complete crop failure)"
    
    def _get_control_timing(
        self,
        growth_stage: Optional[str],
        weeds: List[Weed]
    ) -> List[str]:
        """Get best timing for weed control"""
        timing = []
        
        if growth_stage:
            if "early" in growth_stage.lower() or "seedling" in growth_stage.lower():
                timing.append("Immediate action - critical growth stage")
                timing.append("Pre-emergence herbicides still effective")
            elif "vegetative" in growth_stage.lower():
                timing.append("Good timing for post-emergence control")
                timing.append("Mechanical control safe")
            elif "flowering" in growth_stage.lower():
                timing.append("Avoid chemical sprays during flowering")
                timing.append("Use mechanical control if needed")
            elif "maturity" in growth_stage.lower():
                timing.append("Too late for chemical control")
                timing.append("Hand weeding to prevent seed production")
        
        # Add general timing
        timing.extend([
            "Early morning or late evening (reduced heat stress)",
            "Avoid windy conditions for chemical sprays",
            "Ensure soil moisture adequate for effectiveness"
        ])
        
        return timing
    
    def batch_detect(
        self,
        image_paths: List[str],
        crop_name: str,
        growth_stage: Optional[str] = None
    ) -> List[WeedDetectionResult]:
        """Detect weeds in multiple field images"""
        results = []
        
        for image_path in image_paths:
            try:
                result = self.detect_weeds(image_path, crop_name, growth_stage)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                continue
        
        return results
    
    def get_field_summary(
        self,
        results: List[WeedDetectionResult]
    ) -> Dict[str, Any]:
        """Generate field-level weed summary"""
        if not results:
            return {}
        
        total_coverage = sum(r.weed_coverage_percentage for r in results) / len(results)
        
        all_weeds = set()
        for r in results:
            all_weeds.update(r.weeds_identified)
        
        critical_count = sum(1 for r in results if r.priority_level == "critical")
        high_count = sum(1 for r in results if r.priority_level == "high")
        
        return {
            "total_samples": len(results),
            "average_weed_coverage": round(total_coverage, 2),
            "unique_weeds_identified": list(all_weeds),
            "weed_species_count": len(all_weeds),
            "critical_areas": critical_count,
            "high_priority_areas": high_count,
            "requires_immediate_action": critical_count > 0 or high_count > len(results) // 2,
            "field_infestation_level": self._classify_infestation(total_coverage).value
        }
