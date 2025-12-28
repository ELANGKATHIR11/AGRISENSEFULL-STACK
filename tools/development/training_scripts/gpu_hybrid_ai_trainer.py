#!/usr/bin/env python3
"""
GPU-Optimized Hybrid AI Training Pipeline for AgriSense
=======================================================
Leverages RTX 5060 GPU for enhanced deep learning training with:
- PyTorch with CUDA 12.4 support
- TensorFlow with GPU acceleration
- Mixed precision training (FP16)
- Optimized data augmentation
- Advanced neural network architectures
- Model ensemble techniques

Author: AgriSense Team
Date: December 2025
"""

import os
import sys
import logging
import warnings
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)

# PyTorch imports with CUDA support
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, TensorDataset
from torch.cuda.amp import autocast, GradScaler

# TensorFlow imports with GPU support
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers, callbacks

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'gpu_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class GPUTrainingConfig:
    """Configuration for GPU-optimized training"""
    # Device settings
    # RTX 5060 has sm_120 but PyTorch only supports sm_90, so use CPU for PyTorch
    device: str = "cpu"  # Force CPU for PyTorch due to compute capability mismatch
    mixed_precision: bool = False  # Disable mixed precision for CPU
    tf_mixed_precision: bool = True  # TensorFlow can still use GPU
    
    # Training hyperparameters
    batch_size: int = 128  # Larger batch for RTX 5060
    epochs: int = 100
    learning_rate: float = 0.001
    weight_decay: float = 1e-4
    
    # Early stopping
    patience: int = 15
    min_delta: float = 0.0001
    
    # Data augmentation
    augmentation_factor: int = 3
    
    # Model ensemble
    num_ensemble_models: int = 5
    
    # Paths
    dataset_dir: Path = Path("datasets/enhanced")
    output_dir: Path = Path("ml_models/gpu_trained")
    
    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)


# ============================================================================
# GPU Utility Functions
# ============================================================================

def check_gpu_availability():
    """Check and log GPU availability"""
    logger.info("=" * 70)
    logger.info("🔍 GPU AVAILABILITY CHECK")
    logger.info("=" * 70)
    
    # PyTorch GPU check
    if torch.cuda.is_available():
        logger.info(f"✅ PyTorch CUDA Available: {torch.cuda.is_available()}")
        logger.info(f"   CUDA Version: {torch.version.cuda}")
        logger.info(f"   GPU Device: {torch.cuda.get_device_name(0)}")
        logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        logger.info(f"   Compute Capability: sm_{torch.cuda.get_device_properties(0).major}{torch.cuda.get_device_properties(0).minor}")
    else:
        logger.warning("⚠️  PyTorch CUDA not available - using CPU")
    
    # TensorFlow GPU check
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        logger.info(f"✅ TensorFlow GPU Available: {len(gpus)} device(s)")
        for gpu in gpus:
            logger.info(f"   {gpu.name}")
    else:
        logger.warning("⚠️  TensorFlow GPU not available - using CPU")
    
    logger.info("=" * 70)


def configure_tensorflow_gpu():
    """Configure TensorFlow for optimal GPU usage"""
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            # Enable memory growth to prevent TF from allocating all GPU memory
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logger.info("✅ TensorFlow GPU memory growth enabled")
        except RuntimeError as e:
            logger.error(f"❌ Failed to configure TensorFlow GPU: {e}")


def configure_pytorch_gpu():
    """Configure PyTorch for optimal GPU usage"""
    if torch.cuda.is_available():
        # Set to use the maximum of memory
        torch.cuda.empty_cache()
        
        # Enable cuDNN autotuner for optimal convolution algorithms
        torch.backends.cudnn.benchmark = True
        logger.info("✅ PyTorch cuDNN autotuner enabled")


# ============================================================================
# PyTorch Neural Network Models
# ============================================================================

