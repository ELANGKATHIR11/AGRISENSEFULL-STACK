# 🗂️ AgriSense File Organization Index

This file provides a comprehensive guide to the newly organized AgriSense project structure for easy navigation and access.

## 📁 **Directory Structure Overview**

```
AGRISENSEFULL-STACK/
├── 🤖 ml_models/              # Machine Learning Models & Artifacts
├── 🎯 training_scripts/       # Model Training & Pipeline Scripts  
├── 📊 datasets/               # All Dataset Files (Raw, Enhanced, Chatbot)
├── 🔍 data_processing/        # Data Enhancement & Analysis Scripts
├── 🧪 api_tests/              # API Testing & Integration Tests
├── 📚 documentation/          # Project Documentation & Plans
├── 📈 reports/                # Analysis Reports & Results
├── ⚙️ configuration/          # Configuration Files & Environment
├── 🏗️ agrisense_app/          # Main Application Code
├── 🔌 agrisense_pi_edge_minimal/ # Edge Computing Components
├── 💡 AGRISENSE_IoT/          # IoT Backend & Components
└── 📄 scripts/                # Utility & Helper Scripts
```

---

## 🤖 **ML Models** (`ml_models/`)

### Disease Detection Models (`disease_detection/`)
- `disease_encoder_20250913_172116.joblib` - Feature encoder for disease detection
- `disease_model_20250913_172116.joblib` - Trained disease classification model
- `disease_scaler_20250913_172116.joblib` - Data scaler for disease features

### Weed Management Models (`weed_management/`)
- `weed_encoder_20250913_172117.joblib` - Feature encoder for weed classification
- `weed_model_20250913_172117.joblib` - Trained weed management model
- `weed_scaler_20250913_172117.joblib` - Data scaler for weed features

### Crop Recommendation Models (`crop_recommendation/`)
- `best_crop_tf.keras` - TensorFlow model for crop recommendation
- `best_yield_tf.keras` - TensorFlow model for yield prediction

### General Models
- `feature_encoders.joblib` - General feature encoders

---

## 🎯 **Training Scripts** (`training_scripts/`)

### Main Training Pipelines
- `train_plant_health_models_v2.py` - Enhanced plant health model trainer
- `train_plant_health_models.py` - Legacy compatibility trainer
- `deep_learning_pipeline.py` - Deep learning training pipeline
- `deep_learning_pipeline_v2.py` - Enhanced deep learning pipeline

### Ensemble & Advanced Training
- `advanced_ensemble_trainer.py` - Advanced ensemble model training
- `phase2_ensemble_trainer.py` - Phase 2 ensemble training
- `quick_ml_trainer.py` - Quick ML model training utility

### Setup & Configuration
- `setup_disease_weed_models.py` - Disease & weed model setup script

---

## 📊 **Datasets** (`datasets/`)

### Raw Datasets (`raw/`)
- `crop_disease_dataset.csv` - Raw crop disease data
- `data_core.csv` - Core agricultural data
- `sikkim_crop_dataset.csv` - Sikkim region crop data
- `weed_management_dataset.csv` - Weed management data
- `qa_weeds_diseases.csv` - Q&A data for weeds and diseases
- `weather_cache.csv` - Weather data cache

### Enhanced Datasets (`enhanced/`)
- `enhanced_chatbot_training_dataset.csv` - Enhanced chatbot training data
- `enhanced_disease_dataset.csv` - Enhanced disease detection data
- `enhanced_weed_dataset.csv` - Enhanced weed classification data

### Chatbot Datasets (`chatbot/`)
- `Farming_FAQ_Assistant_Dataset.csv` - Farming FAQ dataset
- `merged_chatbot_training_dataset.csv` - Merged chatbot training data

---

## 🔍 **Data Processing** (`data_processing/`)

### Data Enhancement
- `advanced_data_enhancer.py` - Advanced data augmentation & enhancement
- `analyze_datasets.py` - Dataset analysis & statistics
- `performance_optimization.py` - Performance optimization utilities

