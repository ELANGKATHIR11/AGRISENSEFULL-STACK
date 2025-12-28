"""
Phi LLM Integration for AgriSense Chatbot

This module enhances the chatbot with Phi local LLM capabilities for:
- Response enrichment
- Answer ranking improvement
- Conversational context handling
- Agricultural domain-specific chat

Environment Variables:
    CHATBOT_USE_PHI_LLM: Enable Phi LLM (default: true if Ollama available)
    PHI_LLM_ENDPOINT: Ollama API endpoint (default: http://localhost:11434)
    PHI_MODEL_NAME: Model name (default: phi)
    PHI_CHAT_TEMPERATURE: Response temperature (default: 0.7)
    PHI_CHAT_TIMEOUT: Request timeout in seconds (default: 30)
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_phi_config() -> tuple[str, str, float, int]:
    """Get Phi LLM configuration from environment variables."""
    endpoint = os.getenv("PHI_LLM_ENDPOINT", "http://localhost:11434").rstrip("/")
    model_name = os.getenv("PHI_MODEL_NAME", "phi")
    temperature = float(os.getenv("PHI_CHAT_TEMPERATURE", "0.7"))
    timeout = int(os.getenv("PHI_CHAT_TIMEOUT", "30"))
    return endpoint, model_name, temperature, timeout


def _is_phi_available() -> bool:
    """Check if Phi LLM is available via Ollama."""
    try:
        import requests
        
        endpoint, _, _, timeout = _get_phi_config()
        response = requests.get(
            f"{endpoint}/api/tags",
            timeout=timeout / 2
        )
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        
        # Check if phi model is available
        phi_available = any("phi" in model.lower() for model in models)
        return phi_available
        
    except Exception as e:
        logger.debug(f"Phi availability check failed: {e}")
        return False


def enrich_chatbot_answer(
    question: str,
    base_answer: str,
    crop_type: str = "unknown",
    language: str = "en",
    timeout_s: float = None
) -> Optional[str]:
    """
    Enrich a base answer using Phi LLM for better context with human-like personality.
    
    Args:
        question: Original user question
        base_answer: Base answer from retrieval system
        crop_type: Type of crop (for context)
        language: Language code
        timeout_s: Request timeout in seconds
        
    Returns:
        Enriched, human-like answer or original answer if LLM unavailable
    """
    try:
        import requests
        
        endpoint, model_name, temperature, config_timeout = _get_phi_config()
        timeout = timeout_s or config_timeout
        
        if not _is_phi_available():
            logger.debug("Phi LLM not available, returning base answer")
            return base_answer
        
        # Build human-like enrichment prompt with personality
        prompt = f"""You are a friendly, experienced farmer and agricultural expert named AgriSense Assistant. 
You've been helping farmers for years and genuinely care about their success. Your personality:
- Warm and encouraging, like talking to a trusted farming neighbor
- Use simple, relatable language (avoid complex jargon)
- Show empathy and understanding of farmers' challenges
- Add personal touches like "I understand..." or "In my experience..."
- Keep responses conversational but informative
- Use encouraging phrases like "You're on the right track!" or "Great question!"
- When appropriate, share practical tips as if from personal experience

User's Question: {question}
Crop Context: {crop_type}
Base Information: {base_answer}

Task: Transform the base information into a warm, human-like response that feels like advice from a trusted friend. 
Make it conversational, encouraging, and practical. Add personality while keeping it helpful.
Return ONLY the enhanced response (no labels, no "Enhanced Answer:" prefix).

Language: {language}

