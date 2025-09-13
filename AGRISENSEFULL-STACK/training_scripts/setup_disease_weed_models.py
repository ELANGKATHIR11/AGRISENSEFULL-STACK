#!/usr/bin/env python3
"""
Setup script for Disease and Weed Management integration
Downloads datasets and pre-trained models from Hugging Face
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Union
import requests
from datasets import load_dataset  # type: ignore
from transformers import AutoModelForImageClassification, AutoImageProcessor  # type: ignore

HERE = Path(__file__).parent
BACKEND_DIR = HERE / "agrisense_app" / "backend"
MODELS_DIR = BACKEND_DIR / "models"
DATASETS_DIR = HERE / "datasets"

def ensure_directories():
    """Create necessary directories"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directories: {MODELS_DIR}, {DATASETS_DIR}")

def safe_save_dataset(dataset: Any, path: str) -> bool:
    """Safely save dataset to disk if possible"""
    try:
        if hasattr(dataset, 'save_to_disk'):
            dataset.save_to_disk(path)  # type: ignore
            return True
    except Exception as e:
        print(f"⚠️ Could not save dataset to {path}: {e}")
    return False

def safe_get_dataset_size(dataset: Any, split_name: str = "train") -> int:
    """Safely get dataset size"""
    try:
        if hasattr(dataset, '__getitem__'):
            split_data = dataset[split_name]  # type: ignore
            if hasattr(split_data, '__len__'):
                return len(split_data)  # type: ignore
    except Exception:
        pass
    return 0

def safe_get_num_classes(dataset: Any, split_name: str = "train") -> int:
    """Safely get number of classes"""
    try:
        if hasattr(dataset, '__getitem__'):
            split_data = dataset[split_name]  # type: ignore
            if hasattr(split_data, 'features') and hasattr(split_data.features, 'get'):
                label_feature = split_data.features.get('label')  # type: ignore
                if label_feature and hasattr(label_feature, 'names'):
                    return len(label_feature.names)  # type: ignore
    except Exception:
        pass
    return 0

def safe_check_split_exists(dataset: Any, split_name: str) -> bool:
    """Safely check if split exists in dataset"""
    try:
        if hasattr(dataset, '__contains__'):
            return split_name in dataset  # type: ignore
        elif hasattr(dataset, '__getitem__'):
            dataset[split_name]  # type: ignore
            return True
    except Exception:
        pass
    return False

def download_disease_datasets():
    """Download disease detection datasets from Hugging Face"""
    print("\n📦 Downloading Disease Detection Datasets...")
    
    datasets_info = []
    
    try:
        # 1. PlantVillage Dataset (Primary)
        print("📊 Downloading PlantVillage Dataset...")
        plant_village = load_dataset("BrandonFors/Plant-Diseases-PlantVillage-Dataset")  # type: ignore
        safe_save_dataset(plant_village, str(DATASETS_DIR / "plant_village"))
        
        num_classes = safe_get_num_classes(plant_village, "train")
        train_size = safe_get_dataset_size(plant_village, "train")
        test_size = safe_get_dataset_size(plant_village, "test") if safe_check_split_exists(plant_village, "test") else 0
        
        datasets_info.append({
            "name": "PlantVillage",
            "path": str(DATASETS_DIR / "plant_village"),
            "classes": num_classes,
            "train_size": train_size,
            "test_size": test_size
        })
        print(f"✅ PlantVillage: {num_classes} classes, {train_size} training images")
        
    except Exception as e:
        print(f"⚠️ PlantVillage download failed: {e}")
    
    try:
        # 2. Plant Pathology 2021 (Secondary)
        print("📊 Downloading Plant Pathology 2021...")
        plant_pathology = load_dataset("timm/plant-pathology-2021")  # type: ignore
        safe_save_dataset(plant_pathology, str(DATASETS_DIR / "plant_pathology_2021"))
        
        train_size = safe_get_dataset_size(plant_pathology, "train")
        test_size = safe_get_dataset_size(plant_pathology, "test") if safe_check_split_exists(plant_pathology, "test") else 0
        
        datasets_info.append({
            "name": "Plant Pathology 2021",
            "path": str(DATASETS_DIR / "plant_pathology_2021"),
            "classes": "Multi-label",
            "train_size": train_size,
            "test_size": test_size
        })
        print(f"✅ Plant Pathology 2021: Multi-label, {train_size} training images")
        
    except Exception as e:
        print(f"⚠️ Plant Pathology 2021 download failed: {e}")
    
    try:
        # 3. Simple Plant Disease (Basic)
        print("📊 Downloading Simple Plant Disease...")
        simple_disease = load_dataset("akahana/plant-disease")  # type: ignore
        safe_save_dataset(simple_disease, str(DATASETS_DIR / "simple_plant_disease"))
        
        train_size = safe_get_dataset_size(simple_disease, "train")
        test_size = safe_get_dataset_size(simple_disease, "test") if safe_check_split_exists(simple_disease, "test") else 0
        
        datasets_info.append({
            "name": "Simple Plant Disease",
            "path": str(DATASETS_DIR / "simple_plant_disease"),
            "classes": 3,  # Healthy, Powdery, Rust
            "train_size": train_size,
            "test_size": test_size
        })
        print(f"✅ Simple Plant Disease: 3 classes, {train_size} training images")
        
    except Exception as e:
        print(f"⚠️ Simple Plant Disease download failed: {e}")
    
    # Save dataset info
    with open(DATASETS_DIR / "disease_datasets_info.json", "w") as f:
        json.dump(datasets_info, f, indent=2)
    
    return datasets_info

