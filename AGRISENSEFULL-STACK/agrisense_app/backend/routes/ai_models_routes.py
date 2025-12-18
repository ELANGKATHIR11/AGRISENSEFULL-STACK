"""
API endpoints for Phi LLM and SCOLD VLM integrations.

This module provides REST endpoints for:
1. Phi LLM-enhanced chatbot features
2. SCOLD VLM disease detection
3. SCOLD VLM weed detection
4. Model status and management

Should be imported and included in FastAPI app in main.py
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["ai-models"])

# Import integrations - with graceful degradation
try:
    from ..phi_chatbot_integration import (
        enrich_chatbot_answer,
        rerank_answers_with_phi,
        generate_contextual_response,
        validate_agricultural_answer,
        get_phi_status,
    )
    PHI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Phi integration unavailable: {e}")
    PHI_AVAILABLE = False

try:
    from ..vlm_scold_integration import (
        detect_disease_with_scold,
        detect_weeds_with_scold,
        scold_vlm_status,
    )
    SCOLD_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SCOLD VLM integration unavailable: {e}")
    SCOLD_AVAILABLE = False


# ============================================================================
# PHI LLM ENDPOINTS
# ============================================================================

@router.get("/api/phi/status")
def phi_status() -> Dict[str, Any]:
    """Get Phi LLM integration status"""
    if not PHI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phi integration not available")
    return get_phi_status()


@router.post("/api/chatbot/enrich")
def chatbot_enrich_answer(
    question: str,
    answer: str,
    crop_type: str = "unknown",
    language: str = "en"
) -> Dict[str, Any]:
    """
    Enrich a chatbot answer using Phi LLM
    
    Query Parameters:
    - question: User question
    - answer: Base answer to enrich
    - crop_type: Type of crop (optional)
    - language: Response language code (default: en)
    """
    if not PHI_AVAILABLE:
        return {"enriched_answer": answer, "provider": "base", "llm_available": False}
    
    try:
        enriched = enrich_chatbot_answer(question, answer, crop_type, language)
        return {
            "original_answer": answer,
            "enriched_answer": enriched or answer,
            "provider": "phi-llm",
            "llm_available": True
        }
    except Exception as e:
        logger.error(f"Answer enrichment failed: {e}")
        return {"enriched_answer": answer, "provider": "base", "error": str(e)}


@router.post("/api/chatbot/rerank")
def chatbot_rerank_answers(
    question: str,
    answers: List[str],
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Rerank chatbot answers using Phi LLM
    
    Body:
    {
        "question": "user question",
        "answers": ["answer1", "answer2", ...],
        "top_k": 5
    }
    """
    if not PHI_AVAILABLE:
        return {"reranked_answers": answers[:top_k], "provider": "base", "llm_available": False}
    
    try:
        # Convert string answers to dict format
        answer_dicts = [{"answer": a, "score": 0.5} for a in answers]
        reranked = rerank_answers_with_phi(question, answer_dicts, top_k)
        
        return {
            "original_answers": answers,
            "reranked_answers": [a["answer"] for a in reranked],
            "scores": [a["score"] for a in reranked],
            "provider": "phi-llm",
            "llm_available": True
        }
    except Exception as e:
        logger.error(f"Answer reranking failed: {e}")
        return {"reranked_answers": answers[:top_k], "provider": "base", "error": str(e)}