Response:"""
        
        logger.debug(f"Enriching answer with Phi LLM (model: {model_name})")
        t0 = time.time()
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.85,  # Slightly higher for more creative/human responses
                "top_k": 50,
                "top_p": 0.95,  # Higher for more diverse, natural language
                "repeat_penalty": 1.1,  # Reduce repetition
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.warning(f"Phi LLM error: {response.status_code}")
            return base_answer
        
        elapsed = time.time() - t0
        data = response.json()
        enriched = data.get("response", "").strip()
        
        logger.debug(f"Answer enrichment completed in {elapsed:.2f}s")
        
        # Clean up common artifacts from LLM responses
        cleanup_phrases = [
            "enhanced answer:",
            "response:",
            "here's the enhanced response:",
            "here is the enhanced answer:",
        ]
        enriched_lower = enriched.lower()
        for phrase in cleanup_phrases:
            if enriched_lower.startswith(phrase):
                enriched = enriched[len(phrase):].strip()
                break
        
        # If enrichment produced empty result, return base
        if not enriched or len(enriched) < 10:
            return base_answer
        
        return enriched
        
    except Exception as e:
        logger.debug(f"Answer enrichment failed, using base answer: {e}")
        return base_answer


def rerank_answers_with_phi(
    question: str,
    answers: List[Dict[str, Any]],
    top_k: int = 5,
    timeout_s: float = None
) -> List[Dict[str, Any]]:
    """
    Rerank chat answers using Phi LLM relevance scoring.
    
    Args:
        question: User question
        answers: List of answer dicts with 'answer' key
        top_k: Return top k answers
        timeout_s: Request timeout
        
    Returns:
        Reranked answers with updated scores
    """
    try:
        import requests
        
        endpoint, model_name, _, config_timeout = _get_phi_config()
        timeout = timeout_s or config_timeout
        
        if not _is_phi_available() or not answers:
            return answers[:top_k]
        
        # Build reranking prompt
        answer_list = "\n".join(
            [f"{i+1}. {a.get('answer', 'N/A')}" for i, a in enumerate(answers[:10])]
        )
        
        prompt = f"""You are an agricultural expert evaluating answer relevance.

Question: {question}

Answers to rank (1-10):
{answer_list}

Task: Rate each answer's relevance to the question on a scale of 0 to 1.
Return ONLY a JSON array with indices and scores, like:
[{{"index": 1, "score": 0.95}}, {{"index": 2, "score": 0.7}}]

JSON:"""
        
        logger.debug(f"Reranking {len(answers)} answers with Phi LLM")
        t0 = time.time()
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,  # Low temp for ranking
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return answers[:top_k]
        
        data = response.json()
        response_text = data.get("response", "").strip()
        
        # Extract JSON
        import re
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if not match:
            return answers[:top_k]
        
        try:
            rankings = json.loads(match.group(0))
        except json.JSONDecodeError:
            return answers[:top_k]
        
        elapsed = time.time() - t0
        logger.debug(f"Reranking completed in {elapsed:.2f}s")
        
        # Apply new scores
        score_map = {r.get("index", 0): r.get("score", 0) for r in rankings}
        reranked = []
        
        for i, ans in enumerate(answers):
            new_score = score_map.get(i + 1, ans.get("score", 0.5))
            ans_copy = ans.copy()
            ans_copy["score"] = new_score
            ans_copy["reranked"] = True
            reranked.append(ans_copy)
        
        # Sort by new score
        reranked.sort(key=lambda x: x["score"], reverse=True)
        
        return reranked[:top_k]
        
    except Exception as e:
        logger.debug(f"Phi reranking failed: {e}")
        return answers[:top_k]


def generate_contextual_response(
    messages: List[Dict[str, str]],
    system_prompt: str = None,
    timeout_s: float = None
) -> Optional[str]:
    """
    Generate human-like contextual response using Phi LLM for multi-turn conversations.
    
    Args:
        messages: Chat history with role and content
        system_prompt: System context prompt
        timeout_s: Request timeout
        
    Returns:
        Generated human-like response or None if LLM unavailable
    """
    try:
        import requests
        
        endpoint, model_name, temperature, config_timeout = _get_phi_config()
        timeout = timeout_s or config_timeout
        
        if not _is_phi_available() or not messages:
            return None
        
        # Build conversation prompt with human personality
        system = system_prompt or """You are AgriSense Assistant, a warm and friendly agricultural expert. 