def download_weed_datasets():
    """Download weed/plant segmentation datasets"""
    print("\n🌾 Downloading Weed Detection Datasets...")
    
    datasets_info = []
    
    try:
        # Plantation Segmentation (for weed detection)
        print("📊 Downloading Plantation Segmentation...")
        plantations = load_dataset("UniqueData/plantations_segmentation")  # type: ignore
        safe_save_dataset(plantations, str(DATASETS_DIR / "plantations_segmentation"))
        
        # Try to get size from train split first, then any available split
        train_size = safe_get_dataset_size(plantations, "train")
        if train_size == 0:
            # Try to get from any available split
            try:
                if hasattr(plantations, '__iter__'):
                    for split_name in ['test', 'validation', 'val']:  # type: ignore
                        train_size = safe_get_dataset_size(plantations, split_name)
                        if train_size > 0:
                            break
            except Exception:
                train_size = 0
        
        datasets_info.append({
            "name": "Plantations Segmentation",
            "path": str(DATASETS_DIR / "plantations_segmentation"),
            "type": "segmentation",
            "crops": ["cabbage", "zucchini"],
            "train_size": train_size
        })
        print(f"✅ Plantations Segmentation: {train_size} images")
        
    except Exception as e:
        print(f"⚠️ Plantations Segmentation download failed: {e}")
    
    # Save dataset info
    with open(DATASETS_DIR / "weed_datasets_info.json", "w") as f:
        json.dump(datasets_info, f, indent=2)
    
    return datasets_info

def download_pretrained_models():
    """Download pre-trained disease detection models"""
    print("\n🤖 Downloading Pre-trained Models...")
    
    models_info = []
    
    try:
        # 1. MobileNet V2 (Most popular - 2.8K downloads)
        print("🧠 Downloading MobileNet V2 Disease Detection Model...")
        model_name = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
        
        disease_model = AutoModelForImageClassification.from_pretrained(model_name)
        processor = AutoImageProcessor.from_pretrained(model_name)
        
        model_dir = MODELS_DIR / "mobilenet_disease"
        model_dir.mkdir(exist_ok=True)
        
        disease_model.save_pretrained(str(model_dir))
        processor.save_pretrained(str(model_dir))
        
        models_info.append({
            "name": "MobileNet V2 Disease Detection",
            "path": str(model_dir),
            "architecture": "MobileNet V2",
            "task": "disease_classification",
            "huggingface_id": model_name,
            "downloads": "2.8K+",
            "optimized_for": "mobile/edge"
        })
        print("✅ MobileNet V2 Disease Detection model downloaded")
        
    except Exception as e:
        print(f"⚠️ MobileNet V2 download failed: {e}")
    
    try:
        # 2. Vision Transformer (High accuracy - 1.3K downloads)
        print("🧠 Downloading Vision Transformer Disease Detection Model...")
        model_name = "muhammad-atif-ali/fine_tuned_vit_plant_disease"
        
        vit_model = AutoModelForImageClassification.from_pretrained(model_name)
        vit_processor = AutoImageProcessor.from_pretrained(model_name)
        
        vit_dir = MODELS_DIR / "vit_disease"
        vit_dir.mkdir(exist_ok=True)
        
        vit_model.save_pretrained(str(vit_dir))
        vit_processor.save_pretrained(str(vit_dir))
        
        models_info.append({
            "name": "Vision Transformer Disease Detection",
            "path": str(vit_dir),
            "architecture": "Vision Transformer",
            "task": "disease_classification",
            "huggingface_id": model_name,
            "downloads": "1.3K+",
            "optimized_for": "accuracy"
        })
        print("✅ Vision Transformer Disease Detection model downloaded")
        
    except Exception as e:
        print(f"⚠️ Vision Transformer download failed: {e}")
    
    try:
        # 3. ResNet-50 (Balanced performance - 161 downloads, 10 likes)
        print("🧠 Downloading ResNet-50 Disease Detection Model...")
        model_name = "SanketJadhav/PlantDiseaseClassifier-Resnet50"
        
        resnet_model = AutoModelForImageClassification.from_pretrained(model_name)
        resnet_processor = AutoImageProcessor.from_pretrained(model_name)
        
        resnet_dir = MODELS_DIR / "resnet_disease"
        resnet_dir.mkdir(exist_ok=True)
        
        resnet_model.save_pretrained(str(resnet_dir))
        resnet_processor.save_pretrained(str(resnet_dir))
        
        models_info.append({
            "name": "ResNet-50 Disease Detection",
            "path": str(resnet_dir),
            "architecture": "ResNet-50",
            "task": "disease_classification",
            "huggingface_id": model_name,
            "downloads": "161",
            "optimized_for": "balanced"
        })
        print("✅ ResNet-50 Disease Detection model downloaded")
        
    except Exception as e:
        print(f"⚠️ ResNet-50 download failed: {e}")
    
    # Save models info
    with open(MODELS_DIR / "pretrained_models_info.json", "w") as f:
        json.dump(models_info, f, indent=2)
    
    return models_info

