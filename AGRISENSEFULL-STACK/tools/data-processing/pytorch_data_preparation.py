#!/usr/bin/env python3
"""
PyTorch Training Data Preparation System
Creates optimized PyTorch datasets and dataloaders for agricultural image training
"""

import os
import json
# Make heavy ML libs lazy-imported at runtime. For static analysis and
# to allow lightweight environments, expose simple placeholders here.
TORCH_AVAILABLE = False
torch = None  # type: ignore
nn = None  # type: ignore
# Use typing.Any placeholders so the static analyzer accepts later calls
from typing import Any as _Any
Dataset: _Any = object
DataLoader: _Any = list
WeightedRandomSampler: _Any = None
transforms = None
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, TYPE_CHECKING
import logging
from PIL import Image
import pandas as pd
import numpy as np
import cv2
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from typing import cast
try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
    A_AVAILABLE = True
except Exception:
    A = None  # type: ignore
    ToTensorV2 = None  # type: ignore
    A_AVAILABLE = False

# Provide a lightweight proxy so static analyzers and attribute lookups in
# the module don't fail when albumentations isn't installed; attempts to use
# actual augmentation functions will raise at runtime with a clear message.
if not A_AVAILABLE:
    class _AlbumentationsProxy:
        def __getattr__(self, name):
            def _missing(*args, **kwargs):
                raise RuntimeError(
                    f"Albumentations is not installed; attempted to access '{name}'. "
                    "Install 'albumentations[imgaug]' and 'albumentations.pytorch' to use transforms."
                )
            return _missing
    A = _AlbumentationsProxy()  # type: ignore
    # Hint to static analyzer that `A` can be any type at runtime
    from typing import Any as _Any
    A: _Any = A

if TYPE_CHECKING:
    # Help static analyzers find types without importing heavy runtime deps
    # These imports are for type checking only and won't execute at runtime
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    from torch.utils.data import Dataset as TorchDataset, DataLoader as TorchDataLoader, WeightedRandomSampler as TorchWeightedRandomSampler  # type: ignore
    import torchvision.transforms as tv_transforms  # type: ignore
    import albumentations as alb  # type: ignore
    from albumentations.pytorch import ToTensorV2 as TT2  # type: ignore

# Configure logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import Any as _Any
DatasetBase: _Any = Dataset if TORCH_AVAILABLE else object


