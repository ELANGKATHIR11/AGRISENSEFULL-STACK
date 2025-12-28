#!/usr/bin/env python3
"""
Advanced Deep Learning Pipeline for AgriSense
Implementing neural networks to push accuracy from 98%+ toward 100%
"""

import os
import sys
import logging
import warnings
import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Machine Learning imports
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

# Deep Learning imports with proper fallback
TF_AVAILABLE = False
try:
    import tensorflow as tf
    # Disable GPU warnings
    tf.get_logger().setLevel('ERROR')
    
    import keras
    from keras import layers, models, optimizers, callbacks, regularizers
    TF_AVAILABLE = True
    logger.info("✅ TensorFlow/Keras available for deep learning")
except ImportError as e:
    logger.error(f"❌ TensorFlow not available - deep learning disabled: {e}")

class AdvancedDeepLearningPipeline:
    """Advanced neural network pipeline for optimal accuracy"""
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.models = {}
        self.results = {}
        
        # Set random seeds
        np.random.seed(random_state)
        if TF_AVAILABLE:
            tf.random.set_seed(random_state)
    
    def load_enhanced_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load the enhanced datasets created by ensemble training"""
        logger.info("📊 Loading enhanced datasets...")
        
        disease_path = Path("enhanced_disease_dataset.csv")
        weed_path = Path("enhanced_weed_dataset.csv")
        
        if not disease_path.exists() or not weed_path.exists():
            logger.error("❌ Enhanced datasets not found. Run ensemble training first.")
            sys.exit(1)
        
        disease_df = pd.read_csv(disease_path)
        weed_df = pd.read_csv(weed_path)
        
        logger.info(f"🦠 Disease dataset: {len(disease_df)} samples, {len(disease_df.columns)-1} features")
        logger.info(f"🌿 Weed dataset: {len(weed_df)} samples, {len(weed_df.columns)-1} features")
        
        return disease_df, weed_df
    
    def prepare_neural_data(self, df: pd.DataFrame, target_column: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        """Prepare data specifically for neural network training"""
        logger.info(f"🎯 Preparing neural network data for {target_column}...")
        
        # Separate features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        num_classes = len(np.unique(y_encoded))
        
        # Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=self.random_state, stratify=y_encoded
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=self.random_state, stratify=y_temp
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"📈 Train: {X_train_scaled.shape[0]}, Val: {X_val_scaled.shape[0]}, Test: {X_test_scaled.shape[0]}")
        logger.info(f"🏷️ Classes: {num_classes}")
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, num_classes
    
    def create_deep_network(self, input_dim: int, num_classes: int):
        """Create deep neural network architecture"""
        if not TF_AVAILABLE:
            logger.error("❌ TensorFlow not available")
            return None
        
        logger.info(f"🏗️ Building deep network: {input_dim} → {num_classes}")
        
        model = models.Sequential([
            layers.Input(shape=(input_dim,)),
            
            # First block
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Second block
            layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l1_l2(l1=1e-5, l2=1e-4)),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            
            # Third block
            layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l1_l2(l1=1e-5, l2=1e-4)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Fourth block
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Output layer
            layers.Dense(num_classes, activation='softmax' if num_classes > 2 else 'sigmoid')
        ])
        
        return model
    
    def create_wide_deep_network(self, input_dim: int, num_classes: int):
        """Create wide & deep network architecture"""
        if not TF_AVAILABLE:
            logger.error("❌ TensorFlow not available")
            return None
        
        logger.info(f"🏗️ Building wide & deep network: {input_dim} → {num_classes}")
        
        # Input layer
        inputs = layers.Input(shape=(input_dim,))
        
        # Wide component (linear)
        wide = layers.Dense(num_classes, activation='linear')(inputs)
        
        # Deep component
        deep = layers.Dense(256, activation='relu')(inputs)
        deep = layers.BatchNormalization()(deep)
        deep = layers.Dropout(0.3)(deep)
        
        deep = layers.Dense(128, activation='relu')(deep)
        deep = layers.BatchNormalization()(deep)
        deep = layers.Dropout(0.3)(deep)
        
        deep = layers.Dense(64, activation='relu')(deep)
        deep = layers.BatchNormalization()(deep)
        deep = layers.Dropout(0.2)(deep)
        
        # Combine wide and deep
        combined = layers.Concatenate()([wide, deep])
        output = layers.Dense(num_classes, activation='softmax' if num_classes > 2 else 'sigmoid')(combined)
        
        model = models.Model(inputs=inputs, outputs=output)
        return model
    
    def create_residual_network(self, input_dim: int, num_classes: int):
        """Create residual network with skip connections"""
        if not TF_AVAILABLE:
            logger.error("❌ TensorFlow not available")
            return None
        
        logger.info(f"🏗️ Building residual network: {input_dim} → {num_classes}")
        
        inputs = layers.Input(shape=(input_dim,))
        
        # First block
        x = layers.Dense(256, activation='relu')(inputs)
        x = layers.BatchNormalization()(x)
        
        # Residual block 1
        residual = layers.Dense(256)(x)
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(256)(x)
        x = layers.Add()([x, residual])  # Skip connection
        x = layers.Activation('relu')(x)
        
        # Residual block 2
        residual2 = layers.Dense(128)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128)(x)
        x = layers.Add()([x, residual2])  # Skip connection
        x = layers.Activation('relu')(x)
        
        # Output
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.2)(x)
        output = layers.Dense(num_classes, activation='softmax' if num_classes > 2 else 'sigmoid')(x)
        
        model = models.Model(inputs=inputs, outputs=output)
        return model
    
    def compile_model(self, model, learning_rate: float = 0.001, optimizer_type: str = "adam"):
        """Compile model with optimized settings"""
        if not TF_AVAILABLE or model is None:
            return None
        
        # Choose optimizer
        if optimizer_type == "adam":
            optimizer = optimizers.Adam(learning_rate=learning_rate, beta_1=0.9, beta_2=0.999)
        elif optimizer_type == "rmsprop":
            optimizer = optimizers.RMSprop(learning_rate=learning_rate)
        else:
            optimizer = optimizers.Adam(learning_rate=learning_rate)
        
        # Compile model
        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model
    
    def get_callbacks(self, model_name: str):
        """Get training callbacks"""
        if not TF_AVAILABLE:
            return []
        
        return [
            callbacks.EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=8,
                min_lr=1e-7,
                verbose=1
            ),
            callbacks.ModelCheckpoint(
                f'best_{model_name}_model.h5',
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            )
        ]
    
    def train_neural_network(self, model, X_train, y_train, X_val, y_val, 
                           model_name: str, epochs: int = 200, batch_size: int = 32):
        """Train neural network with advanced techniques"""
        if not TF_AVAILABLE or model is None:
            logger.error("❌ Cannot train - TensorFlow not available")
            return None
        
        logger.info(f"🚀 Training {model_name} neural network...")
        
        # Get callbacks
        model_callbacks = self.get_callbacks(model_name)
        
        # Train model
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=model_callbacks,
            verbose=1
        )
        
        return model, history
    
    def evaluate_neural_model(self, model, X_test, y_test, model_name: str) -> Dict[str, float]:
        """Evaluate neural network performance"""
        if not TF_AVAILABLE or model is None:
            return {"accuracy": 0.0}
        
        logger.info(f"📊 Evaluating {model_name}...")
        
        # Predictions
        y_pred_proba = model.predict(X_test, verbose=0)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')
        
        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
        logger.info(f"✅ {model_name} Results:")
        logger.info(f"   🎯 Accuracy: {accuracy:.4f}")
        logger.info(f"   🎯 Precision: {precision:.4f}")
        logger.info(f"   🎯 Recall: {recall:.4f}")
        logger.info(f"   🎯 F1-Score: {f1:.4f}")
        
        return results
    
    def run_automl_optimization(self, X_train, y_train, X_val, y_val, dataset_name: str):
        """Run AutoML optimization for hyperparameters"""
        logger.info(f"🔍 Running AutoML optimization for {dataset_name}...")
        
        # Combine train and validation for hyperparameter search
        X_combined = np.vstack([X_train, X_val])
        y_combined = np.hstack([y_train, y_val])
        
        # Traditional ML models for comparison
        models_to_test = {
            'rf': RandomForestClassifier(random_state=self.random_state),
            'svm': SVC(random_state=self.random_state, probability=True),
            'lr': LogisticRegression(random_state=self.random_state, max_iter=1000)
        }
        
        param_grids = {
            'rf': {
                'n_estimators': [200, 300, 500],
                'max_depth': [15, 20, None],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            },
            'svm': {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.001, 0.01],
                'kernel': ['rbf', 'poly']
            },
            'lr': {
                'C': [0.01, 0.1, 1, 10, 100],
                'solver': ['liblinear', 'lbfgs'],
                'penalty': ['l1', 'l2']
            }
        }
        
        best_models = {}
        for name, model in models_to_test.items():
            logger.info(f"🔧 Optimizing {name}...")
            
            grid_search = GridSearchCV(
                model, param_grids[name],
                cv=5, scoring='accuracy',
                n_jobs=-1, verbose=0
            )
            
            grid_search.fit(X_combined, y_combined)
            best_models[name] = grid_search.best_estimator_
            
            logger.info(f"   ✅ Best {name} score: {grid_search.best_score_:.4f}")
        
        return best_models
    
    def create_ensemble_with_neural_networks(self, traditional_models: dict, neural_models: dict, 
                                           X_train, y_train, dataset_name: str):
        """Create ensemble combining traditional ML and neural networks"""
        logger.info(f"🤝 Creating hybrid ensemble for {dataset_name}...")
        
        # Combine all models
        estimators = []
        for name, model in traditional_models.items():
            estimators.append((f'traditional_{name}', model))
        
        # Add neural network predictions (if available)
        if TF_AVAILABLE and neural_models:
            for name, model in neural_models.items():
                # Create a wrapper for neural network
                class KerasWrapper:
                    def __init__(self, model):
                        self.model = model
                    
                    def predict(self, X):
                        proba = self.model.predict(X, verbose=0)
                        return np.argmax(proba, axis=1)
                    
                    def predict_proba(self, X):
                        return self.model.predict(X, verbose=0)
                
                estimators.append((f'neural_{name}', KerasWrapper(model)))
        
        # Create voting classifier
        ensemble = VotingClassifier(estimators=estimators, voting='soft')
        ensemble.fit(X_train, y_train)
        
        return ensemble
    
    def run_complete_pipeline(self):
        """Run the complete deep learning pipeline"""
        logger.info("🚀 Starting Advanced Deep Learning Pipeline")
        logger.info("=" * 60)
        
        # Load enhanced datasets
        disease_df, weed_df = self.load_enhanced_datasets()
        
        datasets = [
            (disease_df, 'disease_label', 'disease'),
            (weed_df, 'dominant_weed_species', 'weed')
        ]
        
        all_results = {}
        
        for df, target_col, dataset_name in datasets:
            logger.info(f"\n🎯 Processing {dataset_name.upper()} dataset")
            logger.info("-" * 40)
            
            # Prepare data
            X_train, X_val, X_test, y_train, y_val, y_test, num_classes = self.prepare_neural_data(df, target_col)
            
            # Neural network architectures to test
            neural_models = {}
            
            if TF_AVAILABLE:
                architectures = [
                    ('deep', self.create_deep_network),
                    ('wide_deep', self.create_wide_deep_network),
                    ('residual', self.create_residual_network)
                ]
                
                for arch_name, create_func in architectures:
                    logger.info(f"\n🏗️ Training {arch_name} architecture...")
                    
                    # Create and compile model
                    model = create_func(X_train.shape[1], num_classes)
                    if model is not None:
                        model = self.compile_model(model, learning_rate=0.001)
                        
                        # Train model
                        result = self.train_neural_network(
                            model, X_train, y_train, X_val, y_val, 
                            f"{dataset_name}_{arch_name}", epochs=100
                        )
                        
                        if result is not None:
                            trained_model, history = result
                        
                        if trained_model is not None:
                            # Evaluate model
                            results = self.evaluate_neural_model(
                                trained_model, X_test, y_test, f"{dataset_name}_{arch_name}"
                            )
                            neural_models[arch_name] = trained_model
                            self.results[f"{dataset_name}_{arch_name}"] = results
            
            # Run AutoML optimization
            traditional_models = self.run_automl_optimization(X_train, y_train, X_val, y_val, dataset_name)
            
            # Evaluate traditional models
            for name, model in traditional_models.items():
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                logger.info(f"📊 Traditional {name} accuracy: {accuracy:.4f}")
                self.results[f"{dataset_name}_traditional_{name}"] = {"accuracy": accuracy}
            
            # Create hybrid ensemble
            ensemble = self.create_ensemble_with_neural_networks(
                traditional_models, neural_models, X_train, y_train, dataset_name
            )
            
            # Evaluate ensemble
            y_pred_ensemble = ensemble.predict(X_test)
            ensemble_accuracy = accuracy_score(y_test, y_pred_ensemble)
            logger.info(f"🎉 {dataset_name.upper()} Hybrid Ensemble Accuracy: {ensemble_accuracy:.4f}")
            self.results[f"{dataset_name}_hybrid_ensemble"] = {"accuracy": ensemble_accuracy}
            
            # Save best models
            self.models[f"{dataset_name}_ensemble"] = ensemble
            all_results[dataset_name] = ensemble_accuracy
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 DEEP LEARNING PIPELINE COMPLETE!")
        logger.info("=" * 60)
        
        for dataset_name, accuracy in all_results.items():
            logger.info(f"🏆 {dataset_name.upper()} Final Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        # Save results
        self.save_results()
        
        return all_results
    
    def save_results(self):
        """Save all results and models"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results summary
        results_file = f"deep_learning_results_{timestamp}.json"
        import json
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Save models
        models_file = f"deep_learning_models_{timestamp}.pkl"
        with open(models_file, 'wb') as f:
            pickle.dump(self.models, f)
        
        logger.info(f"💾 Results saved to: {results_file}")
        logger.info(f"💾 Models saved to: {models_file}")

def main():
    """Main execution function"""
    logger.info("🌟 AgriSense Advanced Deep Learning Pipeline")
    logger.info("🎯 Goal: Push accuracy from 98%+ toward 100%")
    
    # Initialize pipeline
    pipeline = AdvancedDeepLearningPipeline(random_state=42)
    
    # Run complete pipeline
    results = pipeline.run_complete_pipeline()
    
    logger.info("\n🎊 Pipeline execution completed!")
    return results

if __name__ == "__main__":
    main()