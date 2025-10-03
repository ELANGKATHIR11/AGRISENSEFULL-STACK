"""Lightweight natural language understanding utilities for the chatbot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class IntentPattern:
    intent: str
    keywords: Tuple[str, ...]


class NLUService:
    """Simple intent recognition and entity extraction.

    This avoids heavy ML dependencies while providing deterministic behaviour
    suitable for an embedded FastAPI service.
    """

    _INTENT_PATTERNS: Tuple[IntentPattern, ...] = (
        IntentPattern("irrigation_help", ("water", "irrigat", "moisture", "dry")),
        IntentPattern("disease_help", ("disease", "fungus", "pest", "spot", "blight")),
        IntentPattern("fertilizer_advice", ("fertil", "nutrient", "manure", "npk")),
        IntentPattern("weather_inquiry", ("weather", "forecast", "rain", "temperature")),
        IntentPattern("general_help", ("help", "advice", "support", "guide")),
    )

    _CROP_KEYWORDS = (
        "rice",
        "wheat",
        "maize",
        "corn",
        "cotton",
        "soybean",
        "sugarcane",
        "millet",
        "paddy",
    )

    _PROBLEM_KEYWORDS = (
        "yellow",
        "brown",
        "wilting",
        "holes",
        "spots",
        "rust",
        "mold",
        "rot",
        "dry",
    )

    _QUANTITY_KEYWORDS = (
        "litre",
        "liter",
        "kg",
        "kilogram",
        "gram",
    )

    def recognize_intent(self, text: str) -> Tuple[str, float]:
        """Return (intent, confidence) for *text*."""

        lowered = text.lower()
        best_intent = "general_help"
        best_score = 0.0

        for pattern in self._INTENT_PATTERNS:
            score = sum(1 for kw in pattern.keywords if kw in lowered)
            if score > best_score:
                best_intent = pattern.intent
                best_score = score

        confidence = min(1.0, best_score / max(1, len(lowered.split())))
        return best_intent, confidence

    def extract_entities(self, text: str) -> Dict[str, str]:
        """Extract key entities from *text*.

        This is intentionally lightweight; it simply identifies common
        agricultural terms that help tailor template responses.
        """

        lowered = text.lower()
        tokens = lowered.split()
        entities: Dict[str, str] = {}

        for crop in self._CROP_KEYWORDS:
            if crop in tokens:
                entities["crop"] = crop
                break

        for problem in self._PROBLEM_KEYWORDS:
            if problem in tokens:
                entities["problem"] = problem
                break

        for qty in self._QUANTITY_KEYWORDS:
            if qty in tokens:
                entities["quantity_unit"] = qty
                break

        return entities
