"""Lightweight response generation utilities for the chatbot."""

from __future__ import annotations

from typing import Dict

try:  # Optional heavy dependency (transformers/torch)
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - optional dependency
    AutoModelForCausalLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore


class TemplateResponseGenerator:
    """Template-based response generator used as the default fallback."""

    _TEMPLATES: Dict[str, str] = {
        "weather_inquiry": "The current weather conditions are ideal for {crop} cultivation.",
        "crop_advice": "Based on your soil conditions, I recommend planting {crop} this season.",
        "disease_help": "I've identified {problem} in your {crop}. Here's the treatment plan:",
        "irrigation_help": "Your {crop} needs watering. I recommend {water_amount} liters per square meter.",
        "general_help": "How can I assist you with your farming needs today?",
    }

    def generate_response(self, intent: str, entities: Dict[str, str]) -> str:
        response = self._TEMPLATES.get(intent, self._TEMPLATES["general_help"])
        for key, value in entities.items():
            response = response.replace(f"{{{key}}}", value)
        return response


class ResponseGenerator:
    """Neural response generator with graceful fallback to templates."""

    def __init__(self) -> None:
        self.template_generator = TemplateResponseGenerator()
        self.tokenizer = None
        self.model = None

        if AutoTokenizer is None or AutoModelForCausalLM is None or torch is None:
            # Heavy dependencies not available; stay in template mode
            return

        model_name = "microsoft/DialoGPT-medium"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
        except Exception:
            # If loading fails, keep fallback behaviour
            self.tokenizer = None
            self.model = None

    def generate(self, intent: str, entities: Dict[str, str], context: str = "") -> str:
        """Generate a response, preferring neural output when available."""

        if self.tokenizer is None or self.model is None:
            return self.template_generator.generate_response(intent, entities)

        prompt = context or self.template_generator.generate_response(intent, entities)
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=128,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.7,
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.strip() or self.template_generator.generate_response(intent, entities)
        except Exception:
            return self.template_generator.generate_response(intent, entities)
