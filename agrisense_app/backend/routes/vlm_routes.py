"""
VLM API Routes for AgriSense
REST API endpoints for disease detection and weed management
"""

import logging
import io
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..vlm.vlm_engine import VLMEngine
from ..vlm.disease_detector import DiseaseSeverity
from ..vlm.weed_detector import WeedInfestationLevel

logger = logging.getLogger(__name__)

# Initialize VLM Engine
vlm_engine = VLMEngine(use_ml=True)

# Create router
router = APIRouter(prefix="/api/vlm", tags=["VLM - Vision Language Model"])


# Request/Response Models
class CropListResponse(BaseModel):
    """Response for listing crops"""
    total_crops: int
    categories: dict
    crops: List[str]


class CropInfoResponse(BaseModel):
    """Response for crop information"""
    name: str
    scientific_name: str
    category: str
    growth_stages: List[str]
    optimal_conditions: dict
    regional_importance: List[str]
    common_diseases: List[str]
    common_weeds: List[str]


class DiseaseAnalysisResponse(BaseModel):
    """Response for disease analysis"""
    analysis_type: str = "disease"
    crop_name: str
    disease_name: Optional[str]
    confidence: float
    severity: str
    affected_area_percentage: float
    symptoms_detected: List[str]
    treatment_recommendations: List[str]
    prevention_tips: List[str]
    priority_actions: List[str]
    estimated_time_to_action: str
    urgent_action_required: bool
    success_probability: float
    cost_estimate: Optional[dict] = None


class WeedAnalysisResponse(BaseModel):
    """Response for weed analysis"""
    analysis_type: str = "weed"
    crop_name: str
    weeds_identified: List[str]
    infestation_level: str
    weed_coverage_percentage: float
    control_recommendations: dict
    priority_level: str
    estimated_yield_impact: str
    best_control_timing: List[str]
    priority_actions: List[str]
    estimated_time_to_action: str
    multiple_weeds_detected: bool
    success_probability: float
    cost_estimate: Optional[dict] = None


class ComprehensiveAnalysisResponse(BaseModel):
    """Response for comprehensive analysis"""
    analysis_type: str = "comprehensive"
    crop_name: str
    disease_analysis: dict
    weed_analysis: dict
    combined_recommendations: List[str]
    priority_actions: List[str]
    estimated_time_to_action: str
    success_probability: float
    cost_estimate: Optional[dict] = None


# ====================
# API ENDPOINTS
# ====================

@router.get("/health", summary="VLM Health Check")
async def vlm_health():
    """Check VLM system health"""
    return {
        "status": "healthy",
        "vlm_engine": "initialized",
        "supported_crops": len(vlm_engine.supported_crops),
        "disease_detector": "active",
        "weed_detector": "active"
    }


@router.get("/crops", response_model=CropListResponse, summary="List All Supported Crops")
async def list_crops(
    category: Optional[str] = Query(None, description="Filter by category (cereal, pulse, oilseed, etc.)")
):
    """
    List all supported crops
    
    **Categories:**
    - cereal
    - pulse
    - oilseed
    - vegetable
    - fruit
    - cash_crop
    - spice
    """
    try:
        crops = vlm_engine.list_supported_crops(category)
        
        # Get categories distribution
        all_crops = vlm_engine.supported_crops
        categories = {}
        for crop_key in all_crops:
            crop_info = vlm_engine.get_crop_info(crop_key)
            if crop_info:
                cat = crop_info["category"]
                categories[cat] = categories.get(cat, 0) + 1
        
        return CropListResponse(
            total_crops=len(crops),
            categories=categories,
            crops=crops
        )
    except Exception as e:
        logger.error(f"Failed to list crops: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crops/{crop_name}", response_model=CropInfoResponse, summary="Get Crop Information")