You speak like an experienced farmer who genuinely cares about helping others succeed. 
You use simple language, show empathy, share practical tips, and maintain a conversational, 
encouraging tone. Think of yourself as a trusted farming neighbor who's always happy to help."""
        
        prompt_parts = [f"System: {system}\n"]
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)
        
        logger.debug(f"Generating human-like contextual response with {model_name}")
        t0 = time.time()
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.85,  # Higher for more natural conversation
                "top_k": 50,
                "top_p": 0.95,
                "repeat_penalty": 1.1,
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return None
        
        elapsed = time.time() - t0
        data = response.json()
        generated = data.get("response", "").strip()
        
        logger.debug(f"Response generation completed in {elapsed:.2f}s")
        return generated if generated else None
        
    except Exception as e:
        logger.debug(f"Contextual response generation failed: {e}")
        return None


def validate_agricultural_answer(
    question: str,
    answer: str,
    timeout_s: float = None
) -> Dict[str, Any]:
    """
    Validate if answer is appropriate and safe for agricultural context.
    
    Args:
        question: User question
        answer: Proposed answer
        timeout_s: Request timeout
        
    Returns:
        Dict with is_valid, confidence, and feedback
    """
    try:
        import requests
        
        endpoint, model_name, _, config_timeout = _get_phi_config()
        timeout = timeout_s or config_timeout
        
        if not _is_phi_available():
            return {"is_valid": True, "confidence": 0.5, "feedback": "LLM unavailable"}
        
        prompt = f"""You are a safety validator for agricultural advice.

Question: {question}
Proposed Answer: {answer}

Task: Assess if this answer is:
1. Relevant to agriculture
2. Safe and non-harmful
3. Factually reasonable

Return JSON: {{"is_valid": true/false, "confidence": 0-1, "reason": "..."}}

JSON:"""
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            return {"is_valid": True, "confidence": 0.5, "feedback": "Validation skipped"}
        
        data = response.json()
        response_text = data.get("response", "").strip()
        
        # Extract JSON
        import re
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
                return result
            except json.JSONDecodeError:
                pass
        
        return {"is_valid": True, "confidence": 0.5, "feedback": "Could not validate"}
        
    except Exception as e:
        logger.debug(f"Answer validation failed: {e}")
        return {"is_valid": True, "confidence": 0.5, "feedback": f"Validation error: {str(e)}"}


def get_phi_status() -> Dict[str, Any]:
    """
    Get status of Phi LLM integration.
    
    Returns:
        Dict with availability and configuration info
    """
    endpoint, model_name, temperature, timeout = _get_phi_config()
    available = _is_phi_available()
    
    return {
        "available": available,
        "endpoint": endpoint,
        "model": model_name,
        "temperature": temperature,
        "timeout": timeout,
        "status": "ready" if available else "unavailable",
        "features": [
            "answer_enrichment",
            "answer_reranking",
            "contextual_generation",
            "answer_validation",
            "human_like_responses"
        ]
    }


def generate_greeting(
    user_name: str = None,
    time_of_day: str = None,
    language: str = "en"
) -> str:
    """
    Generate a warm, human-like greeting for new chat sessions.
    
    Args:
        user_name: Optional user name for personalization
        time_of_day: morning/afternoon/evening
        language: Language code
        
    Returns:
        Friendly greeting message
    """
    try:
        import requests
        
        endpoint, model_name, _, timeout = _get_phi_config()
        
        if not _is_phi_available():
            # Fallback greetings
            greetings = {
                "en": f"Hello{' ' + user_name if user_name else ''}! I'm your AgriSense Assistant. How can I help you with your farming today?",
                "hi": f"नमस्ते{' ' + user_name if user_name else ''}! मैं आपका AgriSense सहायक हूं। आज खेती में मैं आपकी कैसे मदद कर सकता हूं?",
                "es": f"¡Hola{' ' + user_name if user_name else ''}! Soy tu Asistente AgriSense. ¿Cómo puedo ayudarte con tu agricultura hoy?"
            }
            return greetings.get(language, greetings["en"])
        
        # Generate personalized greeting with Phi
        time_context = f"It's {time_of_day}" if time_of_day else "It's a beautiful day"
        name_context = f"talking to {user_name}" if user_name else "talking to a farmer"
        
        prompt = f"""You are AgriSense Assistant, a warm and friendly agricultural expert.
Generate a brief, welcoming greeting (2-3 sentences max) for a farmer who just opened the chat.

Context:
- {time_context}
- You're {name_context}
- Language: {language}
- Be warm, encouraging, and professional
- Offer to help with farming questions

Generate greeting:"""
        
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.9,
                "max_tokens": 100,
            },
            timeout=5,  # Quick greeting
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            greeting = data.get("response", "").strip()
            if greeting and len(greeting) > 10:
                return greeting
        
        # Fallback if generation fails
        return f"Hello{' ' + user_name if user_name else ''}! I'm your AgriSense Assistant, here to help with all your farming questions. What would you like to know?"
        
    except Exception as e:
        logger.debug(f"Greeting generation failed: {e}")
        return f"Hello{' ' + user_name if user_name else ''}! Welcome to AgriSense. How can I assist you today?"


