"""
Optional LLM helpers for Gemini and DeepSeek.
Provides a single llm_rerank(question, candidates) API that returns a list of scores in [0,1].

Reads credentials from environment variables and fails gracefully when not configured.

Env:
    GEMINI_API_KEY, GEMINI_MODEL (default: gemini-1.5-flash)
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL (default: https://api.deepseek.com), DEEPSEEK_MODEL (default: deepseek-chat-v3-0324)
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import List, Optional


def _extract_json(text: str) -> Optional[List[dict]]:
    m = re.search(r"\[.*\]", text, flags=re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _prompt(question: str, candidates: List[str]) -> str:
    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(candidates))
    return (
        "You are ranking candidate answers for a user question.\n"
        f"Question: {question}\n\n"
        "Candidates (id: text):\n"
        f"{numbered}\n\n"
        'Return a JSON array of objects [{"id": <1-based id>, "score": <0..1>}], one per candidate.'
    )


def rerank_with_gemini(question: str, candidates: List[str], timeout_s: float = 6.0) -> Optional[List[float]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as generativeai  # type: ignore

        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        # The google.generativeai API may vary by installed version; call guarded
        configure_fn = getattr(generativeai, "configure", None)
        generate_fn = getattr(generativeai, "generate_content", None) or getattr(generativeai, "text", None)
        if configure_fn is None or generate_fn is None:
            # Unsupported installed version or API - bail gracefully
            return None
        configure_fn(api_key=api_key)
        p = _prompt(question, candidates)
        t0 = time.time()
        # Depending on API, generate_fn may be callable with different signatures
        try:
            resp = generate_fn(model=model_name, prompt=p)
        except TypeError:
            # Try alternative call form
            try:
                resp = generate_fn(prompt=p, model=model_name)
            except Exception:
                return None
        if time.time() - t0 > timeout_s:
            return None
        # For Gemini, the response text is in resp.text or resp.candidates[0].content.parts[0].text depending on version
        text = getattr(resp, "text", None)
        if not text and hasattr(resp, "candidates"):
            # Try to extract from candidates if present
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                text = ""
        text = (text or "").strip()
        arr = _extract_json(text)
        if not arr:
            return None
        scores = [0.0] * len(candidates)
        for item in arr:
            idx = int(item.get("id", 0)) - 1
            sc = float(item.get("score", 0.0))
            if 0 <= idx < len(scores):
                scores[idx] = max(0.0, min(1.0, sc))
        return scores
    except Exception:
        return None


def rerank_with_deepseek(question: str, candidates: List[str], timeout_s: float = 6.0) -> Optional[List[float]]:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI  # type: ignore

        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        # Prefer DeepSeek v3 naming if provided; fallback to legacy 'deepseek-chat'
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat-v3-0324")
        if not model:
            model = "deepseek-chat-v3-0324"
        client = OpenAI(api_key=api_key, base_url=base_url)
        p = _prompt(question, candidates)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise answer ranker."},
                {"role": "user", "content": p},
            ],
            temperature=0.2,
            max_tokens=300,
            timeout=timeout_s,
        )
        msg = resp.choices[0].message.content or ""
        arr = _extract_json(msg.strip())
        if not arr:
            return None
        scores = [0.0] * len(candidates)
        for item in arr:
            idx = int(item.get("id", 0)) - 1
            sc = float(item.get("score", 0.0))
            if 0 <= idx < len(scores):
                scores[idx] = max(0.0, min(1.0, sc))
        return scores
    except Exception:
        return None


def llm_rerank(question: str, candidates: List[str]) -> Optional[List[float]]:
    # Prefer Gemini; fallback to DeepSeek
    scores = rerank_with_gemini(question, candidates)
    if scores:
        return scores
    return rerank_with_deepseek(question, candidates)
