#!/usr/bin/env python3
"""
Advanced Deep Learning Pipeline for AgriSense
Push accuracy from 98% to 99%+ using neural networks
"""
# type: ignore
# This file contains TensorFlow/Keras code that may have type issues when TF is not available

import os
import pandas as pd
import numpy as np
import joblib
import warnings
from pathlib import Path
from datetime import datetime
import logging
from typing import Any, Tuple, Dict, List, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ML imports
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Deep Learning imports
TF_AVAILABLE = False
try:
    import tensorflow as tf
    from keras.models import Sequential, Model as KerasModel
    from keras.layers import Dense, Dropout, BatchNormalization, Input, Concatenate, Add
    from keras.optimizers import Adam, RMSprop
    from keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from keras.utils import to_categorical
    from keras.regularizers import l1_l2
    TF_AVAILABLE = True
    logger.info("✅ TensorFlow available for deep learning")
except ImportError as e:
    KerasModel = object  # Fallback type
    Sequential = object
    Dense = object
    Dropout = object
    BatchNormalization = object
    Input = object
    Concatenate = object
    Add = object
    Adam = object
    RMSprop = object
    EarlyStopping = object
    ReduceLROnPlateau = object
    ModelCheckpoint = object
    to_categorical = lambda x: x
    l1_l2 = lambda l1=0.01, l2=0.01: None
    logger.error(f"❌ TensorFlow not available - deep learning disabled: {e}")

from typing import Union, Optional, Tuple, Dict, Any

