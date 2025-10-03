#!/usr/bin/env python3
"""
Sample Data Generator for Testing Agricultural ML Pipeline
Creates synthetic sample images and metadata for testing the complete pipeline
"""

import os
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    """Generate sample agricultural images and metadata for testing"""
    
    def __init__(self, base_output_dir: str = "agricultural_ml_datasets"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
        # Disease categories
        self.diseases = [
            "leaf_spot", "rust", "powdery_mildew", "blight", "anthracnose",
            "downy_mildew", "black_rot", "fusarium_wilt", "bacterial_spot",
            "bacterial_blight", "bacterial_canker", "fire_blight", "bacterial_wilt",
            "mosaic_virus", "yellow_leaf_curl", "ring_spot", "leaf_roll", "streak_virus",
            "nitrogen_deficiency", "phosphorus_deficiency", "potassium_deficiency",
            "iron_deficiency", "magnesium_deficiency"
        ]
        
        # Weed categories
        self.weeds = [
            "dandelion", "plantain", "crabgrass", "foxtail", "yellow_nutsedge",
            "purple_nutsedge", "pigweed", "lambsquarters", "canada_thistle",
            "field_bindweed", "chickweed", "purslane"
        ]
        
        # Crops
        self.crops = [
            "tomato", "potato", "corn", "wheat", "rice", "grape", "apple",
            "citrus", "pepper", "cucumber", "bean", "rose"
        ]
        
        # Colors for different categories
        self.disease_colors = [
            (139, 69, 19), (205, 92, 92), (255, 215, 0), (144, 238, 144),
            (160, 82, 45), (255, 140, 0), (34, 139, 34), (255, 69, 0)
        ]
        
        self.weed_colors = [
            (255, 215, 0), (34, 139, 34), (255, 165, 0), (107, 142, 35),
            (192, 192, 192), (255, 20, 147), (128, 0, 128), (255, 105, 180)
        ]
    
    def create_sample_image(self, category: str, name: str, size: tuple = (400, 300)) -> Image.Image:
        """Create a sample image with text label"""
        # Choose color based on category
        if category == "disease":
            color = random.choice(self.disease_colors)
        elif category == "weed":
            color = random.choice(self.weed_colors)
        else:
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        
        # Create image
        img = Image.new('RGB', size, color)
        draw = ImageDraw.Draw(img)
        
        # Add text label
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"{category.upper()}\n{name.replace('_', ' ').title()}"
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # Draw text with shadow for better visibility
        draw.text((x+2, y+2), text, fill=(0, 0, 0), font=font, align='center')
        draw.text((x, y), text, fill=(255, 255, 255), font=font, align='center')
        
        return img
    
    def generate_disease_dataset(self, num_samples_per_disease: int = 3) -> Dict[str, Any]:
        """Generate sample disease dataset"""
        logger.info("🦠 Generating sample disease dataset...")
        
        output_dir = self.base_output_dir / "disease_images"
        output_dir.mkdir(exist_ok=True)
        
        metadata = []
        total_generated = 0
        
        for disease in self.diseases:
            for i in range(num_samples_per_disease):
                # Create sample image
                crop = random.choice(self.crops)
                severity = random.choice(["mild", "moderate", "severe"])
                
                filename = f"{disease}_{crop}_{severity}_{i+1}.jpg"
                filepath = output_dir / filename
                
                # Generate image
                img = self.create_sample_image("disease", f"{disease} {severity}")
                img.save(filepath, "JPEG", quality=85)
                
                # Create metadata
                metadata_entry = {
                    "filename": filename,
                    "disease_name": disease,
                    "crop": crop,
                    "severity": severity,
                    "category": "disease",
                    "subcategory": disease,
                    "source": "synthetic_generator",
                    "width": img.width,
                    "height": img.height,
                    "file_size": filepath.stat().st_size if filepath.exists() else 0,
                    "created_timestamp": "2025-09-14T14:16:00Z"
                }
                metadata.append(metadata_entry)
                total_generated += 1
        
        # Save metadata
        metadata_file = output_dir / "disease_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        result = {
            "total_collected": total_generated,
            "disease_count": len(self.diseases),
            "samples_per_disease": num_samples_per_disease,
            "output_directory": str(output_dir),
            "metadata_file": str(metadata_file)
        }
        
        logger.info(f"✅ Generated {total_generated} disease images")
        return result
    
    def generate_weed_dataset(self, num_samples_per_weed: int = 3) -> Dict[str, Any]:
        """Generate sample weed dataset"""
        logger.info("🌿 Generating sample weed dataset...")
        
        output_dir = self.base_output_dir / "weed_images"
        output_dir.mkdir(exist_ok=True)
        
        metadata = []
        total_generated = 0
        
        for weed in self.weeds:
            for i in range(num_samples_per_weed):
                # Create sample image
                growth_stage = random.choice(["seedling", "juvenile", "mature", "flowering"])
                
                filename = f"{weed}_{growth_stage}_{i+1}.jpg"
                filepath = output_dir / filename
                
                # Generate image
                img = self.create_sample_image("weed", f"{weed} {growth_stage}")
                img.save(filepath, "JPEG", quality=85)
                
                # Create metadata
                metadata_entry = {
                    "filename": filename,
                    "weed_name": weed,
                    "growth_stage": growth_stage,
                    "category": "weed",
                    "subcategory": weed,
                    "source": "synthetic_generator",
                    "width": img.width,
                    "height": img.height,
                    "file_size": filepath.stat().st_size if filepath.exists() else 0,
                    "created_timestamp": "2025-09-14T14:16:00Z"
                }
                metadata.append(metadata_entry)
                total_generated += 1
        
        # Save metadata
        metadata_file = output_dir / "weed_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        result = {
            "total_collected": total_generated,
            "weed_count": len(self.weeds),
            "samples_per_weed": num_samples_per_weed,
            "output_directory": str(output_dir),
            "metadata_file": str(metadata_file)
        }
        
        logger.info(f"✅ Generated {total_generated} weed images")
        return result
    
    def generate_general_dataset(self, num_samples: int = 10) -> Dict[str, Any]:
        """Generate sample general agricultural dataset"""
        logger.info("🌾 Generating sample general agricultural dataset...")
        
        output_dir = self.base_output_dir / "general_images"
        output_dir.mkdir(exist_ok=True)
        
        metadata = []
        total_generated = 0
        
        categories = [
            "crop_healthy", "field_equipment", "irrigation", "soil_analysis",
            "harvest", "planting", "pest_control", "fertilization"
        ]
        
        for i in range(num_samples):
            category = random.choice(categories)
            crop = random.choice(self.crops)
            
            filename = f"{category}_{crop}_{i+1}.jpg"
            filepath = output_dir / filename
            
            # Generate image
            img = self.create_sample_image("general", f"{category} {crop}")
            img.save(filepath, "JPEG", quality=85)
            
            # Create metadata
            metadata_entry = {
                "filename": filename,
                "category": "general",
                "subcategory": category,
                "crop": crop,
                "source": "synthetic_generator",
                "width": img.width,
                "height": img.height,
                "file_size": filepath.stat().st_size if filepath.exists() else 0,
                "created_timestamp": "2025-09-14T14:16:00Z"
            }
            metadata.append(metadata_entry)
            total_generated += 1
        
        # Save metadata
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        result = {
            "total_collected": total_generated,
            "categories": len(categories),
            "output_directory": str(output_dir),
            "metadata_file": str(metadata_file)
        }
        
        logger.info(f"✅ Generated {total_generated} general images")
        return result
    
    def generate_complete_sample_dataset(self, 
                                       disease_samples: int = 3,
                                       weed_samples: int = 3,
                                       general_samples: int = 10) -> Dict[str, Any]:
        """Generate complete sample dataset for testing"""
        logger.info("🎯 Generating complete sample dataset for testing...")
        
        results = {}
        
        # Generate all datasets
        results['disease'] = self.generate_disease_dataset(disease_samples)
        results['weed'] = self.generate_weed_dataset(weed_samples)
        results['general'] = self.generate_general_dataset(general_samples)
        
        total_images = (results['disease']['total_collected'] + 
                       results['weed']['total_collected'] + 
                       results['general']['total_collected'])
        
        summary = {
            "total_images": total_images,
            "disease_images": results['disease']['total_collected'],
            "weed_images": results['weed']['total_collected'],
            "general_images": results['general']['total_collected'],
            "output_directory": str(self.base_output_dir),
            "generated_for_testing": True
        }
        
        # Save summary
        summary_file = self.base_output_dir / "sample_dataset_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({**summary, **results}, f, indent=2)
        
        logger.info(f"🎯 Complete sample dataset generated: {total_images} images")
        return summary

def main():
    """Generate sample data for testing"""
    generator = SampleDataGenerator()
    
    result = generator.generate_complete_sample_dataset(
        disease_samples=3,
        weed_samples=3,
        general_samples=5
    )
    
    print("\n" + "="*60)
    print("🎯 SAMPLE DATASET GENERATION COMPLETE")
    print("="*60)
    print(f"📊 Total Images: {result['total_images']}")
    print(f"🦠 Disease Images: {result['disease_images']}")
    print(f"🌿 Weed Images: {result['weed_images']}")
    print(f"🌾 General Images: {result['general_images']}")
    print(f"📁 Output Directory: {result['output_directory']}")
    print("="*60)
    print("✅ Ready for pipeline testing!")

if __name__ == "__main__":
    main()