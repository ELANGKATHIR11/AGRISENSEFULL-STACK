#!/usr/bin/env python3
"""
Simplified Agricultural Data Collection Script
Collects sample training data for disease and weed detection models
"""

import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAgriDataCollector:
    """Simplified data collector for agricultural images"""
    
    def __init__(self, output_dir: str = "training_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "diseases").mkdir(exist_ok=True)
        (self.output_dir / "weeds").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Disease and weed lists
        self.diseases = [
            "tomato_early_blight", "tomato_late_blight", "corn_rust", "wheat_rust",
            "potato_blight", "apple_scab", "grape_downy_mildew", "rice_blast"
        ]
        
        self.weeds = [
            "dandelion", "crabgrass", "clover", "chickweed", "plantain",
            "lambsquarters", "pigweed", "foxtail"
        ]
    
    def create_sample_metadata(self):
        """Create sample metadata files for training"""
        logger.info("Creating sample metadata files...")
        
        # Disease metadata
        disease_metadata = {}
        for disease in self.diseases:
            disease_metadata[disease] = {
                "scientific_name": f"Sample {disease}",
                "symptoms": ["leaf spots", "wilting", "discoloration"],
                "treatments": ["fungicide", "cultural_controls"],
                "severity_levels": ["mild", "moderate", "severe"],
                "affected_crops": ["tomato", "corn", "wheat", "potato"],
                "environmental_factors": ["humidity", "temperature", "moisture"]
            }
        
        disease_file = self.output_dir / "metadata" / "disease_metadata.json"
        with open(disease_file, 'w') as f:
            json.dump(disease_metadata, f, indent=2)
        
        # Weed metadata
        weed_metadata = {}
        for weed in self.weeds:
            weed_metadata[weed] = {
                "scientific_name": f"Sample {weed}",
                "type": "broadleaf" if weed in ["dandelion", "clover", "chickweed"] else "grass",
                "season": "cool_season",
                "control_methods": ["herbicide", "mechanical", "cultural"],
                "herbicides": ["2,4-D", "glyphosate", "dicamba"],
                "growth_habit": "perennial" if weed in ["dandelion", "clover"] else "annual"
            }
        
        weed_file = self.output_dir / "metadata" / "weed_metadata.json"
        with open(weed_file, 'w') as f:
            json.dump(weed_metadata, f, indent=2)
        
        logger.info(f"Metadata files created in {self.output_dir}/metadata/")
    
    def create_sample_training_structure(self):
        """Create sample training directory structure"""
        logger.info("Creating sample training directory structure...")
        
        # Create class directories for diseases
        for disease in self.diseases:
            disease_dir = self.output_dir / "diseases" / disease
            disease_dir.mkdir(exist_ok=True)
            
            # Create sample info file
            info_file = disease_dir / "info.json"
            with open(info_file, 'w') as f:
                json.dump({
                    "class_name": disease,
                    "description": f"Sample {disease} for training",
                    "image_count": 0,
                    "data_sources": ["manual_collection"],
                    "last_updated": "2025-09-14"
                }, f, indent=2)
        
        # Create class directories for weeds
        for weed in self.weeds:
            weed_dir = self.output_dir / "weeds" / weed
            weed_dir.mkdir(exist_ok=True)
            
            # Create sample info file
            info_file = weed_dir / "info.json"
            with open(info_file, 'w') as f:
                json.dump({
                    "class_name": weed,
                    "description": f"Sample {weed} for training",
                    "image_count": 0,
                    "data_sources": ["manual_collection"],
                    "last_updated": "2025-09-14"
                }, f, indent=2)
        
        logger.info("Sample training structure created successfully!")
    
    def generate_sample_config(self):
        """Generate configuration file for training"""
        config = {
            "data_info": {
                "total_diseases": len(self.diseases),
                "total_weeds": len(self.weeds),
                "disease_classes": self.diseases,
                "weed_classes": self.weeds
            },
            "training_config": {
                "image_size": [224, 224],
                "batch_size": 16,
                "epochs": 50,
                "learning_rate": 0.001,
                "validation_split": 0.2,
                "augmentation": True
            },
            "model_config": {
                "disease_models": ["resnet50", "mobilenetv3", "vit_base"],
                "weed_models": ["deeplabv3", "resnet50", "mobilenetv3"],
                "output_dir": "trained_models"
            },
            "data_collection": {
                "status": "structure_created",
                "next_steps": [
                    "Add training images to class directories",
                    "Run data validation",
                    "Start model training"
                ]
            }
        }
        
        config_file = self.output_dir / "training_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Training configuration saved to {config_file}")
        return config
    
    def run_setup(self):
        """Run the complete setup process"""
        logger.info("🚀 Starting Agricultural Data Collection Setup")
        logger.info("=" * 60)
        
        try:
            # Create directory structure
            self.create_sample_training_structure()
            
            # Create metadata
            self.create_sample_metadata()
            
            # Generate configuration
            config = self.generate_sample_config()
            
            # Summary
            logger.info("=" * 60)
            logger.info("✅ DATA COLLECTION SETUP COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📁 Output directory: {self.output_dir.absolute()}")
            logger.info(f"🦠 Disease classes: {len(self.diseases)}")
            logger.info(f"🌿 Weed classes: {len(self.weeds)}")
            logger.info(f"📋 Metadata files: 2")
            logger.info(f"⚙️  Configuration: training_config.json")
            
            logger.info("\n📝 NEXT STEPS:")
            logger.info("1. Add training images to the class directories")
            logger.info("2. Validate the dataset structure")
            logger.info("3. Run the training pipeline")
            logger.info("4. Deploy trained models to the backend")
            
            return {
                "success": True,
                "output_dir": str(self.output_dir.absolute()),
                "disease_classes": len(self.diseases),
                "weed_classes": len(self.weeds),
                "config": config
            }
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """Main function"""
    collector = SimpleAgriDataCollector()
    result = collector.run_setup()
    
    if result["success"]:
        print("\n🎉 Ready to proceed with model training!")
        print("Run the training script when you have added training images.")
    else:
        print(f"\n❌ Setup failed: {result['error']}")

if __name__ == "__main__":
    main()