class AdvancedDeepLearningPipeline:
    """Advanced neural network pipeline for agricultural ML"""
    
    def __init__(self, output_dir: str = "deep_learning_models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.disease_data = None
        self.weed_data = None
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.results = {}
        
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for deep learning pipeline")
            
        # Set TensorFlow configuration for optimal performance
        self._configure_tensorflow()
        
        logger.info(f"🧠 Deep Learning Pipeline initialized: {self.output_dir}")
    
    def _configure_tensorflow(self):
        """Configure TensorFlow for optimal performance"""
        try:
            # Enable memory growth for GPU if available
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"🎮 GPU acceleration enabled: {len(gpus)} GPU(s)")
            else:
                logger.info("💻 Using CPU for deep learning")
            
            # Set mixed precision for better performance
            tf.config.optimizer.set_jit(True)
            
        except Exception as e:
            logger.warning(f"⚠️ TensorFlow configuration warning: {e}")
    
    def load_enhanced_datasets(self) -> bool:
        """Load the enhanced datasets"""
        try:
            logger.info("📥 Loading enhanced datasets for deep learning...")
            
            if os.path.exists('enhanced_disease_dataset.csv'):
                self.disease_data = pd.read_csv('enhanced_disease_dataset.csv')
                logger.info(f"✅ Disease dataset: {self.disease_data.shape}")
            else:
                logger.error("❌ Enhanced disease dataset not found")
                return False
                
            if os.path.exists('enhanced_weed_dataset.csv'):
                self.weed_data = pd.read_csv('enhanced_weed_dataset.csv')
                logger.info(f"✅ Weed dataset: {self.weed_data.shape}")
            else:
                logger.error("❌ Enhanced weed dataset not found")
                return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Error loading datasets: {e}")
            return False
    
    def prepare_data_for_dl(self, data: pd.DataFrame, target_col: str) -> tuple:
        """Prepare data specifically for deep learning"""
        logger.info(f"🔧 Preparing data for deep learning: {target_col}")
        
        # Separate features and target
        X = data.drop([target_col], axis=1)
        y = data[target_col]
        
        # Handle categorical features
        categorical_cols = X.select_dtypes(include=['object']).columns
        encoder_key = f"{target_col}_categorical_encoders"
        
        if encoder_key not in self.encoders:
            self.encoders[encoder_key] = {}
        
        for col in categorical_cols:
            if col not in self.encoders[encoder_key]:
                self.encoders[encoder_key][col] = LabelEncoder()
            X[col] = self.encoders[encoder_key][col].fit_transform(X[col].astype(str))
        
        # Handle target encoding
        target_encoder_key = f"{target_col}_target_encoder"
        if target_encoder_key not in self.encoders:
            self.encoders[target_encoder_key] = LabelEncoder()
        y_encoded = self.encoders[target_encoder_key].fit_transform(y.astype(str))
        
        # Convert to categorical for neural networks
        num_classes = len(np.unique(y_encoded))
        y_categorical = to_categorical(y_encoded)
        
        # Scale features
        scaler_key = f"{target_col}_dl_scaler"
        if scaler_key not in self.scalers:
            self.scalers[scaler_key] = StandardScaler()
        X_scaled = self.scalers[scaler_key].fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_categorical, test_size=0.2, random_state=42, 
            stratify=y_encoded
        )
        
        # Additional validation split for early stopping
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.25, random_state=42
        )
        
        logger.info(f"📊 Data splits - Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
        logger.info(f"🏷️ Classes: {num_classes}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test, num_classes
    
    def create_advanced_neural_network(self, input_dim: int, num_classes: int, model_type: str = "deep") -> Any:
        """Create advanced neural network architectures"""
        logger.info(f"🏗️ Building {model_type} neural network: {input_dim} inputs → {num_classes} classes")
        
        if model_type == "deep":
            return self._create_deep_network(input_dim, num_classes)
        elif model_type == "wide_deep":
            return self._create_wide_deep_network(input_dim, num_classes)
        elif model_type == "residual":
            return self._create_residual_network(input_dim, num_classes)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_deep_network(self, input_dim: int, num_classes: int) -> Any:
        """Create a deep neural network with advanced regularization"""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow not available - cannot create neural network")
            
        model = Sequential([  # type: ignore
            Input(shape=(input_dim,)),  # type: ignore
            
            # First block
            Dense(512, activation='relu'),  # type: ignore
            BatchNormalization(),  # type: ignore
            Dropout(0.3),  # type: ignore
            
            # Second block
            Dense(256, activation='relu', kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4)),  # type: ignore
            BatchNormalization(),  # type: ignore
            Dropout(0.4),  # type: ignore
            
            # Third block
            Dense(128, activation='relu', kernel_regularizer=l1_l2(l1=1e-5, l2=1e-4)),  # type: ignore
            BatchNormalization(),  # type: ignore
            Dropout(0.3),  # type: ignore
            
            # Fourth block
            Dense(64, activation='relu'),  # type: ignore
            BatchNormalization(),  # type: ignore
            Dropout(0.2),  # type: ignore
            
            # Output layer
            Dense(num_classes, activation='softmax')  # type: ignore
        ])
        
        return model
    
    def _create_wide_deep_network(self, input_dim: int, num_classes: int) -> Any:
        """Create a wide & deep network for better feature learning"""
        # Input layer
        inputs = Input(shape=(input_dim,))  # type: ignore
        
        # Wide component (linear)
        wide = Dense(num_classes, activation='linear')(inputs)  # type: ignore
        
        # Deep component
        deep = Dense(256, activation='relu')(inputs)  # type: ignore
        deep = BatchNormalization()(deep)  # type: ignore
        deep = Dropout(0.3)(deep)  # type: ignore
        
        deep = Dense(128, activation='relu')(deep)  # type: ignore
        deep = BatchNormalization()(deep)  # type: ignore
        deep = Dropout(0.3)(deep)  # type: ignore
        
        deep = Dense(64, activation='relu')(deep)  # type: ignore
        deep = Dropout(0.2)(deep)  # type: ignore
        
        # Combine wide and deep
        combined = Concatenate()([wide, deep])  # type: ignore
        output = Dense(num_classes, activation='softmax')(combined)  # type: ignore
        
        model = Model(inputs=inputs, outputs=output)  # type: ignore
        return model
    
    def _create_residual_network(self, input_dim: int, num_classes: int) -> Any:
        """Create a residual network with skip connections"""
        inputs = Input(shape=(input_dim,))  # type: ignore
        
        # First layer
        x = Dense(256, activation='relu')(inputs)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        
        # Residual block 1
        residual = x
        x = Dense(256, activation='relu')(x)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        x = Dropout(0.3)(x)  # type: ignore
        x = Dense(256, activation='relu')(x)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        x = tf.keras.layers.Add()([x, residual])  # type: ignore # Skip connection
        
        # Residual block 2
        x = Dense(128, activation='relu')(x)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        residual2 = x
        x = Dense(128, activation='relu')(x)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        x = Dropout(0.3)(x)  # type: ignore
        x = Dense(128, activation='relu')(x)  # type: ignore
        x = BatchNormalization()(x)  # type: ignore
        x = tf.keras.layers.Add()([x, residual2])  # type: ignore # Skip connection
        
        # Final layers
        x = Dense(64, activation='relu')(x)  # type: ignore
        x = Dropout(0.2)(x)  # type: ignore
        output = Dense(num_classes, activation='softmax')(x)  # type: ignore
        
        model = Model(inputs=inputs, outputs=output)  # type: ignore
        return model
    
    def compile_model(self, model: Any, learning_rate: float = 0.001, optimizer_type: str = "adam") -> Any:
        """Compile model with advanced optimization"""
        if optimizer_type == "adam":
            optimizer = Adam(learning_rate=learning_rate, beta_1=0.9, beta_2=0.999, epsilon=1e-7)  # type: ignore
        elif optimizer_type == "rmsprop":
            optimizer = RMSprop(learning_rate=learning_rate)  # type: ignore
        else:
            optimizer = Adam(learning_rate=learning_rate)  # type: ignore
        
        model.compile(  # type: ignore
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_2_accuracy']
        )
        
        return model
    
    def create_callbacks(self, model_name: str) -> list:
        """Create advanced training callbacks"""
        callbacks = [
            EarlyStopping(  # type: ignore
                monitor='val_accuracy',  # type: ignore
                patience=15,  # type: ignore
                restore_best_weights=True,  # type: ignore
                verbose=1  # type: ignore
            ),
            ReduceLROnPlateau(  # type: ignore
                monitor='val_loss',  # type: ignore
                factor=0.5,  # type: ignore
                patience=8,  # type: ignore
                min_lr=1e-7,  # type: ignore
                verbose=1  # type: ignore
            ),
            ModelCheckpoint(  # type: ignore
                filepath=self.output_dir / f"{model_name}_best.keras",  # type: ignore
                monitor='val_accuracy',  # type: ignore
                save_best_only=True,  # type: ignore
                verbose=1  # type: ignore
            )
        ]
        
        return callbacks
    
    def train_neural_network(self, model: Any, X_train, y_train, X_val, y_val, 
                           model_name: str, epochs: int = 150) -> dict:
        """Train neural network with advanced techniques"""
        logger.info(f"🚀 Training {model_name} neural network...")
        
        callbacks = self.create_callbacks(model_name)
        
        # Train model
        history = model.fit(  # type: ignore
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        return {
            'model': model,
            'history': history,
            'model_name': model_name
        }
    
    def evaluate_model(self, model: Any, X_test, y_test, model_name: str) -> dict:
        """Comprehensive model evaluation"""
        logger.info(f"📊 Evaluating {model_name}...")
        
        # Basic evaluation
        test_loss, test_accuracy, top_2_accuracy = model.evaluate(X_test, y_test, verbose=0)  # type: ignore
        
        # Predictions
        y_pred_proba = model.predict(X_test, verbose=0)  # type: ignore
        y_pred = np.argmax(y_pred_proba, axis=1)
        y_true = np.argmax(y_test, axis=1)
        
        # Classification report
        report = classification_report(y_true, y_pred, output_dict=True)
        
        results = {
            'test_accuracy': test_accuracy,
            'test_loss': test_loss,
            'top_2_accuracy': top_2_accuracy,
            'classification_report': report,
            'model_name': model_name
        }
        
        logger.info(f"✅ {model_name} - Accuracy: {test_accuracy:.4f}, Top-2: {top_2_accuracy:.4f}")
        
        return results
    
    def train_disease_deep_learning_models(self):
        """Train multiple neural networks for disease detection"""
        logger.info("\n🦠 DEEP LEARNING DISEASE DETECTION")
        logger.info("=" * 50)
        
        if self.disease_data is None:
            logger.error("❌ Disease data not loaded")
            return
        
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = self.prepare_data_for_dl(
            self.disease_data, 'disease_label'
        )
        
        input_dim = X_train.shape[1]
        
        # Train multiple architectures
        architectures = ['deep', 'wide_deep', 'residual']
        
        for arch in architectures:
            try:
                logger.info(f"\n🏗️ Training {arch} neural network...")
                
                model = self.create_advanced_neural_network(input_dim, num_classes, arch)
                model = self.compile_model(model)
                
                # Train model
                train_results = self.train_neural_network(
                    model, X_train, y_train, X_val, y_val, f"disease_{arch}"
                )
                
                # Evaluate model
                eval_results = self.evaluate_model(
                    train_results['model'], X_test, y_test, f"disease_{arch}"
                )
                
                # Store results
                self.results[f'disease_{arch}'] = {
                    **train_results,
                    **eval_results
                }
                
            except Exception as e:
                logger.error(f"❌ Error training {arch} for disease: {e}")
        
        # Find best model
        best_model = max(
            [k for k in self.results.keys() if k.startswith('disease_')],
            key=lambda x: self.results[x]['test_accuracy']
        )
        
        logger.info(f"\n🏆 Best Disease Model: {best_model}")
        logger.info(f"   Accuracy: {self.results[best_model]['test_accuracy']:.4f}")
    
    def train_weed_deep_learning_models(self):
        """Train multiple neural networks for weed management"""
        logger.info("\n🌿 DEEP LEARNING WEED MANAGEMENT")
        logger.info("=" * 50)
        
        if self.weed_data is None:
            logger.error("❌ Weed data not loaded")
            return
        
        # Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test, num_classes = self.prepare_data_for_dl(
            self.weed_data, 'dominant_weed_species'
        )
        
        input_dim = X_train.shape[1]
        
        # Train multiple architectures
        architectures = ['deep', 'wide_deep', 'residual']
        
        for arch in architectures:
            try:
                logger.info(f"\n🏗️ Training {arch} neural network...")
                
                model = self.create_advanced_neural_network(input_dim, num_classes, arch)
                model = self.compile_model(model)
                
                # Train model
                train_results = self.train_neural_network(
                    model, X_train, y_train, X_val, y_val, f"weed_{arch}"
                )
                
                # Evaluate model
                eval_results = self.evaluate_model(
                    train_results['model'], X_test, y_test, f"weed_{arch}"
                )
                
                # Store results
                self.results[f'weed_{arch}'] = {
                    **train_results,
                    **eval_results
                }
                
            except Exception as e:
                logger.error(f"❌ Error training {arch} for weed: {e}")
        
        # Find best model
        best_model = max(
            [k for k in self.results.keys() if k.startswith('weed_')],
            key=lambda x: self.results[x]['test_accuracy']
        )
        
        logger.info(f"\n🏆 Best Weed Model: {best_model}")
        logger.info(f"   Accuracy: {self.results[best_model]['test_accuracy']:.4f}")
    
    def save_models(self):
        """Save all trained models and components"""
        logger.info("💾 Saving deep learning models...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for model_name, model_data in self.results.items():
            try:
                # Save Keras model
                model_path = self.output_dir / f"{model_name}_{timestamp}.keras"
                model_data['model'].save(model_path)
                logger.info(f"✅ Saved {model_name}: {model_path}")
                
            except Exception as e:
                logger.error(f"❌ Error saving {model_name}: {e}")
        
        # Save encoders and scalers
        encoders_path = self.output_dir / f"dl_encoders_{timestamp}.joblib"
        scalers_path = self.output_dir / f"dl_scalers_{timestamp}.joblib"
        
        joblib.dump(self.encoders, encoders_path)
        joblib.dump(self.scalers, scalers_path)
        
        logger.info(f"✅ Saved encoders: {encoders_path}")
        logger.info(f"✅ Saved scalers: {scalers_path}")
    
    def generate_deep_learning_report(self) -> str:
        """Generate comprehensive deep learning report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
# Deep Learning Pipeline Results
Generated: {timestamp}

## Architecture Performance Comparison

### Disease Detection Models
"""
        
        disease_models = [k for k in self.results.keys() if k.startswith('disease_')]
        for model_name in disease_models:
            results = self.results[model_name]
            report += f"- **{model_name}**: {results['test_accuracy']:.4f} accuracy, {results['top_2_accuracy']:.4f} top-2\n"
        
        report += "\n### Weed Management Models\n"
        
        weed_models = [k for k in self.results.keys() if k.startswith('weed_')]
        for model_name in weed_models:
            results = self.results[model_name]
            report += f"- **{model_name}**: {results['test_accuracy']:.4f} accuracy, {results['top_2_accuracy']:.4f} top-2\n"
        
        if self.results:
            best_disease = max(disease_models, key=lambda x: self.results[x]['test_accuracy']) if disease_models else None
            best_weed = max(weed_models, key=lambda x: self.results[x]['test_accuracy']) if weed_models else None
            
            report += f"""

## Best Models Summary
- **Best Disease Model**: {best_disease} ({self.results[best_disease]['test_accuracy']:.4f} accuracy)
- **Best Weed Model**: {best_weed} ({self.results[best_weed]['test_accuracy']:.4f} accuracy)

## Technical Details
- **Architectures**: Deep, Wide & Deep, Residual Networks
- **Regularization**: Dropout, BatchNorm, L1/L2, Early Stopping
- **Optimization**: Adam with learning rate scheduling
- **Validation**: Train/Val/Test splits with early stopping

## Achievement Summary
- 🎯 Target: 99%+ accuracy through deep learning
- 🧠 Advanced neural network architectures
- 📊 Multiple model comparison
- 🔬 Comprehensive evaluation metrics
"""
        
        return report
    
    def run_deep_learning_pipeline(self):
        """Run the complete deep learning pipeline"""
        logger.info("🧠 STARTING ADVANCED DEEP LEARNING PIPELINE")
        logger.info("=" * 60)
        
        if not self.load_enhanced_datasets():
            logger.error("Failed to load datasets")
            return False
        
        # Train models
        self.train_disease_deep_learning_models()
        self.train_weed_deep_learning_models()
        
        # Save models
        self.save_models()
        
        # Generate report
        report = self.generate_deep_learning_report()
        report_path = self.output_dir / 'deep_learning_report.md'
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ DEEP LEARNING PIPELINE COMPLETE")
        logger.info("="*60)
        logger.info(f"🧠 Neural networks trained and saved")
        logger.info(f"📋 Report generated: {report_path}")
        
        return True


def main():
    """Run the advanced deep learning pipeline"""
    try:
        pipeline = AdvancedDeepLearningPipeline()
        pipeline.run_deep_learning_pipeline()
    except ImportError as e:
        print(f"❌ Deep learning requirements not met: {e}")
        print("💡 Install TensorFlow: pip install tensorflow")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")


if __name__ == "__main__":
    main()