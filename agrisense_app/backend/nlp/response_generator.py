"""Template-based response generation for the chatbot."""

from __future__ import annotations

from typing import Dict


class ResponseGenerator:
    """Generates conversational responses using lightweight templates."""

    _TEMPLATES: Dict[str, str] = {
        "irrigation_help": (
            "For {crop} I recommend irrigating with adequate water. Monitor soil moisture"
            " and adjust watering schedule accordingly."),
        "disease_help": (
            "It sounds like your {crop} may have an issue. Inspect leaves and stems closely."
            " Consider removing affected areas and apply appropriate treatment."),
        "fertilizer_advice": (
            "Apply a balanced fertilizer for {crop}. Follow instructions on packaging"
            " and avoid over-application."),
        "weather_inquiry": (
            "Current guidance: check the local forecast for rainfall and temperature"
            " to plan field activities."),
        "general_help": (
            "Happy to assist with your farming questions. Provide more details about"
            " your crop and the challenge you face."),
    }

    def generate(self, intent: str, entities: Dict[str, str]) -> str:
        base = self._TEMPLATES.get(intent, self._TEMPLATES["general_help"])
        response = base
        for key, value in entities.items():
            response = response.replace(f"{{{key}}}", value)
        return response
