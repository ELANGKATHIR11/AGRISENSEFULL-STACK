#!/usr/bin/env python3
"""
Dataset Organization and Validation System
Organizes, validates, and structures collected agricultural images for ML training
"""

import os
import json
import shutil
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from PIL import Image, ImageStat
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import cv2
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetOrganizer:
    """Organizes and validates agricultural image datasets"""
    
    def __init__(self, input_dir: str, output_dir: str = "organized_datasets"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Quality thresholds (relaxed for synthetic/sample data)
        self.min_resolution = (100, 100)  # Reduced from 224x224
        self.max_resolution = (4096, 4096)
        self.min_file_size = 1000  # Reduced from 5KB
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.min_brightness = 10  # Reduced from 20
        self.max_brightness = 245  # Increased from 235
        self.min_contrast = 5  # Reduced from 10
        
        # Statistics
        self.validation_stats = {
            "total_images": 0,
            "valid_images": 0,
            "invalid_images": 0,
            "duplicates_removed": 0,
            "issues": defaultdict(int)
        }
        
        self.image_hashes = set()
        
    def validate_image_quality(self, image_path: Path) -> Tuple[bool, List[str]]:
        """Validate individual image quality"""
        issues = []
        
        try:
            # Check file size
            file_size = image_path.stat().st_size
            if file_size < self.min_file_size:
                issues.append(f"File too small: {file_size} bytes")
            elif file_size > self.max_file_size:
                issues.append(f"File too large: {file_size} bytes")
            
            # Open and validate image
            with Image.open(image_path) as img:
                # Check resolution
                width, height = img.size
                if width < self.min_resolution[0] or height < self.min_resolution[1]:
                    issues.append(f"Resolution too low: {width}x{height}")
                elif width > self.max_resolution[0] or height > self.max_resolution[1]:
                    issues.append(f"Resolution too high: {width}x{height}")
                
                # Check if grayscale or color
                if img.mode not in ['RGB', 'RGBA', 'L']:
                    issues.append(f"Unsupported image mode: {img.mode}")
                
                # Convert to RGB for analysis
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Check brightness and contrast
                stat = ImageStat.Stat(img)
                brightness = sum(stat.mean) / 3
                contrast = sum(stat.stddev) / 3
                
                if brightness < self.min_brightness:
                    issues.append(f"Too dark: brightness {brightness:.1f}")
                elif brightness > self.max_brightness:
                    issues.append(f"Too bright: brightness {brightness:.1f}")
                
                if contrast < self.min_contrast:
                    issues.append(f"Low contrast: {contrast:.1f}")
                
                # Basic format validation (skip img.verify() as it breaks the image)
                if not hasattr(img, 'format') or img.format not in ['JPEG', 'PNG', 'BMP', 'TIFF']:
                    if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                        issues.append(f"Unsupported file extension: {image_path.suffix}")
            
            # Check for duplicates using hash
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
                if image_hash in self.image_hashes:
                    issues.append("Duplicate image")
                else:
                    self.image_hashes.add(image_hash)
            
        except Exception as e:
            issues.append(f"Cannot open/process image: {str(e)}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def organize_by_category(self, source_metadata: str) -> Dict[str, Any]:
        """Organize images by category with validation"""
        logger.info("📁 Organizing images by category...")
        
        # Load metadata
        if source_metadata.endswith('.json'):
            with open(source_metadata, 'r') as f:
                metadata = json.load(f)
        else:
            df = pd.read_csv(source_metadata)
            metadata = df.to_dict('records')
        
        organized_stats = {
            "categories": defaultdict(lambda: defaultdict(int)),
            "valid_files": [],
            "invalid_files": []
        }
        
        for item in metadata:
            self.validation_stats["total_images"] += 1
            
            # Determine paths
            if 'filename' in item:
                source_path = self.input_dir / item['filename']
            else:
                # Try to construct path from other fields
                category = item.get('category', item.get('disease_name', item.get('weed_name', 'unknown')))
                filename = f"{category}_{self.validation_stats['total_images']}.jpg"
                source_path = self.input_dir / filename
            
            if not source_path.exists():
                logger.warning(f"File not found: {source_path}")
                continue
            
            # Validate image
            is_valid, issues = self.validate_image_quality(source_path)
            
            if is_valid:
                # Organize valid images
                category = item.get('category', 'unknown')
                subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
                
                # Create organized directory structure
                category_dir = self.output_dir / "organized" / category
                subcategory_dir = category_dir / subcategory
                subcategory_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file with organized naming
                new_filename = f"{subcategory}_{organized_stats['categories'][category][subcategory]:04d}.jpg"
                dest_path = subcategory_dir / new_filename
                
                try:
                    shutil.copy2(source_path, dest_path)
                    
                    # Update metadata
                    item['organized_path'] = str(dest_path.relative_to(self.output_dir))
                    item['validation_status'] = 'valid'
                    organized_stats['valid_files'].append(item)
                    organized_stats['categories'][category][subcategory] += 1
                    
                    self.validation_stats["valid_images"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to copy {source_path}: {e}")
                    issues.append(f"Copy failed: {e}")
            
            if not is_valid:
                # Log invalid images
                self.validation_stats["invalid_images"] += 1
                for issue in issues:
                    self.validation_stats["issues"][issue] += 1
                
                item['validation_status'] = 'invalid'
                item['issues'] = issues
                organized_stats['invalid_files'].append(item)
        
        # Save organized metadata
        organized_metadata_path = self.output_dir / "organized_metadata.json"
        with open(organized_metadata_path, 'w') as f:
            json.dump({
                'valid_files': organized_stats['valid_files'],
                'invalid_files': organized_stats['invalid_files'],
                'statistics': dict(organized_stats['categories'])
            }, f, indent=2)
        
        logger.info(f"✅ Organization complete: {self.validation_stats['valid_images']} valid, {self.validation_stats['invalid_images']} invalid")
        return organized_stats
    
    def create_balanced_splits(self, organized_stats: Dict[str, Any], 
                             train_ratio: float = 0.7, val_ratio: float = 0.15, 
                             test_ratio: float = 0.15) -> Dict[str, Any]:
        """Create balanced train/validation/test splits"""
        logger.info("📊 Creating balanced dataset splits...")
        
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, "Split ratios must sum to 1.0"
        
        splits = {
            'train': {'files': [], 'stats': defaultdict(lambda: defaultdict(int))},
            'val': {'files': [], 'stats': defaultdict(lambda: defaultdict(int))},
            'test': {'files': [], 'stats': defaultdict(lambda: defaultdict(int))}
        }
        
        # Group by category and subcategory
        category_groups = defaultdict(lambda: defaultdict(list))
        for item in organized_stats['valid_files']:
            category = item.get('category', 'unknown')
            subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
            category_groups[category][subcategory].append(item)
        
        # Create splits for each subcategory
        for category, subcategories in category_groups.items():
            for subcategory, items in subcategories.items():
                if len(items) < 3:
                    # Too few items, put all in training
                    splits['train']['files'].extend(items)
                    splits['train']['stats'][category][subcategory] = len(items)
                    logger.warning(f"Only {len(items)} images for {category}/{subcategory}, putting all in training")
                else:
                    # Split proportionally
                    # First split train vs (val+test)
                    train_items, val_test_items = train_test_split(
                        items, train_size=train_ratio, random_state=42, shuffle=True
                    )
                    
                    # Then split val vs test
                    if len(val_test_items) >= 2:
                        val_size = val_ratio / (val_ratio + test_ratio)
                        val_items, test_items = train_test_split(
                            val_test_items, train_size=val_size, random_state=42, shuffle=True
                        )
                    else:
                        val_items = val_test_items
                        test_items = []
                    
                    # Add to splits
                    splits['train']['files'].extend(train_items)
                    splits['val']['files'].extend(val_items)
                    splits['test']['files'].extend(test_items)
                    
                    splits['train']['stats'][category][subcategory] = len(train_items)
                    splits['val']['stats'][category][subcategory] = len(val_items)
                    splits['test']['stats'][category][subcategory] = len(test_items)
        
        # Create split directories and copy files
        for split_name, split_data in splits.items():
            split_dir = self.output_dir / "splits" / split_name
            split_dir.mkdir(parents=True, exist_ok=True)
            
            for item in split_data['files']:
                source_path = Path(item['original_path'])  # Use original_path directly
                
                # Recreate directory structure in split
                category = item.get('category', 'unknown')
                subcategory = item.get('subcategory', item.get('disease_name', item.get('weed_name', 'unknown')))
                
                dest_dir = split_dir / category / subcategory
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                dest_path = dest_dir / source_path.name
                shutil.copy2(source_path, dest_path)
                
                # Update item with split path
                item[f'{split_name}_path'] = str(dest_path.relative_to(self.output_dir))
        
        # Save split metadata
        split_metadata = {
            'train': {
                'files': splits['train']['files'],
                'count': len(splits['train']['files']),
                'stats': dict(splits['train']['stats'])
            },
            'val': {
                'files': splits['val']['files'],
                'count': len(splits['val']['files']),
                'stats': dict(splits['val']['stats'])
            },
            'test': {
                'files': splits['test']['files'],
                'count': len(splits['test']['files']),
                'stats': dict(splits['test']['stats'])
            }
        }
        
        split_metadata_path = self.output_dir / "split_metadata.json"
        with open(split_metadata_path, 'w') as f:
            json.dump(split_metadata, f, indent=2)
        
        logger.info(f"📊 Splits created - Train: {split_metadata['train']['count']}, "
                   f"Val: {split_metadata['val']['count']}, Test: {split_metadata['test']['count']}")
        
        return split_metadata
    
    def generate_dataset_report(self, organized_stats: Dict[str, Any], 
                               split_metadata: Dict[str, Any]):
        """Generate comprehensive dataset report"""
        logger.info("📋 Generating dataset report...")
        
        report = {
            "dataset_summary": {
                "total_collected": self.validation_stats["total_images"],
                "valid_images": self.validation_stats["valid_images"],
                "invalid_images": self.validation_stats["invalid_images"],
                "validation_rate": self.validation_stats["valid_images"] / max(1, self.validation_stats["total_images"]) * 100
            },
            "category_distribution": dict(organized_stats['categories']),
            "split_distribution": {
                split: data['stats'] for split, data in split_metadata.items()
            },
            "quality_issues": dict(self.validation_stats["issues"]),
            "recommendations": []
        }
        
        # Add recommendations based on analysis
        if report["dataset_summary"]["validation_rate"] < 80:
            report["recommendations"].append("Low validation rate - consider improving data collection quality")
        
        # Check for class imbalance
        category_counts = organized_stats['categories']
        
        if category_counts:
            max_count = max(category_counts.values())
            min_count = min(category_counts.values())
            if max_count / min_count > 10:
                report["recommendations"].append("Significant class imbalance detected - consider data augmentation")
        
        # Save report
        report_path = self.output_dir / "dataset_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate visual report
        self._create_visual_report(report, organized_stats, split_metadata)
        
        logger.info(f"📋 Dataset report saved to {report_path}")
        return report
    
    def _create_visual_report(self, report: Dict[str, Any], 
                             organized_stats: Dict[str, Any],
                             split_metadata: Dict[str, Any]):
        """Create visual dataset analysis"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('AgriSense Dataset Analysis Report', fontsize=16, fontweight='bold')
            
            # 1. Validation Statistics
            ax1 = axes[0, 0]
            validation_data = [
                report["dataset_summary"]["valid_images"],
                report["dataset_summary"]["invalid_images"]
            ]
            labels = ['Valid Images', 'Invalid Images']
            colors = ['#2ecc71', '#e74c3c']
            ax1.pie(validation_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Image Validation Results')
            
            # 2. Category Distribution
            ax2 = axes[0, 1]
            category_counts = {}
            for category, subcats in organized_stats['categories'].items():
                category_counts[category] = sum(subcats.values())
            
            if category_counts:
                categories = list(category_counts.keys())
                counts = list(category_counts.values())
                bars = ax2.bar(categories, counts, color=['#3498db', '#f39c12'])
                ax2.set_title('Images per Category')
                ax2.set_ylabel('Number of Images')
                ax2.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom')
            
            # 3. Split Distribution
            ax3 = axes[1, 0]
            split_counts = [
                split_metadata['train']['count'],
                split_metadata['val']['count'],
                split_metadata['test']['count']
            ]
            split_labels = ['Train', 'Validation', 'Test']
            split_colors = ['#9b59b6', '#e67e22', '#1abc9c']
            bars = ax3.bar(split_labels, split_counts, color=split_colors)
            ax3.set_title('Dataset Split Distribution')
            ax3.set_ylabel('Number of Images')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
            
            # 4. Quality Issues
            ax4 = axes[1, 1]
            if report["quality_issues"]:
                issues = list(report["quality_issues"].keys())
                counts = list(report["quality_issues"].values())
                # Limit to top 5 issues
                if len(issues) > 5:
                    sorted_issues = sorted(zip(issues, counts), key=lambda x: x[1], reverse=True)
                    issues = [x[0] for x in sorted_issues[:5]]
                    counts = [x[1] for x in sorted_issues[:5]]
                
                bars = ax4.barh(issues, counts, color='#e74c3c')
                ax4.set_title('Top Quality Issues')
                ax4.set_xlabel('Number of Images')
            else:
                ax4.text(0.5, 0.5, 'No Quality Issues Found!', 
                        ha='center', va='center', transform=ax4.transAxes,
                        fontsize=14, color='green', fontweight='bold')
                ax4.set_title('Quality Issues')
            
            plt.tight_layout()
            
            # Save plot
            plot_path = self.output_dir / "dataset_analysis.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Visual report saved to {plot_path}")
            
        except ImportError:
            logger.warning("matplotlib/seaborn not available, skipping visual report")
        except Exception as e:
            logger.error(f"Failed to create visual report: {e}")
    
    def organize_existing_structure(self) -> Dict[str, Any]:
        """Organize images from existing directory structure"""
        logger.info("🚀 Starting complete dataset organization...")
        
        # Scan for existing images in the directory structure
        disease_dir = self.input_dir / "disease_images"
        weed_dir = self.input_dir / "weed_images"
        general_dir = self.input_dir / "general_images"
        
        all_valid_files = []
        all_invalid_files = []
        categories = defaultdict(list)
        
        # Process disease images
        if disease_dir.exists():
            logger.info("Processing disease images...")
            disease_files = self._scan_directory_structure(disease_dir, "disease")
            all_valid_files.extend(disease_files['valid_files'])
            all_invalid_files.extend(disease_files['invalid_files'])
            categories.update(disease_files['categories'])
        
        # Process weed images
        if weed_dir.exists():
            logger.info("Processing weed images...")
            weed_files = self._scan_directory_structure(weed_dir, "weed")
            all_valid_files.extend(weed_files['valid_files'])
            all_invalid_files.extend(weed_files['invalid_files'])
            categories.update(weed_files['categories'])
        
        # Process general images
        if general_dir.exists():
            logger.info("Processing general images...")
            general_files = self._scan_directory_structure(general_dir, "general")
            all_valid_files.extend(general_files['valid_files'])
            all_invalid_files.extend(general_files['invalid_files'])
            categories.update(general_files['categories'])
        
        # Create balanced splits
        logger.info("📊 Creating balanced dataset splits...")
        organized_stats = {
            'valid_files': all_valid_files,
            'invalid_files': all_invalid_files,
            'categories': categories
        }
        splits = self.create_balanced_splits(organized_stats)
        
        # Generate report
        logger.info("📋 Generating dataset report...")
        
        # Convert categories to proper format for reporting
        category_stats = {}
        for cat, items_list in categories.items():
            category_stats[cat] = len(items_list)
        
        organized_stats_for_report = {
            'valid_files': all_valid_files,
            'invalid_files': all_invalid_files,
            'categories': category_stats
        }
        
        report = self.generate_dataset_report(organized_stats_for_report, splits)
        
        logger.info(f"✅ Dataset organization completed!")
        logger.info(f"📊 Results: {len(all_valid_files)} valid images organized")
        
        return {
            'total_organized': len(all_valid_files),
            'valid_files': all_valid_files,
            'invalid_files': all_invalid_files,
            'categories': categories,
            'splits': splits,
            'report': report
        }
    
    def _scan_directory_structure(self, base_dir: Path, category_type: str) -> Dict[str, Any]:
        """Scan existing directory structure for images"""
        valid_files = []
        invalid_files = []
        categories = defaultdict(list)
        
        # Look for image files in all subdirectories
        for image_path in base_dir.rglob("*.jpg"):
            if image_path.is_file():
                self.validation_stats["total_images"] += 1
                
                # Validate image
                is_valid, issues = self.validate_image_quality(image_path)
                
                if is_valid:
                    # Extract category from path structure
                    relative_path = image_path.relative_to(base_dir)
                    
                    # Extract actual category/disease name from filename or directory structure
                    if category_type == "disease":
                        # Extract disease name from filename (e.g. "leaf_spot_potato_moderate_1.jpg" -> "leaf_spot")
                        filename_parts = image_path.stem.split('_')
                        if len(filename_parts) >= 2:
                            # Take first part or first two parts as disease name
                            if filename_parts[0] in ['bacterial', 'nitrogen', 'phosphorus', 'potassium', 'iron', 'magnesium', 'yellow']:
                                category = '_'.join(filename_parts[:2])  # e.g. "bacterial_canker", "yellow_leaf_curl"
                            else:
                                category = filename_parts[0]  # e.g. "leaf_spot", "rust"
                        else:
                            category = "unknown_disease"
                    elif category_type == "weed":
                        # Extract weed name from filename
                        filename_parts = image_path.stem.split('_')
                        if len(filename_parts) >= 1:
                            if filename_parts[0] in ['yellow', 'purple', 'canada', 'field']:
                                category = '_'.join(filename_parts[:2])  # e.g. "yellow_nutsedge", "canada_thistle"
                            else:
                                category = filename_parts[0]  # e.g. "dandelion", "crabgrass"
                        else:
                            category = "unknown_weed"
                    else:
                        # For general images, use directory or filename prefix
                        if len(relative_path.parts) > 1:
                            category = relative_path.parts[0]
                        else:
                            category = image_path.stem.split('_')[0]
                    
                    # Create metadata
                    relative_path = image_path.relative_to(self.input_dir)
                    metadata = {
                        'original_path': str(image_path),
                        'organized_path': str(relative_path),  # Add organized_path
                        'filename': image_path.name,
                        'category': f"{category_type}_{category}",
                        'subcategory': category,
                        'type': category_type,
                        'valid': True
                    }
                    
                    valid_files.append(metadata)
                    categories[f"{category_type}_{category}"].append(metadata)
                    self.validation_stats["valid_images"] += 1
                else:
                    invalid_files.append({
                        'path': str(image_path),
                        'issues': issues
                    })
                    self.validation_stats["invalid_images"] += 1
                    for issue in issues:
                        self.validation_stats["issues"][issue] += 1
        
        logger.info(f"✅ Organization complete: {len(valid_files)} valid, {len(invalid_files)} invalid")
        
        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'categories': categories
        }

    def organize_complete_dataset(self, disease_metadata: str, weed_metadata: str) -> Dict[str, Any]:
        """Complete dataset organization workflow"""
        logger.info("🚀 Starting complete dataset organization...")
        
        start_time = time.time()
        
        # Process disease dataset
        logger.info("Processing disease images...")
        disease_stats = self.organize_by_category(disease_metadata)
        
        # Reset hashes for weed processing (to allow same images in different categories)
        self.image_hashes.clear()
        
        # Process weed dataset
        logger.info("Processing weed images...")
        weed_stats = self.organize_by_category(weed_metadata)
        
        # Combine statistics
        combined_stats = {
            'valid_files': disease_stats['valid_files'] + weed_stats['valid_files'],
            'invalid_files': disease_stats['invalid_files'] + weed_stats['invalid_files'],
            'categories': {}
        }
        combined_stats['categories'].update(disease_stats['categories'])
        combined_stats['categories'].update(weed_stats['categories'])
        
        # Create splits
        split_metadata = self.create_balanced_splits(combined_stats)
        
        # Generate report
        report = self.generate_dataset_report(combined_stats, split_metadata)
        
        end_time = time.time()
        
        results = {
            "total_organized": len(combined_stats['valid_files']),
            "total_invalid": len(combined_stats['invalid_files']),
            "categories": len(combined_stats['categories']),
            "duration": end_time - start_time,
            "output_dir": str(self.output_dir),
            "report": report
        }
        
        logger.info("✅ Dataset organization completed!")
        logger.info(f"📊 Results: {results['total_organized']} valid images organized")
        
        return results

def main():
    """Main execution"""
    # Example usage
    organizer = DatasetOrganizer(
        input_dir="agricultural_datasets",
        output_dir="organized_agricultural_datasets"
    )
    
    # Organize datasets (you would specify actual metadata files)
    results = organizer.organize_complete_dataset(
        disease_metadata="disease_datasets/disease_metadata.json",
        weed_metadata="weed_datasets/weed_metadata.json"
    )
    
    print("\n" + "="*60)
    print("📁 DATASET ORGANIZATION COMPLETE")
    print("="*60)
    print(f"✅ Valid Images: {results['total_organized']}")
    print(f"❌ Invalid Images: {results['total_invalid']}")
    print(f"🏷️  Categories: {results['categories']}")
    print(f"⏱️  Duration: {results['duration']:.1f} seconds")
    print(f"📁 Output: {results['output_dir']}")
    print("="*60)

if __name__ == "__main__":
    main()