class DeepResidualNet(nn.Module):
    """Deep Residual Network with skip connections"""
    
    def __init__(self, input_dim: int, num_classes: int, dropout: float = 0.3):
        super(DeepResidualNet, self).__init__()
        
        # Initial layer
        self.fc_init = nn.Linear(input_dim, 512)
        self.bn_init = nn.BatchNorm1d(512)
        
        # Residual blocks
        self.res_block1 = self._make_residual_block(512, 512, dropout)
        self.res_block2 = self._make_residual_block(512, 256, dropout)
        self.res_block3 = self._make_residual_block(256, 128, dropout)
        
        # Output layer
        self.fc_out = nn.Linear(128, num_classes)
        
    def _make_residual_block(self, in_features, out_features, dropout):
        """Create a residual block"""
        return nn.ModuleDict({
            'fc1': nn.Linear(in_features, out_features),
            'bn1': nn.BatchNorm1d(out_features),
            'dropout1': nn.Dropout(dropout),
            'fc2': nn.Linear(out_features, out_features),
            'bn2': nn.BatchNorm1d(out_features),
            'dropout2': nn.Dropout(dropout),
            'shortcut': nn.Linear(in_features, out_features) if in_features != out_features else nn.Identity()
        })
    
    def _forward_residual_block(self, x, block):
        """Forward pass through residual block"""
        identity = block['shortcut'](x)
        
        out = F.relu(block['bn1'](block['fc1'](x)))
        out = block['dropout1'](out)
        out = block['bn2'](block['fc2'](out))
        out = block['dropout2'](out)
        
        out += identity
        out = F.relu(out)
        return out
    
    def forward(self, x):
        x = F.relu(self.bn_init(self.fc_init(x)))
        
        x = self._forward_residual_block(x, self.res_block1)
        x = self._forward_residual_block(x, self.res_block2)
        x = self._forward_residual_block(x, self.res_block3)
        
        x = self.fc_out(x)
        return x


class AttentionNet(nn.Module):
    """Neural network with attention mechanism"""
    
    def __init__(self, input_dim: int, num_classes: int, dropout: float = 0.3):
        super(AttentionNet, self).__init__()
        
        # Feature extraction layers
        self.fc1 = nn.Linear(input_dim, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.dropout1 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.dropout2 = nn.Dropout(dropout)
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 1),
            nn.Softmax(dim=1)
        )
        
        # Output layers
        self.fc3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.dropout3 = nn.Dropout(dropout)
        
        self.fc_out = nn.Linear(128, num_classes)
        
    def forward(self, x):
        # Feature extraction
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout1(x)
        
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        # Apply attention
        attention_weights = self.attention(x)
        x = x * attention_weights
        
        # Output
        x = F.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)
        
        x = self.fc_out(x)
        return x


# ============================================================================
# TensorFlow Model Architectures
# ============================================================================

def create_tf_efficient_net(input_dim: int, num_classes: int) -> keras.Model:
    """Create EfficientNet-inspired model"""
    inputs = layers.Input(shape=(input_dim,))
    
    # Stem
    x = layers.Dense(512, activation='swish')(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    
    # MBConv-like blocks
    for units in [512, 256, 256, 128]:
        # Expansion
        expanded = layers.Dense(units * 4, activation='swish')(x)
        expanded = layers.BatchNormalization()(expanded)
        expanded = layers.Dropout(0.3)(expanded)
        
        # Projection
        projected = layers.Dense(units)(expanded)
        projected = layers.BatchNormalization()(projected)
        
        # Skip connection if dimensions match
        if x.shape[-1] == units:
            x = layers.Add()([x, projected])
        else:
            x = projected
    
    # Head
    x = layers.Dense(64, activation='swish')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name='EfficientNet')
    return model