### ML Analysis
- `ml_optimization_analyzer.py` - ML model optimization analysis
- `integrate_backend_models.py` - Backend model integration script

---

## 🧪 **API Tests** (`api_tests/`)

### Comprehensive Testing
- `comprehensive_api_test.py` - Full API testing suite
- `comprehensive_test.py` - Comprehensive system tests
- `test_api_integration.py` - API integration tests
- `test_api.py` - Basic API tests

### Specialized Testing
- `test_plant_health_api.py` - Plant health API tests
- `test_plant_health_integration.py` - Plant health integration tests
- `quick_plant_health_test.py` - Quick plant health testing
- `test_integration.py` - General integration tests

---

## 📚 **Documentation** (`documentation/`)

### Main Documentation
- `README.md` - Main project README
- `README_AZURE.md` - Azure deployment documentation
- `README_RUN.md` - Running instructions
- `PROJECT_DOCUMENTATION.md` - Comprehensive project documentation

### Planning & Architecture
- `DISEASE_WEED_INTEGRATION_PLAN.md` - Disease & weed integration plan
- `HACKATHON_UPGRADE_PLAN.md` - Hackathon upgrade plan
- `optimization_roadmap.md` - Optimization roadmap

---

## 📈 **Reports** (`reports/`)

### Success Reports
- `100_PERCENT_SUCCESS_REPORT.md` - 100% success achievement report
- `FINAL_PROJECT_REPORT.md` - Final project completion report
- `ML_OPTIMIZATION_SUCCESS_REPORT.md` - ML optimization success report
- `data_enhancement_report.md` - Data enhancement analysis report

### Analysis Results
- `ml_optimization_analysis.json` - ML optimization analysis results
- `optimization_report.json` - Optimization report data
- `test_results.json` - Testing results data

---

## ⚙️ **Configuration** (`configuration/`)

### Environment & Setup
- `.env` - Environment variables
- `.env.example` - Environment variables template
- `pyrightconfig.json` - Pyright type checker configuration
- `azure.yaml` - Azure deployment configuration

### Build & Deployment
- `Dockerfile` - Docker container configuration
- `.dockerignore` - Docker ignore rules
- `.gitignore` - Git ignore rules
- `.gitattributes` - Git attributes configuration

---

## 🚀 **Quick Access Commands**

### Training New Models
```bash
# Train plant health models
python training_scripts/train_plant_health_models_v2.py

# Run deep learning pipeline
python training_scripts/deep_learning_pipeline_v2.py

# Quick ML training
python training_scripts/quick_ml_trainer.py
```

### Testing APIs
```bash
# Comprehensive API testing
python api_tests/comprehensive_api_test.py

# Plant health specific tests
python api_tests/test_plant_health_api.py

# Quick health check
python api_tests/quick_plant_health_test.py
```

### Data Processing
```bash
# Enhance datasets
python data_processing/advanced_data_enhancer.py

# Analyze datasets
python data_processing/analyze_datasets.py

# Optimize performance
python data_processing/performance_optimization.py
```

---

## 📋 **Benefits of This Organization**

✅ **Easy Navigation** - Logical folder structure with clear categorization
✅ **Quick Access** - All related files grouped together
✅ **Maintainability** - Easy to find and update specific components
✅ **Scalability** - Room for growth in each category
✅ **Professional Structure** - Industry-standard organization
✅ **Documentation** - Clear documentation of what goes where

---

## 🎯 **Next Steps**

1. **Update Import Paths** - Update any hardcoded file paths in scripts
2. **Update Documentation** - Reference new file locations in docs
3. **Test Functionality** - Ensure all moved files work correctly
4. **Version Control** - Commit the new organized structure

---

*Generated on: September 13, 2025*
*AgriSense Project - Organized for Maximum Efficiency* 🌾