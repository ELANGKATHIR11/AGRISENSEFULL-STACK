#!/usr/bin/env python3
"""
Master Agricultural Dataset Collection Orchestrator
Coordinates all components to create comprehensive ML datasets
"""

import os
import sys
import logging
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import from current directory
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from agricultural_image_collector import AgricultureImageCollector
from disease_image_collector import DiseaseImageCollector
from weed_image_collector import WeedImageCollector
from dataset_organizer import DatasetOrganizer
from agricultural_augmentation import AgriculturalAugmentationPipeline
from pytorch_data_preparation import DataLoaderFactory, create_dataset_analysis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterDatasetOrchestrator:
    """Master orchestrator for complete dataset creation workflow"""
    
    def __init__(self, base_output_dir: str = "agricultural_ml_datasets"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        
        # Initialize all components
        self.general_collector = AgricultureImageCollector(str(self.base_output_dir / "general_images"))
        self.disease_collector = DiseaseImageCollector(str(self.base_output_dir / "disease_images"))
        self.weed_collector = WeedImageCollector(str(self.base_output_dir / "weed_images"))
        
        # Progress tracking
        self.progress = {
            'general_collection': {'status': 'pending', 'count': 0, 'time': 0},
            'disease_collection': {'status': 'pending', 'count': 0, 'time': 0},
            'weed_collection': {'status': 'pending', 'count': 0, 'time': 0},
            'organization': {'status': 'pending', 'count': 0, 'time': 0},
            'augmentation': {'status': 'pending', 'count': 0, 'time': 0},
            'pytorch_preparation': {'status': 'pending', 'count': 0, 'time': 0}
        }
        
        logger.info(f"🎬 Master Dataset Orchestrator initialized")
        logger.info(f"📁 Output directory: {self.base_output_dir}")
    
    async def collect_all_images(self, 
                                max_images_per_category: int = 100,
                                use_parallel: bool = True) -> Dict[str, Any]:
        """Collect all types of agricultural images"""
        logger.info("🔄 Starting comprehensive image collection...")
        
        start_time = time.time()
        
        if use_parallel:
            # Run collections in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all collection tasks
                general_future = executor.submit(
                    self._collect_general_images, max_images_per_category
                )
                disease_future = executor.submit(
                    self._collect_disease_images, max_images_per_category
                )
                weed_future = executor.submit(
                    self._collect_weed_images, max_images_per_category
                )
                
                # Wait for completion and collect results
                general_result = general_future.result()
                disease_result = disease_future.result()
                weed_result = weed_future.result()
        else:
            # Sequential collection
            general_result = self._collect_general_images(max_images_per_category)
            disease_result = self._collect_disease_images(max_images_per_category)
            weed_result = self._collect_weed_images(max_images_per_category)
        
        total_time = time.time() - start_time
        
        # Combine results
        combined_results = {
            'general': general_result,
            'diseases': disease_result,
            'weeds': weed_result,
            'total_images': (general_result.get('total_collected', 0) + 
                           disease_result.get('total_collected', 0) + 
                           weed_result.get('total_collected', 0)),
            'total_time': total_time,
            'collection_complete': True
        }
        
        # Save collection summary
        summary_path = self.base_output_dir / "collection_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(combined_results, f, indent=2, default=str)
        
        logger.info(f"✅ Image collection complete!")
        logger.info(f"📊 Total images collected: {combined_results['total_images']}")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        
        return combined_results
    
    def _collect_general_images(self, max_images: int) -> Dict[str, Any]:
        """Collect general agricultural images"""
        logger.info("🌾 Collecting general agricultural images...")
        start_time = time.time()
        
        try:
            self.progress['general_collection']['status'] = 'running'
            
            # Run collection using the correct method
            result = self.general_collector.collect_all()
            
            count = result.get('total_collected', 0)
            self.progress['general_collection'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ General collection: {count} images")
            return result
            
        except Exception as e:
            self.progress['general_collection']['status'] = 'failed'
            logger.error(f"❌ General collection failed: {e}")
            return {'total_collected': 0, 'error': str(e)}
    
    def _collect_disease_images(self, max_images: int) -> Dict[str, Any]:
        """Collect disease images"""
        logger.info("🦠 Collecting plant disease images...")
        start_time = time.time()
        
        try:
            self.progress['disease_collection']['status'] = 'running'
            
            result = self.disease_collector.collect_complete_dataset()
            
            count = result.get('total_collected', 0)
            self.progress['disease_collection'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ Disease collection: {count} images")
            return result
            
        except Exception as e:
            self.progress['disease_collection']['status'] = 'failed'
            logger.error(f"❌ Disease collection failed: {e}")
            return {'total_collected': 0, 'error': str(e)}
    
    def _collect_weed_images(self, max_images: int) -> Dict[str, Any]:
        """Collect weed images"""
        logger.info("🌿 Collecting weed images...")
        start_time = time.time()
        
        try:
            self.progress['weed_collection']['status'] = 'running'
            
            result = self.weed_collector.collect_complete_dataset()
            
            count = result.get('total_collected', 0)
            self.progress['weed_collection'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ Weed collection: {count} images")
            return result
            
        except Exception as e:
            self.progress['weed_collection']['status'] = 'failed'
            logger.error(f"❌ Weed collection failed: {e}")
            return {'total_collected': 0, 'error': str(e)}
    
    def organize_collected_data(self, 
                               train_split: float = 0.7,
                               val_split: float = 0.15,
                               test_split: float = 0.15) -> Dict[str, Any]:
        """Organize all collected data into training structure"""
        logger.info("📋 Organizing collected datasets...")
        start_time = time.time()
        
        try:
            self.progress['organization']['status'] = 'running'
            
            # Create organizer for the collected dataset directory
            organizer = DatasetOrganizer(str(self.base_output_dir), str(self.base_output_dir / "organized_datasets"))
            
            # Check for metadata files from collections
            disease_metadata = self.base_output_dir / "disease_images" / "disease_metadata.json"
            weed_metadata = self.base_output_dir / "weed_images" / "weed_metadata.json"
            general_metadata = self.base_output_dir / "general_images" / "metadata.json"
            
            # First try to use existing directory structure (for sample data)
            disease_dir = self.base_output_dir / "disease_images"
            weed_dir = self.base_output_dir / "weed_images"
            general_dir = self.base_output_dir / "general_images"
            
            # Check if we have any images in directory structure
            has_images = any([
                disease_dir.exists() and any(disease_dir.rglob("*.jpg")),
                weed_dir.exists() and any(weed_dir.rglob("*.jpg")),
                general_dir.exists() and any(general_dir.rglob("*.jpg"))
            ])
            
            if has_images:
                # Use directory structure organization (for sample data or existing collections)
                logger.info("📁 Using existing directory structure...")
                result = organizer.organize_existing_structure()
            elif disease_metadata.exists() and weed_metadata.exists():
                # Use complete dataset organization
                result = organizer.organize_complete_dataset(
                    disease_metadata=str(disease_metadata),
                    weed_metadata=str(weed_metadata)
                )
            elif disease_metadata.exists():
                # Organize disease images only
                result = organizer.organize_by_category(str(disease_metadata))
            elif weed_metadata.exists():
                # Organize weed images only  
                result = organizer.organize_by_category(str(weed_metadata))
            elif general_metadata.exists():
                # Organize general images only
                result = organizer.organize_by_category(str(general_metadata))
            else:
                raise ValueError("No metadata files or image directories found from collection phase")
            
            count = result.get('total_organized', 0)
            self.progress['organization'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ Organization complete: {count} images organized")
            return result
            
        except Exception as e:
            self.progress['organization']['status'] = 'failed'
            logger.error(f"❌ Organization failed: {e}")
            return {'total_organized': 0, 'error': str(e)}
    
    def create_augmented_dataset(self, 
                                augmentation_factor: int = 3,
                                augmentation_level: str = 'medium') -> Dict[str, Any]:
        """Create augmented versions of the dataset"""
        logger.info("🔄 Creating augmented dataset...")
        start_time = time.time()
        
        try:
            self.progress['augmentation']['status'] = 'running'
            
            # Get organized dataset path
            organized_dir = self.base_output_dir / "organized_datasets"
            augmented_dir = self.base_output_dir / "augmented_datasets"
            
            if not organized_dir.exists():
                raise ValueError("Organized dataset not found. Run organization first.")
            
            # Create augmentation pipeline
            aug_pipeline = AgriculturalAugmentationPipeline(str(augmented_dir))
            
            # Get metadata from organized dataset
            metadata_file = organized_dir / "split_metadata.json"
            if not metadata_file.exists():
                raise ValueError("Split metadata not found")
            
            # Apply augmentation
            result = aug_pipeline.augment_dataset(
                dataset_dir=str(organized_dir),
                metadata_file=str(metadata_file)
            )
            
            count = result.get('total_augmented', 0)
            self.progress['augmentation'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ Augmentation complete: {count} augmented images")
            return result
            
        except Exception as e:
            self.progress['augmentation']['status'] = 'failed'
            logger.error(f"❌ Augmentation failed: {e}")
            return {'total_augmented': 0, 'error': str(e)}
    
    def prepare_pytorch_datasets(self, 
                                batch_size: int = 32,
                                image_size: int = 224,
                                num_workers: int = 4) -> Dict[str, Any]:
        """Prepare PyTorch datasets and data loaders"""
        logger.info("🔥 Preparing PyTorch datasets...")
        start_time = time.time()
        
        try:
            self.progress['pytorch_preparation']['status'] = 'running'
            
            # Use augmented dataset if available, otherwise organized dataset
            dataset_dir = self.base_output_dir / "augmented_datasets"
            metadata_file = dataset_dir / "augmented_metadata.json"
            
            if not dataset_dir.exists() or not metadata_file.exists():
                # Fallback to organized dataset
                dataset_dir = self.base_output_dir / "organized_datasets"
                metadata_file = dataset_dir / "split_metadata.json"
                
                if not dataset_dir.exists() or not metadata_file.exists():
                    raise ValueError("No organized or augmented dataset found")
            
            # Create data loaders
            train_loader, val_loader, test_loader, dataset_info = DataLoaderFactory.create_loaders(
                data_dir=str(dataset_dir),
                metadata_file=str(metadata_file),
                batch_size=batch_size,
                image_size=image_size,
                num_workers=num_workers
            )
            
            # Create analysis
            analysis_dir = self.base_output_dir / "pytorch_analysis"
            create_dataset_analysis(dataset_info, str(analysis_dir))
            
            # Save dataset info
            pytorch_dir = self.base_output_dir / "pytorch_datasets"
            pytorch_dir.mkdir(exist_ok=True)
            
            with open(pytorch_dir / "dataset_info.json", 'w') as f:
                json.dump(dataset_info, f, indent=2)
            
            count = dataset_info['train_size'] + dataset_info['val_size'] + dataset_info['test_size']
            self.progress['pytorch_preparation'].update({
                'status': 'completed',
                'count': count,
                'time': time.time() - start_time
            })
            
            logger.info(f"✅ PyTorch preparation complete: {count} samples ready")
            
            return {
                'dataset_info': dataset_info,
                'train_samples': dataset_info['train_size'],
                'val_samples': dataset_info['val_size'],
                'test_samples': dataset_info['test_size'],
                'num_classes': dataset_info['num_classes'],
                'pytorch_ready': True
            }
            
        except Exception as e:
            self.progress['pytorch_preparation']['status'] = 'failed'
            logger.error(f"❌ PyTorch preparation failed: {e}")
            return {'pytorch_ready': False, 'error': str(e)}
    
    async def run_complete_pipeline(self,
                                   max_images_per_category: int = 100,
                                   augmentation_factor: int = 3,
                                   batch_size: int = 32,
                                   image_size: int = 224) -> Dict[str, Any]:
        """Run the complete dataset creation pipeline"""
        logger.info("🚀 Starting complete ML dataset creation pipeline...")
        pipeline_start = time.time()
        
        results = {}
        
        try:
            # Phase 1: Image Collection
            print("\n" + "="*60)
            print("📸 PHASE 1: IMAGE COLLECTION")
            print("="*60)
            
            collection_results = await self.collect_all_images(
                max_images_per_category=max_images_per_category,
                use_parallel=True
            )
            results['collection'] = collection_results
            
            # Phase 2: Data Organization
            print("\n" + "="*60)
            print("📋 PHASE 2: DATA ORGANIZATION")
            print("="*60)
            
            organization_results = self.organize_collected_data()
            results['organization'] = organization_results
            
            # Phase 3: Data Augmentation
            print("\n" + "="*60)
            print("🔄 PHASE 3: DATA AUGMENTATION")
            print("="*60)
            
            augmentation_results = self.create_augmented_dataset(
                augmentation_factor=augmentation_factor
            )
            results['augmentation'] = augmentation_results
            
            # Phase 4: PyTorch Preparation
            print("\n" + "="*60)
            print("🔥 PHASE 4: PYTORCH PREPARATION")
            print("="*60)
            
            pytorch_results = self.prepare_pytorch_datasets(
                batch_size=batch_size,
                image_size=image_size
            )
            results['pytorch'] = pytorch_results
            
            # Final summary
            total_time = time.time() - pipeline_start
            results['pipeline_summary'] = {
                'total_time': total_time,
                'success': True,
                'final_dataset_ready': pytorch_results.get('pytorch_ready', False)
            }
            
            self._print_final_summary(results, total_time)
            
            # Save complete results
            final_results_path = self.base_output_dir / "pipeline_results.json"
            with open(final_results_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            results['pipeline_summary'] = {
                'success': False,
                'error': str(e),
                'total_time': time.time() - pipeline_start
            }
            return results
    
    def _print_final_summary(self, results: Dict[str, Any], total_time: float):
        """Print comprehensive final summary"""
        print("\n" + "="*80)
        print("🎯 AGRICULTURAL ML DATASET CREATION COMPLETE!")
        print("="*80)
        
        # Collection summary
        collection = results.get('collection', {})
        print(f"📸 Images Collected: {collection.get('total_images', 0):,}")
        print(f"   🌾 General: {collection.get('general', {}).get('total_collected', 0)}")
        print(f"   🦠 Diseases: {collection.get('diseases', {}).get('total_collected', 0)}")
        print(f"   🌿 Weeds: {collection.get('weeds', {}).get('total_collected', 0)}")
        
        # Organization summary
        organization = results.get('organization', {})
        print(f"\n📋 Images Organized: {organization.get('total_organized', 0):,}")
        
        # Augmentation summary
        augmentation = results.get('augmentation', {})
        print(f"🔄 Images Augmented: {augmentation.get('total_augmented', 0):,}")
        
        # PyTorch summary
        pytorch = results.get('pytorch', {})
        if pytorch.get('pytorch_ready'):
            print(f"\n🔥 PyTorch Dataset Ready:")
            print(f"   📚 Training: {pytorch.get('train_samples', 0):,}")
            print(f"   🔍 Validation: {pytorch.get('val_samples', 0):,}")
            print(f"   🧪 Test: {pytorch.get('test_samples', 0):,}")
            print(f"   🏷️  Classes: {pytorch.get('num_classes', 0)}")
        
        # Performance summary
        print(f"\n⏱️  Total Pipeline Time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        
        # Status summary
        success_count = sum(1 for phase in self.progress.values() if phase['status'] == 'completed')
        total_phases = len(self.progress)
        print(f"📊 Phases Completed: {success_count}/{total_phases}")
        
        # Output directory
        print(f"📁 Output Directory: {self.base_output_dir}")
        
        print("="*80)
        
        if pytorch.get('pytorch_ready'):
            print("✅ Dataset is ready for ML model training!")
        else:
            print("⚠️  Dataset creation incomplete - check errors above")
        
        print("="*80)

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Agricultural ML Dataset Creation Pipeline')
    parser.add_argument('--output-dir', default='agricultural_ml_datasets', 
                       help='Output directory for datasets')
    parser.add_argument('--max-images', type=int, default=50,
                       help='Maximum images per category to collect')
    parser.add_argument('--augmentation-factor', type=int, default=2,
                       help='Augmentation factor (number of augmented versions per image)')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='PyTorch batch size')
    parser.add_argument('--image-size', type=int, default=224,
                       help='Target image size')
    parser.add_argument('--phase', choices=['collect', 'organize', 'augment', 'pytorch', 'all'],
                       default='all', help='Which phase to run')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = MasterDatasetOrchestrator(args.output_dir)
    
    if args.phase == 'all':
        # Run complete pipeline
        results = asyncio.run(orchestrator.run_complete_pipeline(
            max_images_per_category=args.max_images,
            augmentation_factor=args.augmentation_factor,
            batch_size=args.batch_size,
            image_size=args.image_size
        ))
    else:
        # Run specific phase
        if args.phase == 'collect':
            results = asyncio.run(orchestrator.collect_all_images(args.max_images))
        elif args.phase == 'organize':
            results = orchestrator.organize_collected_data()
        elif args.phase == 'augment':
            results = orchestrator.create_augmented_dataset(args.augmentation_factor)
        elif args.phase == 'pytorch':
            results = orchestrator.prepare_pytorch_datasets(args.batch_size, args.image_size)
    
    print(f"\n🏁 Phase '{args.phase}' completed!")

if __name__ == "__main__":
    main()