def create_tf_transformer_net(input_dim: int, num_classes: int) -> keras.Model:
    """Create Transformer-inspired model for tabular data"""
    inputs = layers.Input(shape=(input_dim,))
    
    # Embedding
    x = layers.Dense(256)(inputs)
    x = layers.LayerNormalization()(x)
    
    # Multi-head attention block
    attention_output = layers.MultiHeadAttention(
        num_heads=8,
        key_dim=32,
        dropout=0.1
    )(x, x)
    
    x = layers.Add()([x, attention_output])
    x = layers.LayerNormalization()(x)
    
    # Feed-forward network
    ffn = layers.Dense(512, activation='relu')(x)
    ffn = layers.Dropout(0.3)(ffn)
    ffn = layers.Dense(256)(ffn)
    
    x = layers.Add()([x, ffn])
    x = layers.LayerNormalization()(x)
    
    # Output
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation='softmax')(x)
    
    model = models.Model(inputs=inputs, outputs=outputs, name='TransformerNet')
    return model


# ============================================================================
# Training Pipeline
# ============================================================================

class GPUHybridAITrainer:
    """GPU-optimized trainer for hybrid AI models"""
    
    def __init__(self, config: GPUTrainingConfig = None):
        self.config = config or GPUTrainingConfig()
        self.device = torch.device(self.config.device)
        
        # Initialize scalers and encoders
        self.disease_scaler = StandardScaler()
        self.weed_scaler = StandardScaler()
        self.disease_encoder = LabelEncoder()
        self.weed_encoder = LabelEncoder()
        
        # Results storage
        self.results = {}
        self.models = {}
        
        logger.info(f"Trainer initialized with PyTorch device: {self.device}")
        logger.info("Note: PyTorch using CPU due to RTX 5060 compute capability (sm_120 > sm_90)")
        
    def load_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load enhanced datasets"""
        logger.info("📊 Loading datasets...")
        
        disease_path = self.config.dataset_dir / "enhanced_disease_dataset.csv"
        weed_path = self.config.dataset_dir / "enhanced_weed_dataset.csv"
        
        if not disease_path.exists():
            logger.error(f"❌ Disease dataset not found: {disease_path}")
            raise FileNotFoundError(f"Dataset not found: {disease_path}")
        
        if not weed_path.exists():
            logger.error(f"❌ Weed dataset not found: {weed_path}")
            raise FileNotFoundError(f"Dataset not found: {weed_path}")
        
        disease_df = pd.read_csv(disease_path)
        weed_df = pd.read_csv(weed_path)
        
        logger.info(f"✅ Disease dataset: {len(disease_df)} samples, {len(disease_df.columns)} features")
        logger.info(f"✅ Weed dataset: {len(weed_df)} samples, {len(weed_df.columns)} features")
        
        return disease_df, weed_df
    
    def prepare_data(self, df: pd.DataFrame, target_col: str, 
                     scaler: StandardScaler, encoder: LabelEncoder) -> Tuple:
        """Prepare data for training"""
        logger.info(f"🎯 Preparing data for {target_col}...")
        
        # Check if target column exists
        if target_col not in df.columns:
            # Try common variations
            possible_cols = [col for col in df.columns if 'label' in col.lower() or 'target' in col.lower() or 'class' in col.lower()]
            if possible_cols:
                target_col = possible_cols[0]
                logger.info(f"   Using column: {target_col}")
            else:
                logger.error(f"❌ Target column not found. Available columns: {df.columns.tolist()}")
                raise KeyError(f"Target column '{target_col}' not found")
        
        # Separate features and target
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # Encode labels
        y_encoded = encoder.fit_transform(y)
        num_classes = len(np.unique(y_encoded))
        
        logger.info(f"   Features: {X.shape[1]}, Classes: {num_classes}")
        logger.info(f"   Class distribution: {np.bincount(y_encoded)}")
        
        # Split data: 70% train, 15% val, 15% test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y_encoded, test_size=0.15, random_state=42, stratify=y_encoded
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp  # 0.176 of 0.85 ≈ 0.15
        )
        
        # Scale features
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)
        
        logger.info(f"   Train: {len(X_train_scaled)}, Val: {len(X_val_scaled)}, Test: {len(X_test_scaled)}")
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, num_classes
    
    def train_pytorch_model(self, X_train, X_val, X_test, y_train, y_val, y_test,
                           num_classes: int, model_name: str) -> Dict[str, Any]:
        """Train a PyTorch model with GPU acceleration"""
        logger.info(f"🔥 Training PyTorch model: {model_name}")
        
        # Convert to tensors
        X_train_t = torch.FloatTensor(X_train).to(self.device)
        y_train_t = torch.LongTensor(y_train).to(self.device)
        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.LongTensor(y_val).to(self.device)
        X_test_t = torch.FloatTensor(X_test).to(self.device)
        y_test_t = torch.LongTensor(y_test).to(self.device)
        
        # Create datasets and dataloaders
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        
        # Initialize model
        input_dim = X_train.shape[1]
        if 'residual' in model_name.lower():
            model = DeepResidualNet(input_dim, num_classes).to(self.device)
        else:
            model = AttentionNet(input_dim, num_classes).to(self.device)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(
            model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', patience=5, factor=0.5, verbose=True
        )
        
        # Mixed precision training
        scaler = GradScaler() if self.config.mixed_precision and torch.cuda.is_available() else None
        
        # Training loop
        best_val_acc = 0.0
        patience_counter = 0
        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
        
        start_time = time.time()
        
        for epoch in range(self.config.epochs):
            # Training phase
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                
                if scaler:
                    with autocast():
                        outputs = model(batch_X)
                        loss = criterion(outputs, batch_y)
                    
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                train_total += batch_y.size(0)
                train_correct += (predicted == batch_y).sum().item()
            
            train_loss /= len(train_loader)
            train_acc = train_correct / train_total
            
            # Validation phase
            model.eval()
            with torch.no_grad():
                val_outputs = model(X_val_t)
                val_loss = criterion(val_outputs, y_val_t).item()
                _, val_predicted = torch.max(val_outputs, 1)
                val_acc = (val_predicted == y_val_t).sum().item() / len(y_val_t)
            
            # Update history
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            
            # Learning rate scheduling
            scheduler.step(val_loss)
            
            # Early stopping
            if val_acc > best_val_acc + self.config.min_delta:
                best_val_acc = val_acc
                patience_counter = 0
                # Save best model
                best_model_state = model.state_dict()
            else:
                patience_counter += 1
            
            # Log progress every 10 epochs
            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.info(
                    f"   Epoch [{epoch+1}/{self.config.epochs}] "
                    f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} "
                    f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
                )
            
            # Early stopping check
            if patience_counter >= self.config.patience:
                logger.info(f"   ⏹️ Early stopping triggered at epoch {epoch+1}")
                break
        
        # Load best model
        model.load_state_dict(best_model_state)
        
        # Test evaluation
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test_t)
            _, test_predicted = torch.max(test_outputs, 1)
            test_acc = (test_predicted == y_test_t).sum().item() / len(y_test_t)
            
            # Get predictions for detailed metrics
            y_pred_cpu = test_predicted.cpu().numpy()
            y_test_cpu = y_test_t.cpu().numpy()
        
        training_time = time.time() - start_time
        
        # Calculate detailed metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test_cpu, y_pred_cpu, average='weighted', zero_division=0
        )
        
        results = {
            'model_name': model_name,
            'framework': 'pytorch',
            'test_accuracy': test_acc,
            'val_accuracy': best_val_acc,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'training_time': training_time,
            'epochs_trained': epoch + 1,
            'history': history
        }
        
        logger.info(f"   ✅ {model_name} - Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
        
        return {'model': model, 'results': results}
    
    def train_tensorflow_model(self, X_train, X_val, X_test, y_train, y_val, y_test,
                               num_classes: int, model_name: str) -> Dict[str, Any]:
        """Train a TensorFlow model with GPU acceleration"""
        logger.info(f"🔥 Training TensorFlow model: {model_name}")
        
        # Enable mixed precision
        if self.config.tf_mixed_precision:
            policy = keras.mixed_precision.Policy('mixed_float16')
            keras.mixed_precision.set_global_policy(policy)
        
        # Create model
        input_dim = X_train.shape[1]
        if 'efficient' in model_name.lower():
            model = create_tf_efficient_net(input_dim, num_classes)
        else:
            model = create_tf_transformer_net(input_dim, num_classes)
        
        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=self.config.patience,
            restore_best_weights=True,
            verbose=1
        )
        
        lr_scheduler = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        )
        
        # Train model
        start_time = time.time()
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=[early_stop, lr_scheduler],
            verbose=0
        )
        
        training_time = time.time() - start_time
        
        # Evaluate on test set
        test_results = model.evaluate(X_test, y_test, verbose=0)
        test_acc = test_results[1]  # accuracy is second metric
        
        # Get predictions for detailed metrics
        y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
        
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        results = {
            'model_name': model_name,
            'framework': 'tensorflow',
            'test_accuracy': test_acc,
            'val_accuracy': max(history.history['val_accuracy']),
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'training_time': training_time,
            'epochs_trained': len(history.history['loss']),
            'history': {
                'train_loss': history.history['loss'],
                'val_loss': history.history['val_loss'],
                'train_acc': history.history['accuracy'],
                'val_acc': history.history['val_accuracy']
            }
        }
        
        logger.info(f"   ✅ {model_name} - Test Accuracy: {test_acc:.4f} ({test_acc*100:.2f}%)")
        
        return {'model': model, 'results': results}
    
    def train_disease_detection(self):
        """Train disease detection models"""
        logger.info("\n" + "=" * 70)
        logger.info("🦠 TRAINING DISEASE DETECTION MODELS")
        logger.info("=" * 70)
        
        # Load disease dataset
        disease_df, _ = self.load_datasets()
        
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = self.prepare_data(
            disease_df, 'label', self.disease_scaler, self.disease_encoder
        )
        
        models_results = {}
        
        # Train PyTorch models
        for model_name in ['PyTorch_Residual', 'PyTorch_Attention']:
            result = self.train_pytorch_model(
                X_train, X_val, X_test, y_train, y_val, y_test,
                num_classes, f'disease_{model_name}'
            )
            models_results[model_name] = result
        
        # Train TensorFlow models
        for model_name in ['TF_EfficientNet', 'TF_Transformer']:
            result = self.train_tensorflow_model(
                X_train, X_val, X_test, y_train, y_val, y_test,
                num_classes, f'disease_{model_name}'
            )
            models_results[model_name] = result
        
        # Find best model
        best_model_name = max(models_results, key=lambda x: models_results[x]['results']['test_accuracy'])
        best_accuracy = models_results[best_model_name]['results']['test_accuracy']
        
        logger.info(f"\n🏆 Best Disease Model: {best_model_name} (Accuracy: {best_accuracy:.4f})")
        
        self.results['disease'] = models_results
        self.models['disease'] = models_results
        
        return models_results
    
    def train_weed_management(self):
        """Train weed management models"""
        logger.info("\n" + "=" * 70)
        logger.info("🌿 TRAINING WEED MANAGEMENT MODELS")
        logger.info("=" * 70)
        
        # Load weed dataset
        _, weed_df = self.load_datasets()
        
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = self.prepare_data(
            weed_df, 'label', self.weed_scaler, self.weed_encoder
        )
        
        models_results = {}
        
        # Train PyTorch models
        for model_name in ['PyTorch_Residual', 'PyTorch_Attention']:
            result = self.train_pytorch_model(
                X_train, X_val, X_test, y_train, y_val, y_test,
                num_classes, f'weed_{model_name}'
            )
            models_results[model_name] = result
        
        # Train TensorFlow models
        for model_name in ['TF_EfficientNet', 'TF_Transformer']:
            result = self.train_tensorflow_model(
                X_train, X_val, X_test, y_train, y_val, y_test,
                num_classes, f'weed_{model_name}'
            )
            models_results[model_name] = result
        
        # Find best model
        best_model_name = max(models_results, key=lambda x: models_results[x]['results']['test_accuracy'])
        best_accuracy = models_results[best_model_name]['results']['test_accuracy']
        
        logger.info(f"\n🏆 Best Weed Model: {best_model_name} (Accuracy: {best_accuracy:.4f})")
        
        self.results['weed'] = models_results
        self.models['weed'] = models_results
        
        return models_results
    
    def save_models(self):
        """Save trained models and results"""
        logger.info("\n" + "=" * 70)
        logger.info("💾 SAVING MODELS AND RESULTS")
        logger.info("=" * 70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save disease models
        if 'disease' in self.models:
            disease_dir = self.config.output_dir / 'disease_detection'
            disease_dir.mkdir(parents=True, exist_ok=True)
            
            for model_name, model_data in self.models['disease'].items():
                model = model_data['model']
                
                if isinstance(model, nn.Module):
                    # PyTorch model
                    save_path = disease_dir / f'disease_{model_name}_{timestamp}.pt'
                    torch.save(model.state_dict(), save_path)
                else:
                    # TensorFlow model
                    save_path = disease_dir / f'disease_{model_name}_{timestamp}.keras'
                    model.save(save_path)
                
                logger.info(f"   ✅ Saved: {save_path.name}")
            
            # Save scaler and encoder
            import joblib
            joblib.dump(self.disease_scaler, disease_dir / f'disease_scaler_{timestamp}.joblib')
            joblib.dump(self.disease_encoder, disease_dir / f'disease_encoder_{timestamp}.joblib')
        
        # Save weed models
        if 'weed' in self.models:
            weed_dir = self.config.output_dir / 'weed_management'
            weed_dir.mkdir(parents=True, exist_ok=True)
            
            for model_name, model_data in self.models['weed'].items():
                model = model_data['model']
                
                if isinstance(model, nn.Module):
                    # PyTorch model
                    save_path = weed_dir / f'weed_{model_name}_{timestamp}.pt'
                    torch.save(model.state_dict(), save_path)
                else:
                    # TensorFlow model
                    save_path = weed_dir / f'weed_{model_name}_{timestamp}.keras'
                    model.save(save_path)
                
                logger.info(f"   ✅ Saved: {save_path.name}")
            
            # Save scaler and encoder
            import joblib
            joblib.dump(self.weed_scaler, weed_dir / f'weed_scaler_{timestamp}.joblib')
            joblib.dump(self.weed_encoder, weed_dir / f'weed_encoder_{timestamp}.joblib')
        
        # Save training results
        results_path = self.config.output_dir / f'training_results_{timestamp}.json'
        
        # Convert results to JSON-serializable format
        json_results = {}
        for category, models in self.results.items():
            json_results[category] = {}
            for model_name, model_data in models.items():
                # Extract only results (not the model object)
                json_results[category][model_name] = model_data['results']
        
        with open(results_path, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)
        
        logger.info(f"   ✅ Results saved: {results_path.name}")
        
        # Generate summary report
        self._generate_summary_report(timestamp)
    
    def _generate_summary_report(self, timestamp: str):
        """Generate a summary report of training results"""
        report_path = self.config.output_dir / f'training_summary_{timestamp}.md'
        
        with open(report_path, 'w') as f:
            f.write("# GPU-Optimized Hybrid AI Training Report\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Device**: {self.device}\n\n")
            
            # GPU info
            if torch.cuda.is_available():
                f.write("## GPU Information\n\n")
                f.write(f"- **GPU**: {torch.cuda.get_device_name(0)}\n")
                f.write(f"- **CUDA Version**: {torch.version.cuda}\n")
                f.write(f"- **Memory**: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB\n\n")
            
            # Disease detection results
            if 'disease' in self.results:
                f.write("## Disease Detection Models\n\n")
                f.write("| Model | Framework | Test Accuracy | Precision | Recall | F1 Score | Training Time (s) |\n")
                f.write("|-------|-----------|---------------|-----------|--------|----------|-------------------|\n")
                
                for model_name, model_data in self.results['disease'].items():
                    results = model_data['results']
                    f.write(f"| {model_name} | {results['framework']} | "
                           f"{results['test_accuracy']:.4f} | "
                           f"{results['precision']:.4f} | "
                           f"{results['recall']:.4f} | "
                           f"{results['f1_score']:.4f} | "
                           f"{results['training_time']:.2f} |\n")
                
                f.write("\n")
            
            # Weed management results
            if 'weed' in self.results:
                f.write("## Weed Management Models\n\n")
                f.write("| Model | Framework | Test Accuracy | Precision | Recall | F1 Score | Training Time (s) |\n")
                f.write("|-------|-----------|---------------|-----------|--------|----------|-------------------|\n")
                
                for model_name, model_data in self.results['weed'].items():
                    results = model_data['results']
                    f.write(f"| {model_name} | {results['framework']} | "
                           f"{results['test_accuracy']:.4f} | "
                           f"{results['precision']:.4f} | "
                           f"{results['recall']:.4f} | "
                           f"{results['f1_score']:.4f} | "
                           f"{results['training_time']:.2f} |\n")
                
                f.write("\n")
            
            # Best models summary
            f.write("## Best Models\n\n")
            
            if 'disease' in self.results:
                best_disease = max(self.results['disease'].items(), 
                                 key=lambda x: x[1]['results']['test_accuracy'])
                f.write(f"- **Best Disease Model**: {best_disease[0]} "
                       f"({best_disease[1]['results']['test_accuracy']*100:.2f}% accuracy)\n")
            
            if 'weed' in self.results:
                best_weed = max(self.results['weed'].items(),
                              key=lambda x: x[1]['results']['test_accuracy'])
                f.write(f"- **Best Weed Model**: {best_weed[0]} "
                       f"({best_weed[1]['results']['test_accuracy']*100:.2f}% accuracy)\n")
        
        logger.info(f"   ✅ Summary report: {report_path.name}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main training pipeline"""
    logger.info("\n" + "=" * 70)
    logger.info("🌾 AGRISENSE GPU-OPTIMIZED HYBRID AI TRAINING 🌾")
    logger.info("=" * 70)
    
    # Check GPU availability
    check_gpu_availability()
    
    # Configure GPU
    configure_tensorflow_gpu()
    configure_pytorch_gpu()
    
    # Initialize trainer
    config = GPUTrainingConfig()
    trainer = GPUHybridAITrainer(config)
    
    try:
        # Train disease detection models
        trainer.train_disease_detection()
        
        # Train weed management models
        trainer.train_weed_management()
        
        # Save all models and results
        trainer.save_models()
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 TRAINING COMPLETE!")
        logger.info("=" * 70)
        
        # Print summary
        if 'disease' in trainer.results:
            best_disease = max(trainer.results['disease'].items(),
                             key=lambda x: x[1]['results']['test_accuracy'])
            logger.info(f"🦠 Best Disease Model: {best_disease[0]} "
                       f"({best_disease[1]['results']['test_accuracy']*100:.2f}% accuracy)")
        
        if 'weed' in trainer.results:
            best_weed = max(trainer.results['weed'].items(),
                          key=lambda x: x[1]['results']['test_accuracy'])
            logger.info(f"🌿 Best Weed Model: {best_weed[0]} "
                       f"({best_weed[1]['results']['test_accuracy']*100:.2f}% accuracy)")
        
        logger.info(f"\n📁 Models saved to: {config.output_dir}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