class AgriculturalDataset(DatasetBase):
    """PyTorch Dataset for agricultural images (diseases and weeds)"""
    
    def __init__(self, 
                 data_dir: str,
                 metadata: List[Dict[str, Any]],
                 split: str = 'train',
                 transform: Optional[Any] = None,
                 target_size: Tuple[int, int] = (224, 224),
                 num_classes: Optional[int] = None):
        # Store basic fields
        self.data_dir = Path(data_dir) if isinstance(data_dir, (str, Path)) else Path('.')
        self.metadata = metadata
        self.split = split
        self.transform = transform
        self.target_size = target_size
        
        # Create label mappings
        self.class_to_idx, self.idx_to_class = self._create_class_mappings()
        self.num_classes = num_classes or len(self.class_to_idx)
        
        # Filter metadata for this split
        self.samples = self._filter_samples()
        
        logger.info(f"📊 {split.upper()} dataset: {len(self.samples)} samples, {self.num_classes} classes")
    
    def _create_class_mappings(self) -> Tuple[Dict[str, int], Dict[int, str]]:
        """Create class to index mappings"""
        classes = set()
        for item in self.metadata:
            # Get class name from various possible fields
            class_name = (item.get('subcategory') or 
                         item.get('disease_name') or 
                         item.get('weed_name') or 
                         item.get('class_name', 'unknown'))
            classes.add(class_name)
        
        classes = sorted(list(classes))
        class_to_idx = {cls: idx for idx, cls in enumerate(classes)}
        idx_to_class = {idx: cls for cls, idx in class_to_idx.items()}
        
        return class_to_idx, idx_to_class
    
    def _filter_samples(self) -> List[Dict[str, Any]]:
        """Filter samples for current split"""
        samples = []
        for item in self.metadata:
            # Check if item belongs to current split
            split_path_key = f"{self.split}_path"
            if split_path_key in item and item[split_path_key]:
                samples.append(item)
            elif self.split == 'train' and 'organized_path' in item:
                # Fallback: if no split paths, assume organized_path is for training
                samples.append(item)
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[Any, int, Dict[str, Any]]:
        """Get item by index"""
        item = self.samples[idx]
        
        # Get image path
        image_path = self._get_image_path(item)
        
        # Load image
        try:
            image = self._load_image(image_path)
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            # Return a black image as fallback
            image = np.zeros((self.target_size[0], self.target_size[1], 3), dtype=np.uint8)
        
        # Apply transforms
        if self.transform:
            if hasattr(self.transform, '__module__') and 'albumentations' in str(self.transform.__module__):
                # Albumentations transform
                transformed = self.transform(image=image)
                image = transformed['image']
            else:
                # Torchvision transform (convert to PIL first)
                pil_image = Image.fromarray(image)
                image = self.transform(pil_image)
        else:
            # Default: convert to tensor
            if TORCH_AVAILABLE and torch is not None:
                image = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0
            else:
                # Return numpy array when torch is not available
                image = image.transpose(2, 0, 1).astype(np.float32) / 255.0
        
        # Get label
        class_name = (item.get('subcategory') or 
                     item.get('disease_name') or 
                     item.get('weed_name') or 
                     item.get('class_name', 'unknown'))
        label = self.class_to_idx.get(class_name, 0)
        
        # Additional metadata
        metadata = {
            'image_path': str(image_path),
            'class_name': class_name,
            'category': item.get('category', 'unknown'),
            'source': item.get('source', 'unknown')
        }
        
        return image, label, metadata
    
    def _get_image_path(self, item: Dict[str, Any]) -> Path:
        """Get image path for item"""
        # Try split-specific path first
        split_path_key = f"{self.split}_path"
        if split_path_key in item and item[split_path_key]:
            return self.data_dir / item[split_path_key]
        
        # Fallback to organized path
        if 'organized_path' in item:
            return self.data_dir / item['organized_path']
        
        # Last resort: try filename
        if 'filename' in item:
            return self.data_dir / item['filename']
        
        raise ValueError(f"Cannot determine image path for item: {item}")
    
    def _load_image(self, image_path: Path) -> np.ndarray:
        """Load and preprocess image"""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load with OpenCV
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        if image.shape[:2] != self.target_size:
            image = cv2.resize(image, (self.target_size[1], self.target_size[0]))
        
        return image
    
    def get_class_weights(self) -> Any:
        """Calculate class weights for balanced training"""
        class_counts = Counter()
        for item in self.samples:
            class_name = (item.get('subcategory') or 
                         item.get('disease_name') or 
                         item.get('weed_name') or 
                         item.get('class_name', 'unknown'))
            class_counts[class_name] += 1
        
        # Calculate inverse frequency weights
        total_samples = len(self.samples)
        weights = []
        for cls in self.idx_to_class.values():
            count = class_counts.get(cls, 1)
            weight = total_samples / (len(self.class_to_idx) * count)
            weights.append(weight)
        
        if TORCH_AVAILABLE and torch is not None:
            return torch.FloatTensor(weights)
        # Fallback to numpy array
        return np.array(weights, dtype=np.float32)
    
    def get_sample_weights(self) -> List[float]:
        """Get sample weights for WeightedRandomSampler"""
        class_weights = self.get_class_weights()
        sample_weights = []
        
        for item in self.samples:
            class_name = (item.get('subcategory') or 
                         item.get('disease_name') or 
                         item.get('weed_name') or 
                         item.get('class_name', 'unknown'))
            class_idx = self.class_to_idx.get(class_name, 0)
            sample_weights.append(class_weights[class_idx].item())
        
        return sample_weights

class TransformFactory:
    """Factory for creating image transforms"""
    @staticmethod
    def get_train_transforms(image_size: int = 224,
                            augmentation_level: str = 'medium') -> Any:
        """Get training transforms with augmentation

        Returns an Albumentations Compose object when available, otherwise raises.
        """
        if not A_AVAILABLE or ToTensorV2 is None:
            raise RuntimeError("Albumentations and ToTensorV2 are required for the TransformFactory. Install 'albumentations[imgaug]' and 'albumentations.pytorch'.")

        if augmentation_level == 'light':
            aug = [
                A.Resize(image_size, image_size),
                A.HorizontalFlip(p=0.5),
                A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2()
            ]
        elif augmentation_level == 'medium':
            aug = [
                A.Resize(image_size, image_size),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.2),
                A.RandomRotate90(p=0.5),
                A.Rotate(limit=30, p=0.7),
                A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
                A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30, val_shift_limit=20, p=0.6),
                A.OneOf([
                    A.GaussianBlur(blur_limit=(1, 3), p=0.3),
                    A.MotionBlur(blur_limit=(3, 7), p=0.3),
                ], p=0.3),
                A.RandomResizedCrop(size=(image_size, image_size), scale=(0.8, 1.0), p=0.5),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2()
            ]
        elif augmentation_level == 'heavy':
            aug = [
                A.Resize(image_size, image_size),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.3),
                A.RandomRotate90(p=0.5),
                A.Rotate(limit=45, p=0.8),
                A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.8),
                A.HueSaturationValue(hue_shift_limit=25, sat_shift_limit=35, val_shift_limit=25, p=0.7),
                A.OneOf([
                    A.GaussianBlur(blur_limit=(1, 5), p=0.4),
                    A.MotionBlur(blur_limit=(3, 9), p=0.4),
                    A.MedianBlur(blur_limit=3, p=0.2),
                ], p=0.4),
                A.RandomResizedCrop(size=(image_size, image_size), scale=(0.7, 1.0), p=0.6),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2()
            ]
        else:
            raise ValueError(f"Unknown augmentation level: {augmentation_level}")

        return A.Compose(aug)  # type: ignore[attr-defined]

    @staticmethod
    def get_val_transforms(image_size: int = 224) -> Any:
        """Get validation/test transforms (no augmentation)"""
        if not A_AVAILABLE or ToTensorV2 is None:
            raise RuntimeError("Albumentations and ToTensorV2 are required for validation transforms.")

        return A.Compose([  # type: ignore[attr-defined]
            A.Resize(image_size, image_size),
            A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            ToTensorV2()
        ])