@router.post("/api/chatbot/contextual")
def chatbot_contextual_response(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate contextual response using Phi LLM
    
    Body:
    {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "system_prompt": "custom system context"
    }
    """
    if not PHI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Phi LLM not available")
    
    try:
        response = generate_contextual_response(messages, system_prompt)
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        return {
            "response": response,
            "provider": "phi-llm",
            "message_count": len(messages)
        }
    except Exception as e:
        logger.error(f"Contextual response generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chatbot/validate")
def chatbot_validate_answer(
    question: str,
    answer: str
) -> Dict[str, Any]:
    """
    Validate if chatbot answer is appropriate
    
    Query Parameters:
    - question: User question
    - answer: Answer to validate
    """
    if not PHI_AVAILABLE:
        return {"is_valid": True, "confidence": 0.5, "provider": "base"}
    
    try:
        validation = validate_agricultural_answer(question, answer)
        validation["provider"] = "phi-llm"
        return validation
    except Exception as e:
        logger.error(f"Answer validation failed: {e}")
        return {"is_valid": True, "confidence": 0.5, "error": str(e)}


# ============================================================================
# SCOLD VLM ENDPOINTS
# ============================================================================

@router.get("/api/scold/status")
def scold_status() -> Dict[str, Any]:
    """Get SCOLD VLM integration status"""
    if not SCOLD_AVAILABLE:
        raise HTTPException(status_code=503, detail="SCOLD integration not available")
    return scold_vlm_status()


@router.post("/api/disease/detect-scold")
async def disease_detect_scold(
    image_base64: str,
    crop_type: str = "unknown"
) -> Dict[str, Any]:
    """
    Detect plant diseases using SCOLD VLM
    
    Body:
    {
        "image_base64": "base64 encoded image",
        "crop_type": "tomato"  # optional
    }
    """
    if not SCOLD_AVAILABLE:
        raise HTTPException(status_code=503, detail="SCOLD VLM not available")
    
    try:
        # Decode base64 to bytes
        import base64
        image_bytes = base64.b64decode(image_base64)
        
        result = detect_disease_with_scold(image_bytes, crop_type)
        
        if not result:
            raise HTTPException(status_code=500, detail="Disease detection failed")
        
        return result
    except Exception as e:
        logger.error(f"SCOLD disease detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/weed/detect-scold")
async def weed_detect_scold(
    image_base64: str,
    crop_type: str = "unknown"
) -> Dict[str, Any]:
    """
    Detect weeds using SCOLD VLM
    
    Body:
    {
        "image_base64": "base64 encoded image",
        "crop_type": "rice"  # optional
    }
    """
    if not SCOLD_AVAILABLE:
        raise HTTPException(status_code=503, detail="SCOLD VLM not available")
    
    try:
        # Decode base64 to bytes
        import base64
        image_bytes = base64.b64decode(image_base64)
        
        result = detect_weeds_with_scold(image_bytes, crop_type)
        
        if not result:
            raise HTTPException(status_code=500, detail="Weed detection failed")
        
        return result
    except Exception as e:
        logger.error(f"SCOLD weed detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/api/models/status")
def models_status() -> Dict[str, Any]:
    """Get status of all AI models"""
    phi_status_data = {"available": False}
    scold_status_data = {"available": False}
    
    try:
        if PHI_AVAILABLE:
            phi_status_data = get_phi_status()
    except Exception as e:
        logger.warning(f"Could not get Phi status: {e}")
    
    try:
        if SCOLD_AVAILABLE:
            scold_status_data = scold_vlm_status()
    except Exception as e:
        logger.warning(f"Could not get SCOLD status: {e}")
    
    return {
        "phi_llm": phi_status_data,
        "scold_vlm": scold_status_data,
        "timestamp": __import__("time").strftime("%Y-%m-%d %H:%M:%S")
    }


@router.get("/api/models/health")
def models_health() -> Dict[str, Any]:
    """Quick health check for all models"""
    health = {
        "phi_llm": {"healthy": False, "reason": "Not available"},
        "scold_vlm": {"healthy": False, "reason": "Not available"}
    }
    
    try:
        if PHI_AVAILABLE:
            status = get_phi_status()
            health["phi_llm"] = {
                "healthy": status.get("available", False),
                "model": status.get("model"),
                "reason": "Ready" if status.get("available") else "Unavailable"
            }
    except Exception as e:
        health["phi_llm"]["reason"] = str(e)
    
    try:
        if SCOLD_AVAILABLE:
            status = scold_vlm_status()
            health["scold_vlm"] = {
                "healthy": status.get("available", False),
                "model": status.get("model"),
                "reason": "Ready" if status.get("available") else "Unavailable"
            }
    except Exception as e:
        health["scold_vlm"]["reason"] = str(e)
    
    overall_healthy = all(h.get("healthy", False) for h in health.values())
    
    return {
        "models": health,
        "overall": "healthy" if overall_healthy else "degraded"
    }
