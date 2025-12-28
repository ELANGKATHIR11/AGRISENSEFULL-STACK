"""
FastAPI routes for AI-powered crop diagnosis and chatbot
"""

import logging
from typing import Dict, Optional, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel, Field

from agrisense_app.backend.core.vlm_engine import get_vlm_engine, CropDiseaseDetector
from agrisense_app.backend.core.chatbot_engine import get_chatbot_engine, AgriAdvisorBot
from agrisense_app.backend.core.ai.rag_engine import FarmerAssistant, get_farmer_assistant
from agrisense_app.backend.core.ai.vision_engine import CropVisionAnalyst, get_crop_vision_analyst

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if AI dependencies are available
AI_AVAILABLE = True  # Set to True since we have the imports working

# Create API router
router = APIRouter(prefix="/ai", tags=["AI Services"])


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    """Request model for RAG chatbot."""
    query: str = Field(
        ...,
        description="Farmer's question about agriculture",
        min_length=3,
        max_length=500,
        example="How do I treat tomato blight?",
    )
    return_sources: bool = Field(
        default=False,
        description="Include source documents in response",
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the best practices for wheat cultivation in dry regions?",
                "return_sources": True,
            }
        }


class ChatResponse(BaseModel):
    """Response model for RAG chatbot."""
    answer: str = Field(..., description="Generated answer")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    retrieval_mode: str = Field(..., description="RAG mode used (rag/retrieval_only/no_results)")
    sources: Optional[list] = Field(None, description="Source documents (if requested)")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "For wheat cultivation in dry regions, follow these best practices...",
                "confidence": 0.92,
                "retrieval_mode": "rag",
                "sources": [
                    {
                        "content": "Wheat cultivation guide excerpt...",
                        "metadata": {"source": "wheat_guide.pdf", "page": 12}
                    }
                ],
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for VLM image analysis."""
    diagnosis: str = Field(..., description="Main finding (disease name, weed species, etc.)")
    severity: str = Field(..., description="Severity level (none/mild/moderate/severe)")
    symptoms: list = Field(default_factory=list, description="Visible symptoms or characteristics")
    treatment: str = Field(..., description="Recommended treatment or actions")
    confidence: float = Field(..., description="Model confidence (0.0-1.0)")
    task: str = Field(..., description="Analysis task performed")
    raw_output: str = Field(..., description="Full model response")
    
    class Config:
        schema_extra = {
            "example": {
                "diagnosis": "Late Blight (Phytophthora infestans)",
                "severity": "moderate",
                "symptoms": [
                    "Dark brown spots on leaves",
                    "White mold on leaf undersides",
                    "Yellowing around affected areas"
                ],
                "treatment": "Apply copper-based fungicide immediately. Remove and destroy infected plants.",
                "confidence": 0.87,
                "task": "disease",
                "raw_output": "This tomato plant shows signs of late blight...",
            }
        }


class IngestRequest(BaseModel):
    """Request model for knowledge base ingestion."""
    pdf_dir: Optional[str] = Field(
        None,
        description="Directory containing PDF crop guides",
        example="./crop_guides",
    )
    json_path: Optional[str] = Field(
        None,
        description="Path to chatbot_qa_pairs.json",
        example="./chatbot_qa_pairs.json",
    )
    force_rebuild: bool = Field(
        default=False,
        description="Force rebuild even if vectorstore exists",
    )


class StatsResponse(BaseModel):
    """Response model for AI system statistics."""
    rag_available: bool
    vlm_available: bool
    rag_stats: Optional[Dict[str, Any]] = None
    vlm_stats: Optional[Dict[str, Any]] = None


# ==================== Endpoints ====================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the RAG-based Farmer Assistant",
    description=(
        "Submit an agricultural question to the RAG chatbot. "
        "The system retrieves relevant context from crop guides and QA pairs, "
        "then generates a comprehensive answer using a local LLM."
    ),
)
async def chat_with_assistant(
    request: ChatRequest,
    assistant: FarmerAssistant = Depends(get_farmer_assistant),
) -> ChatResponse:
    """
    RAG-based chatbot endpoint for agricultural advice.
    
    Why async:
    - FastAPI handles concurrent requests efficiently
    - Non-blocking I/O improves throughput
    - Future-proof for async LLM calls
    
    Why Depends:
    - Dependency injection ensures singleton usage
    - FastAPI handles initialization automatically
    - Easy to mock for testing
    
    Process:
    1. Validate query (Pydantic handles this)
    2. Retrieve relevant context from ChromaDB
    3. Generate answer using LLM
    4. Return structured response
    
    Parameters:
    -----------
    request : ChatRequest
        User query and options
    assistant : FarmerAssistant
        Injected RAG engine instance
        
    Returns:
    --------
    ChatResponse with answer, confidence, and optional sources
    
    Raises:
    -------
    HTTPException 503: If AI services unavailable
    HTTPException 500: If processing fails
    """
    if not AI_AVAILABLE or assistant is None:
        raise HTTPException(
            status_code=503,
            detail="AI services unavailable. Install requirements-ai.txt and initialize knowledge base.",
        )
    
    try:
        logger.info(f"Processing chat query: {request.query[:50]}...")
        
        # Call RAG engine
        result = assistant.ask(
            query=request.query,
            return_sources=request.return_sources,
        )
        
        # Check for errors in result
        if "error" in result:
            logger.error(f"RAG engine error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process query: {result['error']}",
            )
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze crop image with VLM",
    description=(
        "Upload a crop image for AI-powered disease or weed detection. "
        "The VLM analyzes the image and provides diagnosis, severity assessment, "
        "visible symptoms, and treatment recommendations."
    ),
)
async def analyze_crop_image(
    file: UploadFile = File(
        ...,
        description="Crop image (JPEG, PNG, etc.)",
        example="tomato_leaf.jpg",
    ),
    task: str = Form(
        default="disease",
        description="Analysis task: disease, weed, or general",
        example="disease",
    ),
    analyst: CropVisionAnalyst = Depends(get_crop_vision_analyst),
) -> AnalyzeResponse:
    """
    VLM-based crop image analysis endpoint.
    
    Why UploadFile:
    - Efficient handling of large files
    - Async streaming support
    - Automatic cleanup after processing
    
    Why Form for task:
    - Multipart form-data supports both file + fields
    - Standard web form approach
    
    Process:
    1. Validate image upload (FastAPI handles this)
    2. Read image bytes
    3. Preprocess and analyze with VLM
    4. Parse output into structured format
    5. Return diagnosis + recommendations
    
    Parameters:
    -----------
    file : UploadFile
        Uploaded image file
    task : str
        "disease", "weed", or "general"
    analyst : CropVisionAnalyst
        Injected VLM instance
        
    Returns:
    --------
    AnalyzeResponse with diagnosis, treatment, etc.
    
    Raises:
    -------
    HTTPException 400: If invalid image format
    HTTPException 503: If AI services unavailable
    HTTPException 500: If processing fails
    """
    if not AI_AVAILABLE or analyst is None:
        raise HTTPException(
            status_code=503,
            detail="AI services unavailable. Install requirements-ai.txt.",
        )
    
    # Validate file type
    # Why: Prevent processing non-image files
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(allowed_types)}",
        )
    
    # Validate task
    if task not in ["disease", "weed", "general"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task: {task}. Must be 'disease', 'weed', or 'general'.",
        )
    
    try:
        logger.info(f"Processing image analysis: {file.filename}, task={task}")
        
        # Read image bytes
        # Why async: Non-blocking file reading
        image_bytes = await file.read()
        
        # Validate file size (max 10MB)
        # Why: Prevent memory exhaustion
        max_size_mb = 10
        if len(image_bytes) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(image_bytes) / (1024**2):.1f}MB. Max: {max_size_mb}MB",
            )
        
        # Analyze with VLM
        result = analyst.analyze_image(
            image_bytes=image_bytes,
            task=task,
        )
        
        # Check for errors in result
        if "error" in result:
            logger.error(f"VLM analysis error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze image: {result['error']}",
            )
        
        return AnalyzeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in analyze endpoint")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


@router.post(
    "/ingest",
    summary="Ingest knowledge base for RAG",
    description=(
        "Trigger knowledge base ingestion from PDFs and JSON QA pairs. "
        "This is typically a one-time operation (or periodic update). "
        "Requires admin authentication in production."
    ),
)
async def ingest_knowledge_base(
    request: IngestRequest,
    assistant: FarmerAssistant = Depends(get_farmer_assistant),
) -> Dict[str, Any]:
    """
    Trigger RAG knowledge base ingestion.
    
    Why separate endpoint:
    - Ingestion is a long-running operation
    - Should be triggered manually or via scheduler
    - Not part of normal user flow
    
    Security Note:
    - In production, add authentication to this endpoint
    - Example: @router.post("/ingest", dependencies=[Depends(verify_admin)])
    
    Process:
    1. Validate paths
    2. Load PDFs and JSON
    3. Chunk documents
    4. Generate embeddings
    5. Store in ChromaDB
    
    Parameters:
    -----------
    request : IngestRequest
        Paths to PDF directory and JSON file
    assistant : FarmerAssistant
        Injected RAG engine
        
    Returns:
    --------
    Dict with ingestion statistics (docs processed, chunks created, etc.)
    
    Raises:
    -------
    HTTPException 400: If invalid paths
    HTTPException 503: If AI unavailable
    HTTPException 500: If ingestion fails
    """
    if not AI_AVAILABLE or assistant is None:
        raise HTTPException(
            status_code=503,
            detail="AI services unavailable. Install requirements-ai.txt.",
        )
    
    # Validate at least one source provided
    if not request.pdf_dir and not request.json_path:
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one of: pdf_dir, json_path",
        )
    
    try:
        logger.info(f"Starting knowledge base ingestion: pdf_dir={request.pdf_dir}, json_path={request.json_path}")
        
        # Trigger ingestion
        stats = assistant.ingest_knowledge_base(
            pdf_dir=request.pdf_dir,
            json_path=request.json_path,
            force_rebuild=request.force_rebuild,
        )
        
        logger.info(f"Ingestion complete: {stats}")
        return {
            "status": "success",
            "message": "Knowledge base ingestion completed",
            **stats,
        }
        
    except ValueError as e:
        logger.error(f"Ingestion validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Unexpected error during ingestion")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get AI system statistics",
    description=(
        "Retrieve statistics about the AI systems: "
        "RAG chatbot (knowledge base size, model info) and "
        "VLM analyst (model info, memory usage, device)."
    ),
)
async def get_ai_stats(
    assistant: Optional[FarmerAssistant] = Depends(get_farmer_assistant) if AI_AVAILABLE else None,
    analyst: Optional[CropVisionAnalyst] = Depends(get_crop_vision_analyst) if AI_AVAILABLE else None,
) -> StatsResponse:
    """
    Get AI system statistics and health status.
    
    Why this endpoint:
    - Monitoring: Check if AI services are healthy
    - Debugging: View memory usage, device info
    - Admin dashboard: Display system status
    
    Returns:
    --------
    StatsResponse with availability flags and detailed stats
    """
    response = StatsResponse(
        rag_available=AI_AVAILABLE and assistant is not None,
        vlm_available=AI_AVAILABLE and analyst is not None,
    )
    
    try:
        if assistant:
            response.rag_stats = assistant.get_stats()
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        response.rag_stats = {"error": str(e)}
    
    try:
        if analyst:
            response.vlm_stats = analyst.get_stats()
    except Exception as e:
        logger.error(f"Failed to get VLM stats: {e}")
        response.vlm_stats = {"error": str(e)}
    
    return response


# ==================== Health Check ====================

@router.get(
    "/health",
    summary="AI services health check",
    description="Check if AI services are available and ready",
)
async def health_check() -> Dict[str, Any]:
    """
    Simple health check for AI services.
    
    Why separate from main /health:
    - AI services have different dependencies
    - Allows monitoring AI availability independently
    - Can be used by load balancers
    
    Returns:
    --------
    Dict with status and availability info
    """
    return {
        "status": "healthy" if AI_AVAILABLE else "degraded",
        "ai_available": AI_AVAILABLE,
        "message": "AI services ready" if AI_AVAILABLE else "AI dependencies not installed",
    }


# ==================== Error Handlers ====================

# Note: FastAPI automatically handles HTTPException and validation errors
# Additional custom error handlers can be added here if needed

# Example:
# @router.exception_handler(CustomException)
# async def custom_exception_handler(request: Request, exc: CustomException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.message},
#     )