class DataLoaderFactory:
    """Factory for creating optimized data loaders"""
    
    @staticmethod
    def create_loaders(
        data_dir: str,
        metadata_file: str,
        batch_size: int = 32,
        image_size: int = 224,
        num_workers: int = 4,
        augmentation_level: str = 'medium',
        use_weighted_sampling: bool = True,
        pin_memory: bool = True
    ) -> Tuple[Any, Any, Any, Dict[str, Any]]:
        """Create train, validation, and test data loaders"""
        
        logger.info("🔧 Creating data loaders...")
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Get split metadata
        if 'train' in metadata:
            # Split metadata format
            train_metadata = metadata['train']['files']
            val_metadata = metadata['val']['files']
            test_metadata = metadata['test']['files']
        else:
            # Combined metadata format - need to split
            all_files = metadata.get('valid_files', [])
            # Simple split for demo (you might want more sophisticated splitting)
            train_size = int(0.7 * len(all_files))
            val_size = int(0.15 * len(all_files))
            
            train_metadata = all_files[:train_size]
            val_metadata = all_files[train_size:train_size + val_size]
            test_metadata = all_files[train_size + val_size:]
        
        # Ensure required libs are available
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch and torchvision are required to create data loaders. Install torch and torchvision in the environment.")

        # Create transforms
        transform_factory = TransformFactory()
        train_transform = transform_factory.get_train_transforms(image_size, augmentation_level)
        val_transform = transform_factory.get_val_transforms(image_size)
        
        # Create datasets
        train_dataset = AgriculturalDataset(
            data_dir=data_dir,
            metadata=train_metadata,
            split='train',
            transform=train_transform,
            target_size=(image_size, image_size)
        )
        
        val_dataset = AgriculturalDataset(
            data_dir=data_dir,
            metadata=val_metadata,
            split='val',
            transform=val_transform,
            target_size=(image_size, image_size),
            num_classes=train_dataset.num_classes
        )
        
        test_dataset = AgriculturalDataset(
            data_dir=data_dir,
            metadata=test_metadata,
            split='test',
            transform=val_transform,
            target_size=(image_size, image_size),
            num_classes=train_dataset.num_classes
        )
        
        # Create samplers
        train_sampler = None
        if use_weighted_sampling and len(train_dataset) > 0:
            sample_weights = train_dataset.get_sample_weights()
            train_sampler = WeightedRandomSampler(
                sample_weights,
                len(sample_weights),
                True
            )
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=(train_sampler is None),
            sampler=train_sampler,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory
        )
        
        # Compile dataset info
        dataset_info = {
            'num_classes': train_dataset.num_classes,
            'class_to_idx': train_dataset.class_to_idx,
            'idx_to_class': train_dataset.idx_to_class,
            'train_size': len(train_dataset),
            'val_size': len(val_dataset),
            'test_size': len(test_dataset),
            'class_weights': train_dataset.get_class_weights().tolist(),
            'image_size': image_size,
            'batch_size': batch_size
        }
        
        logger.info(f"✅ Data loaders created:")
        logger.info(f"   📚 Train: {len(train_dataset)} samples")
        logger.info(f"   🔍 Val: {len(val_dataset)} samples") 
        logger.info(f"   🧪 Test: {len(test_dataset)} samples")
        logger.info(f"   🏷️  Classes: {train_dataset.num_classes}")
        
        return train_loader, val_loader, test_loader, dataset_info

