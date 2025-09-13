#!/usr/bin/env python3
"""
Legacy compatibility module - redirects to train_plant_health_models_v2.py
This file exists to maintain compatibility with any existing references.
"""

# Import all functionality from the v2 version
from train_plant_health_models_v2 import *

# Explicitly re-export the main class
from train_plant_health_models_v2 import PlantHealthMLTrainer

__all__ = ['PlantHealthMLTrainer']

if __name__ == "__main__":
    print("⚠️  This is a compatibility shim. Please use train_plant_health_models_v2.py directly.")
    print("ℹ️  All functionality has been moved to the v2 version with enhanced features.")