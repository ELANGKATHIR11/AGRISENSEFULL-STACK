"""
Vision Language Model (VLM) Module for AgriSense
Handles disease detection and weed management for 48 Indian crops
"""

from .vlm_engine import VLMEngine
from .crop_database import INDIAN_CROPS_DB, get_crop_info
from .disease_detector import DiseaseDetector
from .weed_detector import WeedDetector

__all__ = [
    'VLMEngine',
    'INDIAN_CROPS_DB',
    'get_crop_info',
    'DiseaseDetector',
    'WeedDetector',
]
