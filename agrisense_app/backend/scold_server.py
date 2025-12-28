"""
SCOLD VLM FastAPI Server
=========================

FastAPI server for SCOLD Vision-Language Model inference.
Provides REST API for agricultural image analysis.

Endpoints:
----------
- GET  /health - Health check
- GET  /status - Model status
- POST /api/detect/disease - Disease detection
- POST /api/detect/weed - Weed identification
- POST /api/analyze - General image analysis
"""

import base64
import io
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SCOLD VLM Server",
    description="Agricultural Vision-Language Model for disease and weed detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
_scold_model = None
_model_loaded = False


# ============================================================================
# Request/Response Models
# ============================================================================

class ImageAnalysisRequest(BaseModel):
    """Request for image analysis"""
    image: str = Field(..., description="Base64 encoded image")
    crop_type: Optional[str] = Field(None, description="Type of crop")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)


class Detection(BaseModel):
    """Single detection result"""
    class_name: str
    confidence: float
    bbox: Optional[List[float]] = None
    area_percentage: Optional[float] = None
    class_id: Optional[int] = None


class AnalysisResponse(BaseModel):
    """Response for image analysis"""
    success: bool
    detections: List[Detection]
    detection_count: int
    processing_time_ms: float
    model_version: str = "SCOLD-1.0"
    metadata: Dict[str, Any] = {}


# ============================================================================
# Model Loading
# ============================================================================

def load_scold_model():
    """Load SCOLD model (lazy loading)"""
    global _scold_model, _model_loaded
    
    if _model_loaded:
        return _scold_model
    
    try:
        import torch
        from transformers import AutoModel, AutoProcessor
        
        model_path = os.getenv(
            "SCOLD_MODEL_PATH",
            str(Path(__file__).parent.parent.parent / "AI_Models" / "scold")
        )
        
        logger.info(f"Loading SCOLD model from: {model_path}")
        
        # Load model and processor
        processor = AutoProcessor.from_pretrained(model_path)
        model = AutoModel.from_pretrained(model_path)
        
        # Move to CPU (edge deployment)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        model.eval()
        
        _scold_model = {
            "model": model,
            "processor": processor,
            "device": device
        }
        _model_loaded = True
        
        logger.info(f"✅ SCOLD model loaded successfully on {device}")
        return _scold_model
        
    except Exception as e:
        logger.error(f"Failed to load SCOLD model: {e}", exc_info=True)
        _model_loaded = False
        return None


def decode_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    try:
        image_bytes = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")


def run_inference(
    image: Image.Image,
    prompt: str,
    confidence_threshold: float = 0.5
) -> List[Detection]:
    """Run SCOLD model inference"""
    
    model_dict = load_scold_model()
    
    if model_dict is None:
        # Fallback detection (for testing)
        return [
            Detection(
                class_name="Model Not Loaded",
                confidence=0.0,
                bbox=None,
                area_percentage=0.0
            )
        ]
    
    try:
        import torch
        
        model = model_dict["model"]
        processor = model_dict["processor"]
        device = model_dict["device"]
        
        # Preprocess image
        inputs = processor(
            images=image,
            text=prompt,
            return_tensors="pt"
        ).to(device)
        
        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Parse outputs (simplified - adapt based on SCOLD's actual output format)
        detections = []
        
        # TODO: Parse actual SCOLD outputs
        # This is a placeholder implementation
        # The actual SCOLD model output format needs to be determined
        
        if hasattr(outputs, "logits"):
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            
            # Get top detections
            top_k = 5
            top_probs, top_indices = torch.topk(probs[0], top_k)
            
            for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
                if prob >= confidence_threshold:
                    detections.append(Detection(
                        class_name=f"class_{int(idx)}",
                        confidence=float(prob),
                        bbox=None,
                        area_percentage=0.0,
                        class_id=int(idx)
                    ))
        
        return detections
        
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        return []


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SCOLD VLM Server",
        "model_loaded": _model_loaded
    }


@app.get("/status")
async def get_status():
    """Get model status"""
    model_dict = load_scold_model()
    
    return {
        "model_loaded": _model_loaded,
        "model_path": os.getenv("SCOLD_MODEL_PATH", "Not set"),
        "device": model_dict["device"] if model_dict else "N/A",
        "available_endpoints": [
            "/health",
            "/status",
            "/api/detect/disease",
            "/api/detect/weed",
            "/api/analyze"
        ]
    }


@app.post("/api/detect/disease", response_model=AnalysisResponse)
async def detect_disease(request: ImageAnalysisRequest):
    """
    Detect plant diseases in image
    
    Args:
        request: Image analysis request with base64 image
        
    Returns:
        AnalysisResponse with disease detections
    """
    start_time = time.time()
    
    try:
        # Decode image
        image = decode_image(request.image)
        
        # Build prompt for disease detection
        crop_type = request.crop_type or "plant"
        prompt = (
            f"Identify any diseases in this {crop_type} image. "
            f"Provide disease names, severity, and affected areas."
        )
        
        # Run inference
        detections = run_inference(
            image=image,
            prompt=prompt,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return AnalysisResponse(
            success=True,
            detections=detections,
            detection_count=len(detections),
            processing_time_ms=processing_time,
            metadata={
                "crop_type": request.crop_type,
                "analysis_type": "disease_detection"
            }
        )
        
    except Exception as e:
        logger.error(f"Disease detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/detect/weed", response_model=AnalysisResponse)
async def detect_weed(request: ImageAnalysisRequest):
    """
    Detect weeds in agricultural field image
    
    Args:
        request: Image analysis request with base64 image
        
    Returns:
        AnalysisResponse with weed detections
    """
    start_time = time.time()
    
    try:
        # Decode image
        image = decode_image(request.image)
        
        # Build prompt for weed detection
        crop_type = request.crop_type or "crop"
        prompt = (
            f"Identify weeds in this {crop_type} field. "
            f"Distinguish between weeds and crop plants. "
            f"Provide weed names and locations."
        )
        
        # Run inference
        detections = run_inference(
            image=image,
            prompt=prompt,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return AnalysisResponse(
            success=True,
            detections=detections,
            detection_count=len(detections),
            processing_time_ms=processing_time,
            metadata={
                "crop_type": request.crop_type,
                "analysis_type": "weed_detection"
            }
        )
        
    except Exception as e:
        logger.error(f"Weed detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    General agricultural image analysis
    
    Args:
        request: Image analysis request with base64 image
        
    Returns:
        AnalysisResponse with analysis results
    """
    start_time = time.time()
    
    try:
        # Decode image
        image = decode_image(request.image)
        
        # Build general analysis prompt
        prompt = (
            f"Analyze this agricultural image. "
            f"Identify crop types, health status, diseases, weeds, "
            f"pests, and any issues requiring attention."
        )
        
        # Run inference
        detections = run_inference(
            image=image,
            prompt=prompt,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return AnalysisResponse(
            success=True,
            detections=detections,
            detection_count=len(detections),
            processing_time_ms=processing_time,
            metadata={
                "crop_type": request.crop_type,
                "analysis_type": "general"
            }
        )
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("🚀 SCOLD VLM Server starting...")
    logger.info("Attempting to load model...")
    load_scold_model()


@app.on_event("shutdown")
async def shutdown_event():
    """Run on server shutdown"""
    logger.info("👋 SCOLD VLM Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("SCOLD_PORT", "8001"))
    host = os.getenv("SCOLD_HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