async def get_crop_details(crop_name: str):
    """
    Get detailed information about a specific crop
    
    **Parameters:**
    - crop_name: Name of the crop (e.g., "rice", "wheat", "tomato")
    """
    try:
        crop_info = vlm_engine.get_crop_info(crop_name)
        if not crop_info:
            raise HTTPException(status_code=404, detail=f"Crop '{crop_name}' not found")
        
        return CropInfoResponse(**crop_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get crop info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crops/{crop_name}/diseases", summary="Get Disease Library for Crop")
async def get_disease_library(crop_name: str):
    """
    Get all known diseases for a specific crop
    
    Returns detailed information about each disease including:
    - Symptoms
    - Causes
    - Treatment options
    - Prevention strategies
    """
    try:
        diseases = vlm_engine.get_disease_library(crop_name)
        if not diseases:
            raise HTTPException(status_code=404, detail=f"No diseases found for crop '{crop_name}'")
        
        return {
            "crop_name": crop_name,
            "total_diseases": len(diseases),
            "diseases": diseases
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get disease library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crops/{crop_name}/weeds", summary="Get Weed Library for Crop")
async def get_weed_library(crop_name: str):
    """
    Get all common weeds for a specific crop
    
    Returns detailed information about each weed including:
    - Identification characteristics
    - Control methods (chemical, organic, mechanical)
    - Competition impact
    - Vulnerable growth stages
    """
    try:
        weeds = vlm_engine.get_weed_library(crop_name)
        if not weeds:
            raise HTTPException(status_code=404, detail=f"No weeds found for crop '{crop_name}'")
        
        return {
            "crop_name": crop_name,
            "total_weeds": len(weeds),
            "weeds": weeds
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get weed library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/disease", response_model=DiseaseAnalysisResponse, summary="Analyze Plant Disease")
async def analyze_disease(
    image: UploadFile = File(..., description="Plant image showing disease symptoms"),
    crop_name: str = Form(..., description="Name of the crop (e.g., 'rice', 'wheat')"),
    expected_diseases: Optional[str] = Form(None, description="Comma-separated list of expected diseases"),
    include_cost: bool = Form(False, description="Include cost estimate")
):
    """
    Analyze plant image for disease detection
    
    **Upload Requirements:**
    - Image format: JPG, JPEG, PNG
    - Image should show disease symptoms clearly
    - Close-up of affected plant parts preferred
    - Good lighting conditions
    
    **Returns:**
    - Disease identification
    - Severity assessment
    - Treatment recommendations
    - Prevention tips
    - Time-sensitive actions
    - Cost estimates (if requested)
    """
    try:
        # Read image
        image_bytes = await image.read()
        
        # Parse expected diseases
        expected_list = None
        if expected_diseases:
            expected_list = [d.strip() for d in expected_diseases.split(",")]
        
        # Analyze
        result = vlm_engine.analyze_disease(
            image_bytes,
            crop_name,
            expected_diseases=expected_list,
            include_cost_estimate=include_cost
        )
        
        # Format response
        disease_data = result.disease_analysis
        
        return DiseaseAnalysisResponse(
            crop_name=result.crop_name,
            disease_name=disease_data["disease_name"],
            confidence=disease_data["confidence"],
            severity=disease_data["severity"],
            affected_area_percentage=disease_data["affected_area_percentage"],
            symptoms_detected=disease_data["symptoms_detected"],
            treatment_recommendations=disease_data["treatment_recommendations"],
            prevention_tips=disease_data["prevention_tips"],
            priority_actions=result.priority_actions or [],
            estimated_time_to_action=result.estimated_time_to_action or "Unknown",
            urgent_action_required=disease_data["urgent_action_required"],
            success_probability=result.success_probability,
            cost_estimate=result.cost_estimate
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Disease analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/weed", response_model=WeedAnalysisResponse, summary="Analyze Field Weeds")
async def analyze_weeds(
    image: UploadFile = File(..., description="Field image showing weed infestation"),
    crop_name: str = Form(..., description="Name of the crop"),
    growth_stage: Optional[str] = Form(None, description="Current crop growth stage"),
    preferred_control: Optional[str] = Form(None, description="Preferred control method: chemical, organic, mechanical"),
    include_cost: bool = Form(False, description="Include cost estimate")
):
    """
    Analyze field image for weed detection and control recommendations
    
    **Upload Requirements:**
    - Image format: JPG, JPEG, PNG
    - Field-level image showing crop and weeds
    - Clear view of ground cover
    - Adequate lighting
    
    **Control Methods:**
    - chemical: Herbicide-based control
    - organic: Natural/biological control
    - mechanical: Physical removal/cultivation
    
    **Returns:**
    - Weed identification
    - Infestation level
    - Control recommendations for all methods
    - Yield impact estimation
    - Best timing for control
    - Cost estimates (if requested)
    """
    try:
        # Read image
        image_bytes = await image.read()
        
        # Validate preferred control
        if preferred_control and preferred_control.lower() not in ["chemical", "organic", "mechanical"]:
            raise ValueError("preferred_control must be: chemical, organic, or mechanical")
        
        # Analyze
        result = vlm_engine.analyze_weeds(
            image_bytes,
            crop_name,
            growth_stage=growth_stage,
            preferred_control=preferred_control,
            include_cost_estimate=include_cost
        )
        
        # Format response
        weed_data = result.weed_analysis
        
        return WeedAnalysisResponse(
            crop_name=result.crop_name,
            weeds_identified=weed_data["weeds_identified"],
            infestation_level=weed_data["infestation_level"],
            weed_coverage_percentage=weed_data["weed_coverage_percentage"],
            control_recommendations=weed_data["control_recommendations"],
            priority_level=weed_data["priority_level"],
            estimated_yield_impact=weed_data["estimated_yield_impact"],
            best_control_timing=weed_data["best_control_timing"],
            priority_actions=result.priority_actions or [],
            estimated_time_to_action=result.estimated_time_to_action or "Unknown",
            multiple_weeds_detected=weed_data["multiple_weeds_detected"],
            success_probability=result.success_probability,
            cost_estimate=result.cost_estimate
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Weed analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/comprehensive", response_model=ComprehensiveAnalysisResponse, summary="Comprehensive Analysis")
async def analyze_comprehensive(
    plant_image: UploadFile = File(..., description="Close-up plant image for disease detection"),
    field_image: UploadFile = File(..., description="Field image for weed detection"),
    crop_name: str = Form(..., description="Name of the crop"),
    growth_stage: Optional[str] = Form(None, description="Current crop growth stage"),
    include_cost: bool = Form(False, description="Include cost estimates")
):
    """
    Comprehensive analysis - both disease and weed detection
    
    **Upload Requirements:**
    - plant_image: Close-up showing disease symptoms
    - field_image: Field view showing weed coverage
    - Both images: JPG, JPEG, or PNG format
    
    **Returns:**
    - Complete disease analysis
    - Complete weed analysis
    - Combined action plan
    - Prioritized recommendations
    - Cost estimates (if requested)
    """
    try:
        # Read images
        plant_bytes = await plant_image.read()
        field_bytes = await field_image.read()
        
        # Analyze
        result = vlm_engine.analyze_comprehensive(
            plant_bytes,
            field_bytes,
            crop_name,
            growth_stage=growth_stage,
            include_cost_estimate=include_cost
        )
        
        return ComprehensiveAnalysisResponse(
            crop_name=result.crop_name,
            disease_analysis=result.disease_analysis,
            weed_analysis=result.weed_analysis,
            combined_recommendations=result.combined_recommendations or [],
            priority_actions=result.priority_actions or [],
            estimated_time_to_action=result.estimated_time_to_action or "Unknown",
            success_probability=result.success_probability,
            cost_estimate=result.cost_estimate
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/status", summary="VLM System Status")
async def vlm_status():
    """Get detailed VLM system status"""
    return {
        "vlm_version": "1.0.0",
        "supported_crops": len(vlm_engine.supported_crops),
        "disease_detector_active": vlm_engine.disease_detector is not None,
        "weed_detector_active": vlm_engine.weed_detector is not None,
        "ml_models_loaded": vlm_engine.disease_detector.use_ml if vlm_engine.disease_detector else False,
        "capabilities": {
            "disease_detection": True,
            "weed_detection": True,
            "comprehensive_analysis": True,
            "batch_processing": True,
            "cost_estimation": True
        },
        "crop_categories": [
            "cereal", "pulse", "oilseed", "vegetable", 
            "fruit", "cash_crop", "spice"
        ]
    }


# Include router in main app
def include_vlm_routes(app):
    """Include VLM routes in FastAPI app"""
    app.include_router(router)
