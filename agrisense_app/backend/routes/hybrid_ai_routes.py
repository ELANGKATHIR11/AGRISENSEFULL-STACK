"""
API Routes for Hybrid LLM+VLM Agricultural AI

Endpoints for multimodal agricultural analysis combining:
- Visual analysis (SCOLD VLM)
- Language understanding (Phi LLM)
- Offline edge deployment
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..hybrid_agri_ai import (
    AnalysisType,
    HybridAgriAI,
    HybridAnalysis,
    get_hybrid_ai,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hybrid", tags=["Hybrid AI"])


# ============================================================================
# Request/Response Models
# ============================================================================

class MultimodalRequest(BaseModel):
    """Request for multimodal analysis"""
    image_base64: str = Field(..., description="Base64 encoded image")
    query: str = Field(..., description="Natural language question about the image")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANS...",
                "query": "What disease is affecting my tomato plant?",
                "context": {
                    "crop_type": "tomato",
                    "location": "greenhouse",
                    "weather": "humid"
                }
            }
        }


class TextQueryRequest(BaseModel):
    """Request for text-only analysis"""
    query: str = Field(..., description="Agricultural question or request")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context information")
    use_history: bool = Field(default=True, description="Use conversation history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's the best fertilizer for wheat in sandy soil?",
                "context": {"soil_type": "sandy", "crop": "wheat"},
                "use_history": True
            }
        }


class ImageAnalysisRequest(BaseModel):
    """Request for image-only analysis"""
    image_base64: str = Field(..., description="Base64 encoded image")
    analysis_type: str = Field(
        default="multimodal",
        description="Type of analysis: disease_detection, weed_identification, crop_health, pest_detection, soil_analysis, multimodal"
    )
    custom_prompt: Optional[str] = Field(default=None, description="Custom analysis prompt")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANS...",
                "analysis_type": "disease_detection",
                "custom_prompt": "Focus on leaf spots and discoloration"
            }
        }


class HybridAnalysisResponse(BaseModel):
    """Response from hybrid analysis"""
    success: bool
    analysis_type: str
    synthesis: Optional[str] = None
    actionable_steps: List[str] = []
    confidence_score: float
    processing_time_ms: float
    visual_analysis: Optional[Dict[str, Any]] = None
    textual_analysis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class SystemStatusResponse(BaseModel):
    """Hybrid AI system status"""
    hybrid_ai_available: bool
    phi_llm_available: bool
    scold_vlm_available: bool
    mode: str
    conversation_history_length: int
    cache_size: int
    config: Dict[str, Any]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=HybridAnalysisResponse)
async def analyze_multimodal(request: MultimodalRequest):
    """
    🌾 Multimodal Agricultural Analysis
    
    Analyze an agricultural image with a natural language question.
    Combines visual AI (SCOLD) and language AI (Phi) for comprehensive insights.
    
    **Use Cases:**
    - "What disease is affecting my crop?"
    - "Is this weed harmful to my plants?"
    - "How healthy are these crops?"
    - "What pest caused this damage?"
    
    **Returns:**
    - Visual detections (disease, pests, weeds)
    - Natural language explanation
    - Actionable treatment steps
    - Confidence scores
    """
    try:
        ai = get_hybrid_ai()
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image: {str(e)}"
            )
        
        # Perform hybrid analysis
        result: HybridAnalysis = ai.analyze_multimodal(
            image_data=image_bytes,
            text_query=request.query,
            context=request.context
        )
        
        # Build response
        return HybridAnalysisResponse(
            success=True,
            analysis_type=result.analysis_type.value,
            synthesis=result.synthesis,
            actionable_steps=result.actionable_steps or [],
            confidence_score=result.confidence_score,
            processing_time_ms=result.processing_time_ms,
            visual_analysis={
                "detections": result.visual.detections if result.visual else [],
                "confidence": result.visual.confidence if result.visual else 0.0,
                "severity": result.visual.severity if result.visual else None,
                "affected_area_percent": result.visual.affected_area_percent if result.visual else None
            } if result.visual else None,
            textual_analysis={
                "response": result.textual.response if result.textual else None,
                "confidence": result.textual.confidence if result.textual else 0.0,
                "recommendations": result.textual.recommendations if result.textual else []
            } if result.textual else None,
            metadata=result.metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multimodal analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze/upload", response_model=HybridAnalysisResponse)
async def analyze_multimodal_upload(
    image: UploadFile = File(..., description="Agricultural image file"),
    query: str = Form(..., description="Question about the image"),
    context_json: Optional[str] = Form(default=None, description="Context as JSON string")
):
    """
    🌾 Multimodal Analysis with File Upload
    
    Same as /analyze but accepts file upload instead of base64.
    More convenient for web forms and mobile apps.
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8004/api/hybrid/analyze/upload \
      -F "image=@diseased_leaf.jpg" \
      -F "query=What's wrong with this leaf?"
    ```
    """
    try:
        # Read uploaded file
        image_bytes = await image.read()
        
        # Parse context if provided
        context = None
        if context_json:
            import json
            try:
                context = json.loads(context_json)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON in context_json"
                )
        
        # Convert to base64 for consistency
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Use main analysis endpoint
        request = MultimodalRequest(
            image_base64=image_b64,
            query=query,
            context=context
        )
        
        return await analyze_multimodal(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload analysis failed: {str(e)}"
        )


@router.post("/text", response_model=Dict[str, Any])
async def analyze_text(request: TextQueryRequest):
    """
    💬 Text-Only Agricultural Advice
    
    Ask agricultural questions without images.
    Uses Phi LLM with agricultural expertise.
    
    **Examples:**
    - "When should I plant wheat in North India?"
    - "What's the best organic fertilizer for tomatoes?"
    - "How do I prepare soil for monsoon planting?"
    """
    try:
        ai = get_hybrid_ai()
        
        result = ai.analyze_text(
            query=request.query,
            context=request.context,
            use_history=request.use_history
        )
        
        return {
            "success": True,
            "response": result.response,
            "confidence": result.confidence,
            "recommendations": result.recommendations or [],
            "context_used": result.context_used
        }
        
    except Exception as e:
        logger.error(f"Text analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Text analysis failed: {str(e)}"
        )


@router.post("/image", response_model=Dict[str, Any])
async def analyze_image(request: ImageAnalysisRequest):
    """
    🔍 Image-Only Visual Analysis
    
    Analyze agricultural image without text query.
    Uses SCOLD VLM for visual detection.
    
    **Analysis Types:**
    - disease_detection: Identify plant diseases
    - weed_identification: Detect and classify weeds
    - crop_health: Assess overall crop condition
    - pest_detection: Find pests and damage
    - soil_analysis: Evaluate soil conditions
    - multimodal: General analysis
    """
    try:
        ai = get_hybrid_ai()
        
        # Decode image
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image: {str(e)}"
            )
        
        # Parse analysis type
        try:
            analysis_type = AnalysisType(request.analysis_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis_type. Must be one of: {[t.value for t in AnalysisType]}"
            )
        
        result = ai.analyze_image(
            image_data=image_bytes,
            analysis_type=analysis_type,
            prompt=request.custom_prompt
        )
        
        return {
            "success": True,
            "detections": result.detections,
            "confidence": result.confidence,
            "locations": result.locations,
            "severity": result.severity,
            "affected_area_percent": result.affected_area_percent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


@router.get("/status", response_model=SystemStatusResponse)
async def get_status():
    """
    📊 Hybrid AI System Status
    
    Check availability of LLM (Phi) and VLM (SCOLD) components.
    Useful for health checks and debugging.
    """
    try:
        ai = get_hybrid_ai()
        status = ai.get_status()
        
        return SystemStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )


@router.post("/history/clear")
async def clear_history():
    """
    🗑️ Clear Conversation History
    
    Reset the conversation context for fresh analysis.
    """
    try:
        ai = get_hybrid_ai()
        ai.clear_history()
        
        return {
            "success": True,
            "message": "Conversation history cleared"
        }
        
    except Exception as e:
        logger.error(f"Clear history error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache():
    """
    🗑️ Clear Response Cache
    
    Clear cached responses for fresh analysis.
    """
    try:
        ai = get_hybrid_ai()
        ai.clear_cache()
        
        return {
            "success": True,
            "message": "Response cache cleared"
        }
        
    except Exception as e:
        logger.error(f"Clear cache error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    ❤️ Health Check
    
    Simple endpoint to verify the hybrid AI service is running.
    """
    try:
        ai = get_hybrid_ai()
        status = ai.get_status()
        
        return {
            "status": "healthy",
            "hybrid_available": status["hybrid_ai_available"],
            "components": {
                "phi_llm": "online" if status["phi_llm_available"] else "offline",
                "scold_vlm": "online" if status["scold_vlm_available"] else "offline"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {
            "status": "degraded",
            "error": str(e)
        }