def get_phi_status() -> Dict[str, Any]:
    """
    Get current Phi LLM status and configuration.
    
    Returns:
        Status dict with availability and config info
    """
    endpoint, model_name, temperature, timeout = _get_phi_config()
    available = _is_phi_available()
    
    return {
        "available": available,
        "endpoint": endpoint,
        "model": model_name,
        "temperature": temperature,
        "timeout": timeout,
        "enabled": os.getenv("CHATBOT_USE_PHI_LLM", "true").lower() in ("true", "1", "yes")
    }


def enrich_chatbot_answer(
    question: str,
    base_answer: str,
    crop_type: str = "unknown",
    language: str = "en",
    timeout_s: Optional[int] = None
) -> str:
    """
    Enrich a chatbot answer with Phi LLM to make it more human-like and contextual.
    
    This is the main function called from main.py to enhance answers with agricultural expertise.
    
    Args:
        question: The farmer's original question
        base_answer: The base answer from the knowledge base
        crop_type: Type of crop being discussed (e.g., "tomato", "rice")
        language: Language code (default: "en")
        timeout_s: Optional timeout override
        
    Returns:
        Enhanced answer string, or base_answer if enrichment fails
    """
    # Check if Phi is available
    status = get_phi_status()
    if not status.get("available") or not status.get("enabled"):
        logger.debug("Phi LLM not available or disabled, returning base answer")
        return base_answer
    
    try:
        import requests
        
        endpoint, model_name, temperature, default_timeout = _get_phi_config()
        timeout = timeout_s if timeout_s is not None else default_timeout
        
        # Build agricultural enrichment prompt
        crop_context = f"about {crop_type} cultivation" if crop_type != "unknown" else "about farming"
        
        prompt = f"""You are an expert agricultural advisor helping farmers. Enhance this answer to be more practical and farmer-friendly.

Farmer's question: {question}

Current answer: {base_answer}

Context: This is {crop_context}

Instructions:
1. Keep all core information from the current answer
2. Add 1-2 practical tips or warnings specific to farming
3. Use friendly, empathetic language that farmers understand
4. Include specific measurements when helpful (liters, grams, days)
5. Mention timing if relevant (morning, evening, season)
6. Keep it concise (3-5 sentences)
7. Focus on actionable advice

Enhanced answer:"""

        # Call Phi LLM
        response = requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 400,  # Max 400 tokens for conciseness
                    "top_p": 0.9,
                }
            },
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            enriched = data.get("response", "").strip()
            
            if enriched and len(enriched) >= 50:  # Sanity check
                # Clean up common prefixes
                for prefix in ["Enhanced answer:", "Answer:", "Farmer-friendly answer:", "Response:", "Here's the enhanced version:"]:
                    if enriched.lower().startswith(prefix.lower()):
                        enriched = enriched[len(prefix):].strip()
                
                logger.info(f"✅ Successfully enriched answer with Phi LLM ({len(enriched)} chars)")
                return enriched
            else:
                logger.warning("Phi enrichment too short, using base answer")
                return base_answer
        else:
            logger.warning(f"Phi API error: {response.status_code}")
            return base_answer
            
    except Exception as e:
        logger.warning(f"Phi enrichment failed: {e}")
        return base_answer


# Initialize logging
logger.info("Phi LLM integration initialized with human-like personality")
logger.debug(f"Configuration: endpoint={_get_phi_config()[0]}, model={_get_phi_config()[1]}")