def create_dataset_analysis(dataset_info: Dict[str, Any], 
                           output_dir: str = "dataset_analysis") -> None:
    """Create comprehensive dataset analysis"""
    logger.info("📊 Creating dataset analysis...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    try:
        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Agricultural Dataset Analysis', fontsize=16, fontweight='bold')
        
        # 1. Dataset split distribution
        ax1 = axes[0, 0]
        splits = ['Train', 'Validation', 'Test']
        sizes = [dataset_info['train_size'], dataset_info['val_size'], dataset_info['test_size']]
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        ax1.pie(sizes, labels=splits, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Dataset Split Distribution')
        
        # 2. Class distribution (top 20 classes)
        ax2 = axes[0, 1]
        class_names = cast(List[str], list(dataset_info.get('idx_to_class', {}).values()))
        class_weights = cast(List[float], dataset_info.get('class_weights', []))
        
        # Convert weights to approximate counts (inverse relationship)
        total_samples = dataset_info['train_size']
        approx_counts = [total_samples / (len(class_weights) * w) for w in class_weights]
        
        # Show top 20 classes
        class_data = list(zip(class_names, approx_counts))
        class_data.sort(key=lambda x: x[1], reverse=True)
        top_classes = class_data[:20]
        
        if top_classes:
            top_names = [str(x[0])[:15] for x in top_classes]  # Truncate long names
            top_counts = [float(x[1]) for x in top_classes]
            
            bars = ax2.barh(range(len(top_names)), top_counts)
            ax2.set_yticks(range(len(top_names)))
            ax2.set_yticklabels(top_names)
            ax2.set_xlabel('Approximate Sample Count')
            ax2.set_title('Top 20 Classes by Sample Count')
            ax2.invert_yaxis()
        
        # 3. Class weights distribution
        ax3 = axes[1, 0]
        ax3.hist(class_weights, bins=30, alpha=0.7, color='#9b59b6')
        ax3.set_xlabel('Class Weight')
        ax3.set_ylabel('Number of Classes')
        ax3.set_title('Class Weights Distribution')
        ax3.axvline(np.mean(class_weights), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(class_weights):.2f}')
        ax3.legend()
        
        # 4. Dataset statistics
        ax4 = axes[1, 1]
        stats_text = f"""
Dataset Statistics:
Total Classes: {dataset_info['num_classes']}
Total Samples: {sum(sizes):,}
Image Size: {dataset_info['image_size']}×{dataset_info['image_size']}
Batch Size: {dataset_info['batch_size']}

Split Ratios:
Train: {sizes[0]/sum(sizes)*100:.1f}%
Val: {sizes[1]/sum(sizes)*100:.1f}%
Test: {sizes[2]/sum(sizes)*100:.1f}%

Class Balance:
Min Weight: {min(class_weights):.3f}
Max Weight: {max(class_weights):.3f}
Weight Ratio: {max(class_weights)/min(class_weights):.1f}:1
        """.strip()
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Dataset Statistics')
        
        plt.tight_layout()
        
        # Save plot
        plot_path = output_path / "dataset_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save dataset info as JSON
        info_path = output_path / "dataset_info.json"
        with open(info_path, 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        logger.info(f"📊 Analysis saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to create dataset analysis: {e}")

def main():
    """Main execution for testing"""
    # Example usage
    try:
        train_loader, val_loader, test_loader, dataset_info = DataLoaderFactory.create_loaders(
            data_dir="organized_agricultural_datasets",
            metadata_file="organized_agricultural_datasets/split_metadata.json",
            batch_size=16,
            image_size=224,
            augmentation_level='medium'
        )
        
        # Create analysis
        create_dataset_analysis(dataset_info)
        
        # Test loading a batch
        logger.info("🧪 Testing data loading...")
        for batch_idx, (images, labels, metadata) in enumerate(train_loader):
            logger.info(f"Batch {batch_idx}: {images.shape}, Labels: {labels.shape}")
            if batch_idx >= 2:  # Test first 3 batches
                break
        
        print("\n" + "="*60)
        print("🎯 PYTORCH TRAINING DATA PREPARATION COMPLETE")
        print("="*60)
        print(f"📚 Training samples: {dataset_info['train_size']}")
        print(f"🔍 Validation samples: {dataset_info['val_size']}")
        print(f"🧪 Test samples: {dataset_info['test_size']}")
        print(f"🏷️  Number of classes: {dataset_info['num_classes']}")
        print(f"📐 Image size: {dataset_info['image_size']}×{dataset_info['image_size']}")
        print(f"📦 Batch size: {dataset_info['batch_size']}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to create data loaders: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()