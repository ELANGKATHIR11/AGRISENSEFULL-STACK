"""
Ollama LLM integration for AgriSense chatbot.
Provides local LLM inference via Ollama API.

Supports:
- Answer reranking based on relevance scoring
- Agricultural domain-specific prompting
- Conversational chat completions
- Graceful fallback when Ollama unavailable

Environment Variables:
    OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
    OLLAMA_MODEL: Model name (default: phi)
                  Options: phi, mistral, neural-chat, tinyllama, llama2
    OLLAMA_TIMEOUT: Request timeout in seconds (default: 30)
    LLM_PROVIDER: Set to 'ollama' to use as primary LLM provider
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import List, Optional

logger = logging.getLogger(__name__)


def _get_ollama_config() -> tuple[str, str, int]:
    """Get Ollama configuration from environment variables."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "phi")
    timeout = int(os.getenv("OLLAMA_TIMEOUT", "30"))
    return base_url, model, timeout


def _extract_json(text: str) -> Optional[List[dict]]:
    """Extract JSON array from text response."""
    m = re.search(r"\[.*\]", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _rerank_prompt(question: str, candidates: List[str]) -> str:
    """Generate prompt for answer reranking."""
    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates))
    return (
        "You are ranking candidate agricultural answers for a user question.\n"
        "Rate each candidate from 0 (irrelevant) to 1 (perfect answer).\n"
        f"Question: {question}\n\n"
        "Candidates:\n"
        f"{numbered}\n\n"
        'Return JSON: [{"id": 1, "score": 0.9}, {"id": 2, "score": 0.3}, ...]'
    )


def _chat_completion_prompt(messages: List[dict]) -> str:
    """Convert chat messages to prompt format."""
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        prompt_parts.append(f"{role}: {content}")
    return "\n".join(prompt_parts) + "\nASSISTANT:"


def _is_ollama_available() -> bool:
    """Check if Ollama server is accessible."""
    try:
        import requests
        
        base_url, _, timeout = _get_ollama_config()
        response = requests.get(
            f"{base_url}/api/tags",
            timeout=timeout / 2  # Use half the timeout for health check
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Ollama availability check failed: {e}")
        return False


def rerank_with_ollama(
    question: str,
    candidates: List[str],
    timeout_s: float = None
) -> Optional[List[float]]:
    """
    Rerank candidate answers using Ollama local LLM.
    
    Args:
        question: The user question
        candidates: List of candidate answers to rerank
        timeout_s: Request timeout in seconds (uses config if None)
        
    Returns:
        List of relevance scores [0.0, 1.0] for each candidate, or None if failed
        
    Example:
        >>> scores = rerank_with_ollama(
        ...     "How to prevent rice blast?",
        ...     [
        ...         "Use resistant varieties",
        ...         "Apply fungicide",
        ...         "Reduce water"
        ...     ]
        ... )
        >>> print(scores)  # [0.95, 0.8, 0.6]
    """
    try:
        import requests
        
        if not candidates:
            return None
            
        base_url, model, config_timeout = _get_ollama_config()
        timeout = timeout_s or config_timeout
        
        # Check Ollama availability
        if not _is_ollama_available():
            logger.warning("Ollama server not available at {base_url}")
            return None
        
        # Generate reranking prompt
        prompt = _rerank_prompt(question, candidates)
        
        # Call Ollama API
        logger.debug(f"Reranking {len(candidates)} candidates with {model} model")
        t0 = time.time()
        
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.warning(f"Ollama API error: {response.status_code}")
            return None
        
        elapsed = time.time() - t0
        
        # Parse response
        data = response.json()
        response_text = data.get("response", "").strip()
        
        logger.debug(f"Ollama reranking completed in {elapsed:.2f}s")
        
        if elapsed > timeout * 0.8:
            logger.warning(f"Ollama response slow ({elapsed:.2f}s)")
        
        # Extract JSON array
        arr = _extract_json(response_text)
        if not arr:
            logger.debug(f"Could not extract JSON from response: {response_text[:100]}")
            return None
        
        # Convert to scores list
        scores = [0.0] * len(candidates)
        for item in arr:
            try:
                idx = int(item.get("id", 0)) - 1
                sc = float(item.get("score", 0.0))
                if 0 <= idx < len(scores):
                    scores[idx] = max(0.0, min(1.0, sc))
            except (ValueError, TypeError):
                continue
        
        logger.debug(f"Reranking scores: {scores}")
        return scores
        
    except ImportError:
        logger.warning("requests library not installed for Ollama support")
        return None
    except Exception as e:
        logger.debug(f"Ollama reranking failed: {e}")
        return None


def chat_with_ollama(
    messages: List[dict],
    temperature: float = 0.7,
    max_tokens: int = 500,
    timeout_s: float = None
) -> Optional[str]:
    """
    Generate chat completion using Ollama local LLM.
    
    Args:
        messages: List of chat messages with 'role' and 'content' keys
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        timeout_s: Request timeout in seconds
        
    Returns:
        Generated response text, or None if failed
        
    Example:
        >>> response = chat_with_ollama([
        ...     {"role": "system", "content": "You are an agricultural expert"},
        ...     {"role": "user", "content": "Tell me about crop rotation"}
        ... ])
        >>> print(response)
    """
    try:
        import requests
        
        if not messages:
            return None
        
        base_url, model, config_timeout = _get_ollama_config()
        timeout = timeout_s or config_timeout
        
        # Check Ollama availability
        if not _is_ollama_available():
            logger.warning(f"Ollama server not available at {base_url}")
            return None
        
        # Build prompt from messages
        prompt = _chat_completion_prompt(messages)
        
        logger.debug(f"Generating chat completion with {model} model")
        t0 = time.time()
        
        # Call Ollama API
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "top_k": 40,
                "top_p": 0.9,
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            logger.warning(f"Ollama API error: {response.status_code}")
            return None
        
        elapsed = time.time() - t0
        data = response.json()
        response_text = data.get("response", "").strip()
        
        logger.debug(f"Chat generation completed in {elapsed:.2f}s ({len(response_text)} chars)")
        
        return response_text
        
    except ImportError:
        logger.warning("requests library not installed for Ollama support")
        return None
    except Exception as e:
        logger.debug(f"Ollama chat failed: {e}")
        return None


def get_ollama_models() -> Optional[List[str]]:
    """
    Get list of available models on Ollama server.
    
    Returns:
        List of model names, or None if unavailable
    """
    try:
        import requests
        
        base_url, _, timeout = _get_ollama_config()
        response = requests.get(
            f"{base_url}/api/tags",
            timeout=timeout
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
        return list(set(models))  # Remove duplicates
        
    except Exception as e:
        logger.debug(f"Could not fetch Ollama models: {e}")
        return None


def ollama_status() -> dict:
    """
    Get status of Ollama integration.
    
    Returns:
        Dict with availability, model, and configuration info
    """
    base_url, model, timeout = _get_ollama_config()
    available = _is_ollama_available()
    models = get_ollama_models() if available else []
    
    return {
        "available": available,
        "base_url": base_url,
        "model": model,
        "timeout": timeout,
        "available_models": models,
        "provider": "ollama"
    }


# Initialize logging
logger.info("Ollama LLM client initialized")
logger.debug(f"Configuration: {_get_ollama_config()}")