def create_disease_classes_mapping():
    """Create disease classes mapping for the models"""
    print("\n📋 Creating Disease Classes Mapping...")
    
    # Common plant disease classes (from PlantVillage dataset)
    disease_classes = {
        "apple": [
            "apple_scab", "apple_black_rot", "apple_cedar_rust", "apple_healthy"
        ],
        "corn": [
            "corn_gray_leaf_spot", "corn_common_rust", "corn_northern_leaf_blight", "corn_healthy"
        ],
        "tomato": [
            "tomato_bacterial_spot", "tomato_early_blight", "tomato_late_blight", 
            "tomato_leaf_mold", "tomato_septoria_leaf_spot", "tomato_spider_mites",
            "tomato_target_spot", "tomato_yellow_leaf_curl_virus", "tomato_mosaic_virus", "tomato_healthy"
        ],
        "potato": [
            "potato_early_blight", "potato_late_blight", "potato_healthy"
        ],
        "pepper": [
            "pepper_bacterial_spot", "pepper_healthy"
        ],
        "grape": [
            "grape_black_rot", "grape_esca", "grape_leaf_blight", "grape_healthy"
        ]
    }
    
    # Treatment recommendations for each disease
    treatment_recommendations = {
        "bacterial_spot": {
            "immediate": ["Remove affected leaves", "Improve air circulation"],
            "chemical": ["Copper-based fungicide", "Streptomycin spray"],
            "organic": ["Neem oil", "Baking soda solution"],
            "prevention": ["Crop rotation", "Drip irrigation", "Sanitize tools"]
        },
        "early_blight": {
            "immediate": ["Remove infected plant debris", "Increase spacing"],
            "chemical": ["Chlorothalonil", "Mancozeb"],
            "organic": ["Compost tea", "Copper soap"],
            "prevention": ["Mulching", "Avoid overhead watering", "Resistant varieties"]
        },
        "late_blight": {
            "immediate": ["Remove all infected plants", "Emergency quarantine"],
            "chemical": ["Metalaxyl", "Cymoxanil"],
            "organic": ["Bordeaux mixture", "Copper sulfate"],
            "prevention": ["Weather monitoring", "Prophylactic treatment", "Field hygiene"]
        },
        "powdery_mildew": {
            "immediate": ["Improve air circulation", "Reduce humidity"],
            "chemical": ["Sulfur dust", "Trifloxystrobin"],
            "organic": ["Milk spray", "Potassium bicarbonate"],
            "prevention": ["Plant spacing", "Morning watering only", "Resistant cultivars"]
        },
        "rust": {
            "immediate": ["Remove affected leaves", "Isolate plants"],
            "chemical": ["Propiconazole", "Tebuconazole"],
            "organic": ["Garlic extract", "Horsetail tea"],
            "prevention": ["Avoid wet foliage", "Plant resistant varieties", "Crop rotation"]
        }
    }
    
    disease_config = {
        "classes": disease_classes,
        "treatments": treatment_recommendations,
        "severity_levels": {
            "low": {"threshold": 0.3, "action": "monitor"},
            "medium": {"threshold": 0.7, "action": "treat_organic"},
            "high": {"threshold": 0.9, "action": "treat_chemical"},
            "critical": {"threshold": 0.95, "action": "emergency_protocol"}
        }
    }
    
    with open(BACKEND_DIR / "disease_classes.json", "w") as f:
        json.dump(disease_config, f, indent=2)
    
    print("✅ Disease classes and treatment mapping created")
    return disease_config

