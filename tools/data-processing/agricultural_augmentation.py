#!/usr/bin/env python3
"""
Agricultural Image Data Augmentation Pipeline
Advanced augmentation system for plant disease and weed datasets
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, TYPE_CHECKING
import logging
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import albumentations as A
# Guard optional, heavy imports so this module is import-safe when ML libs aren't installed.
try:
    # Optional helper to convert to tensor when using Albumentations + PyTorch
    from albumentations.pytorch import ToTensorV2  # type: ignore
except Exception:
    ToTensorV2 = None  # type: ignore

try:
    import torch  # type: ignore
except Exception:
    torch = None  # type: ignore

try:
    from torchvision import transforms  # type: ignore
except Exception:
    transforms = None  # type: ignore

import matplotlib.pyplot as plt

if TYPE_CHECKING:  # help static type checkers know these names exist when analysing
    # These imports are only for type checking / IDE support and won't run at runtime
    try:  # pragma: no cover - type-check only
        import torch as _torch  # type: ignore
        from torchvision import transforms as _transforms  # type: ignore
        from albumentations.pytorch import ToTensorV2 as _ToTensorV2  # type: ignore
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgriculturalAugmentationPipeline:
    """Advanced augmentation pipeline for agricultural images"""
    
    def __init__(self, output_dir: str = "augmented_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Agriculture-specific augmentation parameters
        self.augmentation_config = {
            "basic_transforms": {
                "rotation_range": (-30, 30),
                "brightness_range": (0.7, 1.3),
                "contrast_range": (0.8, 1.2),
                "saturation_range": (0.8, 1.2),
                "hue_shift_range": (-20, 20),
                "blur_kernel_range": (1, 5)
            },
            "agricultural_specific": {
                "lighting_conditions": ["natural", "artificial", "shadow", "overcast"],
                "field_conditions": ["wet", "dry", "dusty", "clean"],
                "growth_stages": ["early", "middle", "late"],
                "seasonal_effects": ["spring", "summer", "fall", "winter"]
            },
            "augmentation_ratios": {
                "basic": 0.8,  # 80% chance for basic augmentations
                "advanced": 0.6,  # 60% chance for advanced augmentations
                "agricultural": 0.4  # 40% chance for agricultural-specific
            }
        }
        
        # Initialize augmentation pipelines
        self._setup_augmentation_pipelines()
        
        # Statistics
        self.augmentation_stats = {
            "original_images": 0,
            "augmented_images": 0,
            "augmentation_types": {},
            "failed_augmentations": 0
        }
    
    def _setup_augmentation_pipelines(self):
        """Setup different augmentation pipelines for various scenarios"""
        
        # Basic augmentation pipeline (Albumentations)
        self.basic_pipeline = A.Compose([
            A.RandomRotate90(p=0.5),
            A.Rotate(limit=30, p=0.7),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.2),
            A.RandomBrightnessContrast(
                brightness_limit=0.3, 
                contrast_limit=0.2, 
                p=0.7
            ),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=0.6
            ),
            A.OneOf([
                A.GaussianBlur(blur_limit=(1, 3), p=0.3),
                A.MotionBlur(blur_limit=(3, 7), p=0.3),
                A.MedianBlur(blur_limit=3, p=0.2)
            ], p=0.4),
            A.RandomResizedCrop(
                size=(224, 224),
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1),
                p=0.5
            )
        ])
        
        # Disease-specific augmentation
        self.disease_pipeline = A.Compose([  # type: ignore
            # Simulate different lighting conditions
            A.OneOf([
                A.RandomBrightnessContrast(brightness_limit=0.4, contrast_limit=0.3, p=1.0),
                A.RandomGamma(gamma_limit=(70, 130), p=1.0),
                A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=1.0)
            ], p=0.8),
            
            # Simulate field conditions
            A.OneOf([
                A.GaussNoise(p=1.0),  # Simulate dust/dirt
                A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=1.0),
                A.MultiplicativeNoise(multiplier=(0.9, 1.1), per_channel=True, p=1.0)
            ], p=0.6),
            
            # Simulate camera/imaging artifacts
            A.OneOf([
                A.ImageCompression(p=1.0),
                A.Downscale(p=1.0),
                A.Sharpen(alpha=(0.2, 0.5), lightness=(0.5, 1.0), p=1.0)
            ], p=0.4),
            
            # Color variations (different soil, background)
            A.ColorJitter(
                brightness=0.2,
                contrast=0.2,
                saturation=0.3,
                hue=0.1,
                p=0.7
            ),
            
            # Geometric transformations
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.2,
                rotate_limit=45,
                border_mode=cv2.BORDER_CONSTANT,
                p=0.7
            )
        ])  # type: ignore
        
        # Weed-specific augmentation
        self.weed_pipeline = A.Compose([
            # Simulate different growth densities
            A.RandomResizedCrop(
                size=(224, 224),
                scale=(0.6, 1.0),  # More aggressive cropping for weeds
                ratio=(0.8, 1.2),
                p=0.8
            ),
            
            # Simulate different field backgrounds
            A.OneOf([
                A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.2, p=1.0),
                A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=25, val_shift_limit=15, p=1.0)
            ], p=0.9),
            
            # Simulate overlapping vegetation
            A.OneOf([
                A.CoarseDropout(
                    num_holes_range=(1, 8), hole_height_range=(8, 32), hole_width_range=(8, 32),
                    p=1.0
                ),
                A.GridDropout(ratio=0.1, unit_size_range=(8, 16), p=1.0)
            ], p=0.3),
            
            # Different seasonal conditions
            A.OneOf([
                A.RandomFog(p=1.0),
                A.RandomRain(p=1.0),
                A.RandomSunFlare(p=1.0)
            ], p=0.2)
        ])
        
        # Severe augmentation for data scarce classes
        self.severe_pipeline = A.Compose([
            A.Rotate(limit=60, p=0.8),
            A.RandomBrightnessContrast(brightness_limit=0.5, contrast_limit=0.4, p=0.9),
            A.HueSaturationValue(hue_shift_limit=30, sat_shift_limit=40, val_shift_limit=30, p=0.8),
            A.OneOf([
                A.ElasticTransform(alpha=50, sigma=5, p=1.0),
                A.GridDistortion(num_steps=5, distort_limit=0.3, p=1.0),
                A.OpticalDistortion(distort_limit=0.2, p=1.0)
            ], p=0.6),
            A.OneOf([
                A.GaussNoise(p=1.0),
                A.ISONoise(color_shift=(0.02, 0.1), intensity=(0.2, 0.8), p=1.0)
            ], p=0.5),
            A.RandomResizedCrop(
                size=(224, 224),
                scale=(0.5, 1.0),
                ratio=(0.7, 1.3),
                p=0.9
            )
        ])
    
    def apply_agricultural_context_augmentation(self, image: np.ndarray, 
                                              context: Dict[str, str]) -> List[np.ndarray]:
        """Apply context-aware augmentations based on agricultural conditions"""
        augmented_images = []
        
        category = context.get('category', 'unknown')
        subcategory = context.get('subcategory', 'unknown')
        
        # Choose appropriate pipeline
        if category == 'disease':
            pipeline = self.disease_pipeline
        elif category == 'weed':
            pipeline = self.weed_pipeline
        else:
            pipeline = self.basic_pipeline
        
        # Apply base augmentations
        try:
            augmented = pipeline(image=image)['image']
            augmented_images.append(augmented)
            self.augmentation_stats['augmentation_types']['base'] = \
                self.augmentation_stats['augmentation_types'].get('base', 0) + 1
        except Exception as e:
            logger.error(f"Base augmentation failed: {e}")
            self.augmentation_stats['failed_augmentations'] += 1
        
        # Apply agricultural-specific augmentations
        agricultural_augs = self._get_agricultural_augmentations(context)
        for aug_name, aug_func in agricultural_augs.items():
            try:
                aug_image = aug_func(image)
                augmented_images.append(aug_image)
                self.augmentation_stats['augmentation_types'][aug_name] = \
                    self.augmentation_stats['augmentation_types'].get(aug_name, 0) + 1
            except Exception as e:
                logger.error(f"Agricultural augmentation {aug_name} failed: {e}")
                self.augmentation_stats['failed_augmentations'] += 1
        
        return augmented_images
    
    def _get_agricultural_augmentations(self, context: Dict[str, str]) -> Dict[str, Callable]:
        """Get agricultural-specific augmentation functions"""
        augmentations = {}
        
        # Lighting condition variations
        augmentations['artificial_lighting'] = lambda img: self._simulate_artificial_lighting(img)
        augmentations['shadow_conditions'] = lambda img: self._simulate_shadow_conditions(img)
        augmentations['overcast_lighting'] = lambda img: self._simulate_overcast_conditions(img)
        
        # Field condition variations
        augmentations['wet_conditions'] = lambda img: self._simulate_wet_conditions(img)
        augmentations['dusty_conditions'] = lambda img: self._simulate_dusty_conditions(img)
        
        # Seasonal variations
        augmentations['autumn_coloring'] = lambda img: self._simulate_autumn_conditions(img)
        augmentations['winter_conditions'] = lambda img: self._simulate_winter_conditions(img)
        
        # Camera/equipment variations
        augmentations['different_focus'] = lambda img: self._simulate_focus_variations(img)
        augmentations['motion_blur'] = lambda img: self._simulate_motion_blur(img)
        
        return augmentations
    
    def _simulate_artificial_lighting(self, image: np.ndarray) -> np.ndarray:
        """Simulate artificial lighting conditions"""
        # Add yellow/warm tint for artificial lighting
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 0] = np.clip(hsv[:, :, 0] + random.uniform(-10, 15), 0, 179)  # Hue shift to yellow
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * random.uniform(1.1, 1.3), 0, 255)  # Increase brightness
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def _simulate_shadow_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate shadow/partial lighting conditions"""
        # Create gradient shadow effect
        h, w = image.shape[:2]
        shadow_mask = np.ones((h, w), dtype=np.float32)
        
        # Random shadow direction
        if random.choice([True, False]):
            # Vertical shadow
            shadow_start = random.randint(0, w//3)
            shadow_end = random.randint(2*w//3, w)
            for i in range(shadow_start, shadow_end):
                shadow_mask[:, i] = 0.4 + 0.6 * (i - shadow_start) / (shadow_end - shadow_start)
        else:
            # Horizontal shadow
            shadow_start = random.randint(0, h//3)
            shadow_end = random.randint(2*h//3, h)
            for i in range(shadow_start, shadow_end):
                shadow_mask[i, :] = 0.4 + 0.6 * (i - shadow_start) / (shadow_end - shadow_start)
        
        # Apply shadow
        shadowed = image.astype(np.float32) * shadow_mask[:, :, np.newaxis]
        return np.clip(shadowed, 0, 255).astype(np.uint8)
    
    def _simulate_overcast_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate overcast/diffused lighting"""
        # Reduce contrast and add slight blue tint
        overcast = cv2.convertScaleAbs(image, alpha=0.8, beta=10)  # Reduce contrast
        hsv = cv2.cvtColor(overcast, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 0] = np.clip(hsv[:, :, 0] + random.uniform(5, 15), 0, 179)  # Blue tint
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 0.9, 0, 255)  # Reduce saturation
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def _simulate_wet_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate wet field conditions"""
        # Increase saturation and add slight reflection effect
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * random.uniform(1.2, 1.4), 0, 255)  # Increase saturation
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * random.uniform(1.05, 1.15), 0, 255)  # Slight brightness increase
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def _simulate_dusty_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate dusty field conditions"""
        # Add noise and reduce contrast
        dusty = image.astype(np.float32)
        noise = np.random.normal(0, random.uniform(5, 15), image.shape)
        dusty = dusty + noise
        dusty = np.clip(dusty, 0, 255)
        
        # Reduce contrast (dusty effect)
        dusty = cv2.convertScaleAbs(dusty, alpha=0.9, beta=5)
        return dusty.astype(np.uint8)
    
    def _simulate_autumn_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate autumn coloring"""
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        # Shift towards orange/red hues
        hsv[:, :, 0] = np.clip(hsv[:, :, 0] + random.uniform(-30, -10), 0, 179)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * random.uniform(1.1, 1.3), 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def _simulate_winter_conditions(self, image: np.ndarray) -> np.ndarray:
        """Simulate winter conditions"""
        # Desaturate and add cool tint
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 0] = np.clip(hsv[:, :, 0] + random.uniform(10, 30), 0, 179)  # Cool tint
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * random.uniform(0.6, 0.8), 0, 255)  # Desaturate
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * random.uniform(1.1, 1.2), 0, 255)  # Increase brightness
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def _simulate_focus_variations(self, image: np.ndarray) -> np.ndarray:
        """Simulate different focus conditions"""
        # Apply slight gaussian blur
        kernel_size = random.choice([3, 5, 7])
        sigma = random.uniform(0.5, 2.0)
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)
    
    def _simulate_motion_blur(self, image: np.ndarray) -> np.ndarray:
        """Simulate motion blur"""
        # Create motion blur kernel
        size = random.choice([5, 7, 9, 11])
        kernel = np.zeros((size, size))
        kernel[int((size-1)/2), :] = np.ones(size)
        kernel = kernel / size
        
        # Apply blur
        return cv2.filter2D(image, -1, kernel)
    
    def calculate_augmentation_strategy(self, metadata: Dict[str, Any]) -> Dict[str, int]:
        """Calculate optimal augmentation strategy based on dataset statistics"""
        logger.info("📊 Calculating augmentation strategy...")
        
        # Analyze class distribution from all splits
        class_counts = {}
        
        # Process each split (train, val, test)
        for split_name, split_data in metadata.items():
            if isinstance(split_data, dict) and 'files' in split_data:
                for item in split_data['files']:
                    category = item.get('category', 'unknown')
                    subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
                    class_key = f"{category}_{subcategory}"
                    class_counts[class_key] = class_counts.get(class_key, 0) + 1
        
        # Fallback: try old format
        if not class_counts:
            for item in metadata.get('valid_files', []):
                category = item.get('category', 'unknown')
                subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
                class_key = f"{category}_{subcategory}"
                class_counts[class_key] = class_counts.get(class_key, 0) + 1
        
        if not class_counts:
            logger.warning("No class data found for augmentation strategy")
            return {}
        
        logger.info(f"🔍 Found {len(class_counts)} classes for augmentation:")
        for class_key, count in sorted(class_counts.items()):
            logger.info(f"   {class_key}: {count} images")
        
        # Calculate target size (median of top 75% classes)
        sorted_counts = sorted(class_counts.values(), reverse=True)
        top_75_count = int(len(sorted_counts) * 0.75)
        target_size = max(3, int(np.median(sorted_counts[:max(1, top_75_count)])))  # Minimum 3 images per class
        
        # Calculate augmentation multipliers
        augmentation_strategy = {}
        for class_key, count in class_counts.items():
            if count < target_size:
                multiplier = min(5, max(1, target_size // count))  # Cap at 5x augmentation
                augmentation_strategy[class_key] = multiplier
            else:
                augmentation_strategy[class_key] = 1  # No augmentation needed
        
        logger.info(f"🎯 Target size: {target_size} images per class")
        logger.info(f"📈 Classes needing augmentation: {sum(1 for m in augmentation_strategy.values() if m > 1)}")
        
        return augmentation_strategy
    
    def augment_dataset(self, dataset_dir: str, metadata_file: str, 
                       strategy: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Augment complete dataset based on strategy"""
        logger.info("🔄 Starting dataset augmentation...")
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Calculate strategy if not provided
        if strategy is None:
            strategy = self.calculate_augmentation_strategy(metadata)
        
        # Process each image
        dataset_path = Path(dataset_dir)
        augmented_count = 0
        
        for item in metadata.get('valid_files', []):
            self.augmentation_stats['original_images'] += 1
            
            # Determine class and multiplier
            category = item.get('category', 'unknown')
            subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
            class_key = f"{category}_{subcategory}"
            multiplier = strategy.get(class_key, 1)
            
            if multiplier <= 1:
                continue  # No augmentation needed
            
            # Load original image
            image_path = dataset_path / item.get('organized_path', item.get('filename', ''))
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}")
                continue
            
            try:
                image = cv2.imread(str(image_path))
                if image is not None:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    print(f"Warning: Could not load image {image_path}")
                    continue
                
                # Create augmented versions
                context = {
                    'category': category,
                    'subcategory': subcategory,
                    'original_path': str(image_path)
                }
                
                augmented_images = self.apply_agricultural_context_augmentation(image, context)
                
                # Save augmented images
                aug_dir = self.output_dir / "augmented" / category / subcategory
                aug_dir.mkdir(parents=True, exist_ok=True)
                
                base_name = image_path.stem
                for i, aug_image in enumerate(augmented_images[:multiplier-1]):  # -1 because original exists
                    aug_filename = f"{base_name}_aug_{i+1}.jpg"
                    aug_path = aug_dir / aug_filename
                    
                    # Convert back to BGR for saving
                    aug_bgr = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(str(aug_path), aug_bgr)
                    
                    augmented_count += 1
                    self.augmentation_stats['augmented_images'] += 1
                
                if augmented_count % 100 == 0:
                    logger.info(f"🔄 Augmented {augmented_count} images...")
                
            except Exception as e:
                logger.error(f"Failed to augment {image_path}: {e}")
                self.augmentation_stats['failed_augmentations'] += 1
        
        # Save augmentation metadata
        aug_metadata = {
            'strategy': strategy,
            'statistics': self.augmentation_stats,
            'config': self.augmentation_config
        }
        
        aug_metadata_path = self.output_dir / "augmentation_metadata.json"
        with open(aug_metadata_path, 'w') as f:
            json.dump(aug_metadata, f, indent=2)
        
        results = {
            'total_augmented': augmented_count,
            'original_images': self.augmentation_stats['original_images'],
            'failed_augmentations': self.augmentation_stats['failed_augmentations'],
            'output_dir': str(self.output_dir)
        }
        
        logger.info(f"✅ Augmentation complete: {augmented_count} new images created")
        return results
    
    def create_preview_grid(self, original_image: np.ndarray, 
                           augmented_images: List[np.ndarray]) -> np.ndarray:
        """Create a preview grid showing original and augmented images"""
        n_images = min(len(augmented_images) + 1, 9)  # Original + up to 8 augmented
        grid_size = int(np.ceil(np.sqrt(n_images)))
        
        # Resize all images to same size
        target_size = (224, 224)
        original_resized = cv2.resize(original_image, target_size)
        augmented_resized = [cv2.resize(img, target_size) for img in augmented_images[:n_images-1]]
        
        # Create grid
        grid = np.zeros((grid_size * target_size[0], grid_size * target_size[1], 3), dtype=np.uint8)
        
        # Place original image at top-left
        grid[:target_size[0], :target_size[1]] = original_resized
        
        # Place augmented images
        for i, aug_img in enumerate(augmented_resized):
            row = (i + 1) // grid_size
            col = (i + 1) % grid_size
            y_start = row * target_size[0]
            y_end = y_start + target_size[0]
            x_start = col * target_size[1]
            x_end = x_start + target_size[1]
            grid[y_start:y_end, x_start:x_end] = aug_img
        
        return grid

def main():
    """Main execution"""
    augmenter = AgriculturalAugmentationPipeline()
    
    # Example usage
    results = augmenter.augment_dataset(
        dataset_dir="organized_agricultural_datasets",
        metadata_file="organized_agricultural_datasets/organized_metadata.json"
    )
    
    print("\n" + "="*60)
    print("🔄 DATASET AUGMENTATION COMPLETE")
    print("="*60)
    print(f"📸 Original Images: {results['original_images']}")
    print(f"🔄 Augmented Images: {results['total_augmented']}")
    print(f"❌ Failed Augmentations: {results['failed_augmentations']}")
    print(f"📁 Output: {results['output_dir']}")
    print("="*60)

if __name__ == "__main__":
    main()