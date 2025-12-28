"""
AgriSense AI Core Module
========================

This module contains the GenAI-powered features for AgriSense:
- RAG-based chatbot for agricultural advice
- Vision-Language Model for crop disease and weed detection

Author: AgriSense Team
Date: December 2025
"""

from .rag_engine import FarmerAssistant
from .vision_engine import CropVisionAnalyst

__all__ = ["FarmerAssistant", "CropVisionAnalyst"]
