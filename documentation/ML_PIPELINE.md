"""
ML Pipeline Documentation for AgriSense
==========================================

This document describes the machine learning pipeline, training procedures,
model versioning, and performance metrics for the AgriSense platform.

## Model Inventory

### 1. Water Recommendation Model
- **Type**: Neural Network (TensorFlow Keras)
- **Primary File**: `core/water_model.keras`
- **Fallback**: `core/water_model.joblib` (scikit-learn)
- **Input Features**: 
  - Soil moisture (%), Temperature (°C), pH, EC (dS/m)
  - Crop type (encoded), Soil type (encoded), Area (m²)
  - NPK levels (ppm), Weather data
- **Output**: Water requirement (liters)
- **Current Version**: 2.1.0
- **Performance**: MAE: 2.3L, RMSE: 3.1L, R²: 0.89

### 2. Fertilizer Recommendation Model
- **Type**: Neural Network (TensorFlow Keras)
- **Primary File**: `core/fert_model.keras`
- **Fallback**: `core/fert_model.joblib`
- **Input Features**: Similar to water model
- **Output**: N, P, K requirements (grams)
- **Current Version**: 2.0.1
- **Performance**: MAE: 15g, RMSE: 22g, R²: 0.85

### 3. Disease Detection Model
- **Type**: Computer Vision (CNN)
- **Files**: 
  - `disease_model_enhanced.joblib`
  - `disease_encoder_enhanced.joblib`
  - `disease_scaler_20250913_172116.joblib`
- **Input**: Plant leaf images (224x224 RGB)
- **Output**: Disease classification + confidence
- **Classes**: 38 plant diseases
- **Current Version**: 3.2.0
- **Performance**: Accuracy: 94.2%, F1: 0.93

### 4. Weed Management Model
- **Type**: Computer Vision + Classification
- **Files**:
  - `weed_model_enhanced.joblib`
  - `weed_encoder_enhanced.joblib`
  - `weed_scaler_20250913_172117.joblib`
- **Input**: Field images
- **Output**: Weed species + density + recommendations
- **Classes**: 12 common weed species
- **Current Version**: 2.5.0
- **Performance**: Accuracy: 91.8%, mAP: 0.88

### 5. Crop Recommendation System
- **Type**: Multi-class classifier
- **File**: `feature_encoders.joblib`
- **Input**: Soil parameters, climate data, region
- **Output**: Top 5 suitable crops with scores
- **Database**: 2000+ crop varieties
- **Current Version**: 1.8.0
- **Performance**: Top-5 Accuracy: 96.5%

### 6. Chatbot NLP System
- **Type**: Sentence-BERT + BM25 Hybrid
- **Files**:
  - `chatbot_qa_pairs.json` (5000+ Q&A pairs)
  - `chatbot_index.npz` (embeddings)
  - `chatbot_index.json` (metadata)
- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Current Version**: 1.5.0
- **Performance**: Recall@3: 0.87, MRR: 0.79

## Training Pipeline

### Directory Structure
```
ml_models/
├── disease_detection/
│   ├── artifacts/
│   │   └── v3.2.0/
│   ├── training_data/
│   └── scripts/
├── weed_management/
│   ├── artifacts/
│   │   └── v2.5.0/
│   ├── training_data/
│   └── scripts/
├── core_models/
│   ├── water/
│   │   └── v2.1.0/
│   └── fertilizer/
│       └── v2.0.1/
└── crop_recommendation/
    └── v1.8.0/
```

### Training Scripts

#### 1. Water/Fertilizer Models
```bash
# Train water model
python scripts/ml_training/train_water_model.py \
    --data datasets/sensor_readings.csv \
    --epochs 100 \
    --batch-size 32 \
    --output ml_models/core_models/water/v2.1.0/

# Train fertilizer model
python scripts/ml_training/train_fert_model.py \
    --data datasets/fertilizer_data.csv \
    --epochs 100 \
    --output ml_models/core_models/fertilizer/v2.0.1/
```

#### 2. Disease Detection
```bash
python scripts/ml_training/train_disease_model.py \
    --data datasets/disease_detection/train/ \
    --val-data datasets/disease_detection/val/ \
    --model efficientnet_b0 \
    --epochs 50 \
    --output ml_models/disease_detection/artifacts/v3.2.0/
```

#### 3. Weed Management
```bash
python scripts/ml_training/train_weed_model.py \
    --data datasets/weed_management/ \
    --architecture yolov8 \
    --epochs 100 \
    --output ml_models/weed_management/artifacts/v2.5.0/
```

#### 4. Chatbot Training
```bash
python scripts/build_chatbot_artifacts.py \
    --csv datasets/chatbot/merged_chatbot_training_dataset.csv \
    --out-dir agrisense_app/backend \
    --model sentence-transformers/all-MiniLM-L6-v2
```

## Model Versioning

### Semantic Versioning Format
`MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes, incompatible model architecture
- **MINOR**: New features, improved accuracy, backward compatible
- **PATCH**: Bug fixes, minor improvements

### Metadata File Format
Each model version must include `metadata.json`:
```json
{
  "model_name": "water_recommendation",
  "version": "2.1.0",
  "trained_on": "2025-09-15T10:30:00Z",
  "training_duration": "2h 15m",
  "dataset_size": 125000,
  "framework": "tensorflow",
  "architecture": "dense_nn_4layer",
  "hyperparameters": {
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100,
    "optimizer": "adam"
  },
  "performance_metrics": {
    "mae": 2.3,
    "rmse": 3.1,
    "r2_score": 0.89,
    "test_samples": 25000
  },
  "commit_hash": "a3b4c5d6",
  "trained_by": "ml-training-pipeline",
  "production_ready": true
}
```

## Performance Benchmarks

### Inference Latency (ms)
- Water/Fertilizer prediction: 15-25ms
- Disease detection (single image): 80-120ms
- Weed classification: 100-150ms
- Chatbot response: 50-80ms
- Crop recommendation: 10-20ms

### Throughput
- API requests/second: 100-150 (single instance)
- Concurrent disease detections: 10-15
- Concurrent chatbot queries: 50-70

## Model Deployment

### Production Deployment Checklist
- [ ] Train model with full dataset
- [ ] Validate on held-out test set
- [ ] Generate metadata.json
- [ ] Run smoke tests (scripts/smoke_ml_infer.py)
- [ ] Version artifacts (MAJOR.MINOR.PATCH)
- [ ] Update model path in code
- [ ] Run integration tests
- [ ] Deploy to staging
- [ ] Monitor metrics for 24h
- [ ] Deploy to production
- [ ] Update documentation

### Rollback Procedure
1. Stop application
2. Restore previous model artifacts
3. Update version in code
4. Restart application
5. Verify health checks
6. Monitor error rates

## Continuous Improvement

### Model Retraining Schedule
- **Water/Fertilizer**: Quarterly (or when MAE > 5L)
- **Disease Detection**: Bi-annually (or when accuracy < 90%)
- **Weed Management**: Bi-annually
- **Chatbot**: Monthly (new Q&A pairs)
- **Crop Recommendation**: Annually

### Data Collection
- Sensor readings: Continuous (PostgreSQL/MongoDB)
- User feedback: Via feedback API endpoints
- Performance metrics: Prometheus/Grafana
- Error logs: Sentry

### Model Monitoring Alerts
- Accuracy drop > 5%
- Latency increase > 50%
- Error rate > 2%
- Memory usage > 85%

## Testing

### Unit Tests
```bash
pytest tests/ml/ -v --cov=agrisense_app.backend.core
```

### Integration Tests
```bash
pytest tests/integration/test_ml_pipeline.py -v
```

### Smoke Tests
```bash
python scripts/smoke_ml_infer.py
```

## Tools and Infrastructure

### Training Environment
- Python 3.9+
- CUDA 11.8 (for GPU training)
- 16GB RAM minimum
- 50GB storage

### Model Registry
- Local filesystem (development)
- S3/Azure Blob (production)
- Model versioning via Git LFS

### Experiment Tracking
- MLflow (optional)
- TensorBoard logs
- Weights & Biases (optional)

## References

- Training datasets: `/datasets`
- Model artifacts: `/ml_models`
- Training scripts: `/scripts/ml_training`
- Evaluation notebooks: `/notebooks/ml_evaluation`