def create_integration_config():
    """Create configuration for integrating with existing AgriSense system"""
    print("\n⚙️ Creating Integration Configuration...")
    
    integration_config = {
        "disease_detection": {
            "enabled": True,
            "primary_model": "mobilenet_disease",
            "confidence_threshold": 0.7,
            "image_formats": ["jpg", "jpeg", "png", "webp"],
            "max_image_size": "10MB",
            "preprocessing": {
                "resize": [224, 224],
                "normalize": True,
                "augmentation": False
            }
        },
        "weed_management": {
            "enabled": True,
            "detection_method": "segmentation",
            "coverage_threshold": 0.1,  # 10% weed coverage triggers action
            "management_actions": {
                "low": "mechanical_removal",
                "medium": "targeted_herbicide",
                "high": "intensive_management"
            }
        },
        "health_monitoring": {
            "enabled": True,
            "scoring_factors": {
                "disease_presence": 0.4,
                "weed_pressure": 0.3,
                "growth_stage": 0.2,
                "environmental_stress": 0.1
            },
            "alert_thresholds": {
                "low_health": 60,
                "critical_health": 40
            }
        },
        "integration_points": {
            "recommendation_engine": True,
            "chatbot_knowledge": True,
            "sensor_data": True,
            "alert_system": True
        },
        "api_endpoints": {
            "/disease/detect": "POST - Image-based disease detection",
            "/weed/assess": "POST - Weed pressure assessment", 
            "/health/score": "GET - Plant health scoring",
            "/treatment/recommend": "POST - Treatment recommendations",
            "/alerts/disease": "GET - Disease alerts",
            "/history/health": "GET - Health history tracking"
        }
    }
    
    with open(BACKEND_DIR / "disease_weed_config.json", "w") as f:
        json.dump(integration_config, f, indent=2)
    
    print("✅ Integration configuration created")
    return integration_config

def test_model_loading():
    """Test if downloaded models can be loaded successfully"""
    print("\n🧪 Testing Model Loading...")
    
    test_results = []
    
    for model_dir in ["mobilenet_disease", "vit_disease", "resnet_disease"]:
        model_path = MODELS_DIR / model_dir
        if model_path.exists():
            try:
                model = AutoModelForImageClassification.from_pretrained(str(model_path))
                processor = AutoImageProcessor.from_pretrained(str(model_path))
                test_results.append({
                    "model": model_dir,
                    "status": "success",
                    "classes": model.config.num_labels if hasattr(model.config, 'num_labels') else "unknown"
                })
                print(f"✅ {model_dir}: Loaded successfully ({test_results[-1]['classes']} classes)")
            except Exception as e:
                test_results.append({
                    "model": model_dir,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ {model_dir}: Loading failed - {e}")
        else:
            print(f"⚠️ {model_dir}: Not found")
    
    with open(MODELS_DIR / "model_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    return test_results

def main():
    """Main setup function"""
    print("🌿 AgriSense Disease & Weed Management Setup")
    print("=" * 50)
    
    # Setup directories
    ensure_directories()
    
    # Download datasets
    disease_datasets = download_disease_datasets()
    weed_datasets = download_weed_datasets()
    
    # Download pre-trained models
    models = download_pretrained_models()
    
    # Create configuration files
    disease_config = create_disease_classes_mapping()
    integration_config = create_integration_config()
    
    # Test model loading
    test_results = test_model_loading()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("=" * 50)
    print(f"📊 Disease Datasets: {len(disease_datasets)}")
    print(f"🌾 Weed Datasets: {len(weed_datasets)}")
    print(f"🤖 Pre-trained Models: {len(models)}")
    print(f"✅ Models Tested: {sum(1 for r in test_results if r['status'] == 'success')}/{len(test_results)}")
    
    print("\n📁 Files Created:")
    print(f"- {DATASETS_DIR}/disease_datasets_info.json")
    print(f"- {DATASETS_DIR}/weed_datasets_info.json")
    print(f"- {MODELS_DIR}/pretrained_models_info.json")
    print(f"- {BACKEND_DIR}/disease_classes.json")
    print(f"- {BACKEND_DIR}/disease_weed_config.json")
    print(f"- {MODELS_DIR}/model_test_results.json")
    
    print("\n🚀 Next Steps:")
    print("1. Run: python agrisense_app/backend/disease_detection.py")
    print("2. Run: python agrisense_app/backend/weed_management.py")
    print("3. Test integration with: python comprehensive_test.py")
    
    if len(disease_datasets) == 0 and len(models) == 0:
        print("\n⚠️ Warning: No datasets or models were downloaded successfully.")
        print("Check your internet connection and Hugging Face access.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)