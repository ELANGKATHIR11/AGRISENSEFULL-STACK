#!/usr/bin/env python3
"""
TensorFlow GPU-Optimized Hybrid AI Training for AgriSense
=========================================================
Focused on TensorFlow with RTX 5060 GPU acceleration
Uses CPU fallback for compatibility while maximizing TensorFlow GPU usage

Author: AgriSense Team  
Date: December 2025
"""

import os
import sys
import json
import time
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import joblib

# TensorFlow with GPU support
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers, callbacks

warnings.filterwarnings('ignore')

# Logging setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("GPU-Optimized Hybrid AI Training - AgriSense")
print("="*70)

# Configure TensorFlow GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info(f"TensorFlow GPU enabled: {len(gpus)} device(s)")
        for gpu in gpus:
            logger.info(f"  - {gpu.name}")
    except RuntimeError as e:
        logger.error(f"GPU configuration error: {e}")
else:
    logger.warning("No GPU detected - using CPU")

# Enable mixed precision for faster training
policy = keras.mixed_precision.Policy('mixed_float16')
keras.mixed_precision.set_global_policy(policy)
logger.info("Mixed precision training enabled (FP16)")

print("="*70 + "\n")


def create_advanced_model(input_dim: int, num_classes: int, model_type: str = 'residual') -> keras.Model:
    """Create advanced neural network architecture"""
    
    inputs = layers.Input(shape=(input_dim,))
    
    if model_type == 'residual':
        # Deep Residual Network
        x = layers.Dense(512, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        # Residual block 1
        residual = layers.Dense(256)(x)
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(256)(x)
        x = layers.Add()([x, residual])
        x = layers.Activation('relu')(x)
        
        # Residual block 2
        residual2 = layers.Dense(128)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(128)(x)
        x = layers.Add()([x, residual2])
        x = layers.Activation('relu')(x)
        
        # Output
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        
    elif model_type == 'attention':
        # Attention-based model
        x = layers.Dense(512, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        
        # Attention mechanism
        attention = layers.Dense(256, activation='tanh')(x)
        attention = layers.Dense(1, activation='softmax')(attention)
        x = layers.Multiply()([x, attention])
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        
    elif model_type == 'efficient':
        # EfficientNet-inspired
        x = layers.Dense(512, activation='swish')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        for units in [256, 256, 128]:
            expanded = layers.Dense(units * 4, activation='swish')(x)
            expanded = layers.BatchNormalization()(expanded)
            expanded = layers.Dropout(0.3)(expanded)
            
            projected = layers.Dense(units)(expanded)
            projected = layers.BatchNormalization()(projected)
            
            if x.shape[-1] == units:
                x = layers.Add()([x, projected])
            else:
                x = projected
        
        x = layers.Dense(64, activation='swish')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
    
    else:
        # Simple deep network
        x = layers.Dense(512, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
    
    outputs = layers.Dense(num_classes, activation='softmax', dtype='float32')(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name=f'{model_type}_model')
    return model


def train_model(X_train, X_val, X_test, y_train, y_val, y_test, 
                num_classes: int, model_name: str, model_type: str) -> Dict:
    """Train a single model"""
    
    logger.info(f"\nTraining {model_name} ({model_type})...")
    logger.info(f"  Input shape: {X_train.shape[1]}, Classes: {num_classes}")
    
    # Create model
    model = create_advanced_model(X_train.shape[1], num_classes, model_type)
    
    # Compile
    model.compile(
        optimizer=optimizers.Adam(learning_rate=0.001),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks
    early_stop = callbacks.EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True,
        verbose=0
    )
    
    lr_scheduler = callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=1e-7,
        verbose=0
    )
    
    # Train
    start_time = time.time()
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=128,
        callbacks=[early_stop, lr_scheduler],
        verbose=0
    )
    training_time = time.time() - start_time
    
    # Evaluate
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='weighted', zero_division=0
    )
    
    logger.info(f"  Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
    logger.info(f"  Training time: {training_time:.2f}s")
    
    return {
        'model': model,
        'history': history.history,
        'test_accuracy': test_acc,
        'test_loss': test_loss,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'training_time': training_time,
        'epochs_trained': len(history.history['loss'])
    }


def main():
    """Main training pipeline"""
    
    # Paths
    dataset_dir = Path("datasets/enhanced")
    output_dir = Path("ml_models/gpu_trained")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = {}
    
    # ============================
    # Disease Detection
    # ============================
    logger.info("\n" + "="*70)
    logger.info("DISEASE DETECTION TRAINING")
    logger.info("="*70)
    
    disease_df = pd.read_csv(dataset_dir / "enhanced_disease_dataset.csv")
    logger.info(f"Dataset: {len(disease_df)} samples, {len(disease_df.columns)} features")
    
    # Find target column
    target_col = 'disease_label' if 'disease_label' in disease_df.columns else [c for c in disease_df.columns if 'label' in c.lower()][0]
    logger.info(f"Target column: {target_col}")
    
    # Prepare data
    X = disease_df.drop(columns=[target_col])
    y = disease_df[target_col]
    
    disease_encoder = LabelEncoder()
    y_encoded = disease_encoder.fit_transform(y)
    num_classes = len(np.unique(y_encoded))
    
    # Split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y_encoded, test_size=0.15, random_state=42, stratify=y_encoded
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
    )
    
    # Scale
    disease_scaler = StandardScaler()
    X_train = disease_scaler.fit_transform(X_train)
    X_val = disease_scaler.transform(X_val)
    X_test = disease_scaler.transform(X_test)
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train models
    disease_results = {}
    for model_type in ['residual', 'attention', 'efficient', 'simple']:
        result = train_model(
            X_train, X_val, X_test, y_train, y_val, y_test,
            num_classes, f'disease_{model_type}', model_type
        )
        disease_results[model_type] = result
    
    results['disease'] = disease_results
    
    # Save best disease model
    best_disease = max(disease_results.items(), key=lambda x: x[1]['test_accuracy'])
    logger.info(f"\nBest disease model: {best_disease[0]} ({best_disease[1]['test_accuracy']*100:.2f}%)")
    
    disease_dir = output_dir / 'disease_detection'
    disease_dir.mkdir(parents=True, exist_ok=True)
    
    best_disease[1]['model'].save(disease_dir / f'disease_best_{timestamp}.keras')
    joblib.dump(disease_scaler, disease_dir / f'disease_scaler_{timestamp}.joblib')
    joblib.dump(disease_encoder, disease_dir / f'disease_encoder_{timestamp}.joblib')
    
    # ============================
    # Weed Management
    # ============================
    logger.info("\n" + "="*70)
    logger.info("WEED MANAGEMENT TRAINING")
    logger.info("="*70)
    
    weed_df = pd.read_csv(dataset_dir / "enhanced_weed_dataset.csv")
    logger.info(f"Dataset: {len(weed_df)} samples, {len(weed_df.columns)} features")
    
    # Find target column
    target_col = 'weed_label' if 'weed_label' in weed_df.columns else [c for c in weed_df.columns if 'label' in c.lower()][0]
    logger.info(f"Target column: {target_col}")
    
    # Prepare data
    X = weed_df.drop(columns=[target_col])
    y = weed_df[target_col]
    
    weed_encoder = LabelEncoder()
    y_encoded = weed_encoder.fit_transform(y)
    num_classes = len(np.unique(y_encoded))
    
    # Split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y_encoded, test_size=0.15, random_state=42, stratify=y_encoded
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
    )
    
    # Scale
    weed_scaler = StandardScaler()
    X_train = weed_scaler.fit_transform(X_train)
    X_val = weed_scaler.transform(X_val)
    X_test = weed_scaler.transform(X_test)
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train models
    weed_results = {}
    for model_type in ['residual', 'attention', 'efficient', 'simple']:
        result = train_model(
            X_train, X_val, X_test, y_train, y_val, y_test,
            num_classes, f'weed_{model_type}', model_type
        )
        weed_results[model_type] = result
    
    results['weed'] = weed_results
    
    # Save best weed model
    best_weed = max(weed_results.items(), key=lambda x: x[1]['test_accuracy'])
    logger.info(f"\nBest weed model: {best_weed[0]} ({best_weed[1]['test_accuracy']*100:.2f}%)")
    
    weed_dir = output_dir / 'weed_management'
    weed_dir.mkdir(parents=True, exist_ok=True)
    
    best_weed[1]['model'].save(weed_dir / f'weed_best_{timestamp}.keras')
    joblib.dump(weed_scaler, weed_dir / f'weed_scaler_{timestamp}.joblib')
    joblib.dump(weed_encoder, weed_dir / f'weed_encoder_{timestamp}.joblib')
    
    # ============================
    # Summary
    # ============================
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE!")
    logger.info("="*70)
    logger.info(f"\nDisease Detection:")
    for model_type, result in disease_results.items():
        logger.info(f"  {model_type:12s}: {result['test_accuracy']:.4f} ({result['test_accuracy']*100:.2f}%)")
    
    logger.info(f"\nWeed Management:")
    for model_type, result in weed_results.items():
        logger.info(f"  {model_type:12s}: {result['test_accuracy']:.4f} ({result['test_accuracy']*100:.2f}%)")
    
    logger.info(f"\nModels saved to: {output_dir}")
    logger.info("="*70)
    
    # Save summary
    summary = {
        'timestamp': timestamp,
        'disease': {k: {
            'accuracy': v['test_accuracy'],
            'precision': v['precision'],
            'recall': v['recall'],
            'f1_score': v['f1_score'],
            'training_time': v['training_time']
        } for k, v in disease_results.items()},
        'weed': {k: {
            'accuracy': v['test_accuracy'],
            'precision': v['precision'],
            'recall': v['recall'],
            'f1_score': v['f1_score'],
            'training_time': v['training_time']
        } for k, v in weed_results.items()}
    }
    
    with open(output_dir / f'training_summary_{timestamp}.json', 'w') as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        sys.exit(1)
