#!/usr/bin/env python3
"""
Enhanced ML Training Pipeline for AgriSense Plant Health Models
Trains disease detection and weed management models using real datasets
"""

import pandas as pd
import numpy as np
import joblib
import warnings
from datetime import datetime
from pathlib import Path

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.neural_network import MLPClassifier

# TensorFlow for advanced models
try:
    import tensorflow as tf
    from keras.models import Sequential  # type: ignore
    from keras.layers import Dense, Dropout  # type: ignore  
    from keras.optimizers import Adam  # type: ignore
    TF_AVAILABLE = True
except ImportError:
    try:
        # Fallback to older tensorflow.keras imports
        import tensorflow as tf  # type: ignore
        from tensorflow.keras.models import Sequential  # type: ignore
        from tensorflow.keras.layers import Dense, Dropout  # type: ignore
        from tensorflow.keras.optimizers import Adam  # type: ignore
        TF_AVAILABLE = True
    except ImportError:
        TF_AVAILABLE = False
        print("⚠️ TensorFlow not available. Using scikit-learn models only.")

warnings.filterwarnings('ignore')

class PlantHealthMLTrainer:
    """Enhanced ML trainer for plant health models"""
    
    def __init__(self, output_dir="agrisense_app/backend/models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"🏗️ PlantHealthMLTrainer initialized - Models will be saved to: {self.output_dir}")
    
    def load_and_preprocess_data(self, dataset_type):
        """Load and preprocess disease or weed dataset"""
        if dataset_type == 'disease':
            df = pd.read_csv('crop_disease_dataset.csv')
        elif dataset_type == 'weed':
            df = pd.read_csv('weed_management_dataset.csv')
        else:
            raise ValueError("dataset_type must be 'disease' or 'weed'")
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
        
        print(f"✅ Loaded {dataset_type} dataset: {len(df)} samples")
        return df
    
    def prepare_disease_features(self, df):
        """Prepare features for disease detection"""
        # Core features for disease detection
        feature_columns = ['temperature_c', 'humidity_pct', 'leaf_wetness_hours', 
                          'ndvi', 'lesion_count_per_leaf', 'severity_percent']
        
        # Encode categorical variables
        encoders = {}
        
        # Crop type encoder
        crop_encoder = LabelEncoder()
        df['crop_type_encoded'] = crop_encoder.fit_transform(df['crop_type'])
        feature_columns.append('crop_type_encoded')
        encoders['crop_type'] = crop_encoder
        
        # Growth stage encoder
        growth_encoder = LabelEncoder()
        df['growth_stage_encoded'] = growth_encoder.fit_transform(df['growth_stage'])
        feature_columns.append('growth_stage_encoded')
        encoders['growth_stage'] = growth_encoder
        
        # Prepare feature matrix
        X = df[feature_columns].values
        
        # Encode target variable
        target_encoder = LabelEncoder()
        y = target_encoder.fit_transform(df['disease_label'])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, y, {
            'feature_scaler': scaler,
            'target_encoder': target_encoder,
            'categorical_encoders': encoders,
            'feature_names': feature_columns,
            'target_classes': target_encoder.classes_
        }
    
    def prepare_weed_features(self, df):
        """Prepare features for weed management"""
        # Core features for weed detection
        feature_columns = ['soil_moisture_pct', 'ndvi', 'canopy_cover_pct', 'weed_density_plants_per_m2']
        
        # Encode categorical variables
        encoders = {}
        
        # Crop type encoder
        crop_encoder = LabelEncoder()
        df['crop_type_encoded'] = crop_encoder.fit_transform(df['crop_type'])
        feature_columns.append('crop_type_encoded')
        encoders['crop_type'] = crop_encoder
        
        # Growth stage encoder
        growth_encoder = LabelEncoder()
        df['growth_stage_encoded'] = growth_encoder.fit_transform(df['growth_stage'])
        feature_columns.append('growth_stage_encoded')
        encoders['growth_stage'] = growth_encoder
        
        # Prepare feature matrix
        X = df[feature_columns].values
        
        # Encode target variable
        target_encoder = LabelEncoder()
        y = target_encoder.fit_transform(df['dominant_weed_species'])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, y, {
            'feature_scaler': scaler,
            'target_encoder': target_encoder,
            'categorical_encoders': encoders,
            'feature_names': feature_columns,
            'target_classes': target_encoder.classes_
        }
    
    def train_models(self, X_train, X_test, y_train, y_test, dataset_type):
        """Train multiple models and return best one"""
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42),
            'Neural Network': MLPClassifier(hidden_layer_sizes=(128, 64), random_state=42, max_iter=1000)
        }
        
        results = {}
        print(f"\n🔬 Training {dataset_type} models...")
        
        for name, model in models.items():
            print(f"  🚀 Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            results[name] = {
                'model': model,
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            print(f"    ✅ {name}: Test Acc={test_score:.3f}, CV={cv_scores.mean():.3f}±{cv_scores.std():.3f}")
        
        return results
    
    def save_model(self, best_model, metadata, dataset_type):
        """Save the best trained model"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model with metadata
        model_path = self.output_dir / f"{dataset_type}_model_{timestamp}.joblib"
        joblib.dump({
            'model': best_model['model'],
            'metadata': metadata,
            'model_type': best_model['name'],
            'accuracy': best_model['test_accuracy'],
            'timestamp': timestamp
        }, model_path)
        
        print(f"✅ Saved {dataset_type} model: {model_path}")
        
        # Create symlink for latest model
        latest_path = self.output_dir / f"{dataset_type}_model_latest.joblib"
        if latest_path.exists():
            latest_path.unlink()
        
        try:
            latest_path.symlink_to(model_path.name)
        except OSError:
            # Fallback for Windows if symlinks not supported
            import shutil
            shutil.copy2(model_path, latest_path)
        
        return model_path
    
    def train_disease_models(self):
        """Train disease detection models"""
        print(f"\n{'='*60}")
        print(f"🔬 TRAINING DISEASE DETECTION MODELS")
        print(f"{'='*60}")
        
        # Load and prepare data
        df = self.load_and_preprocess_data('disease')
        X, y, metadata = self.prepare_disease_features(df)
        
        print(f"📊 Disease dataset info:")
        print(f"  • Features: {X.shape[1]}")
        print(f"  • Samples: {X.shape[0]}")
        print(f"  • Classes: {len(metadata['target_classes'])}")
        print(f"  • Disease types: {list(metadata['target_classes'])}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models
        results = self.train_models(X_train, X_test, y_train, y_test, 'disease')
        
        # Find best model
        best_name = max(results.keys(), key=lambda k: results[k]['test_accuracy'])
        best_model = results[best_name]
        best_model['name'] = best_name
        
        # Save best model
        model_path = self.save_model(best_model, metadata, 'disease')
        
        print(f"\n🏆 Best disease model: {best_name} (Accuracy: {best_model['test_accuracy']:.3f})")
        return best_model, metadata
    
    def train_weed_models(self):
        """Train weed management models"""
        print(f"\n{'='*60}")
        print(f"🌿 TRAINING WEED MANAGEMENT MODELS")
        print(f"{'='*60}")
        
        # Load and prepare data
        df = self.load_and_preprocess_data('weed')
        X, y, metadata = self.prepare_weed_features(df)
        
        print(f"📊 Weed dataset info:")
        print(f"  • Features: {X.shape[1]}")
        print(f"  • Samples: {X.shape[0]}")
        print(f"  • Classes: {len(metadata['target_classes'])}")
        print(f"  • Weed species: {list(metadata['target_classes'])}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train models
        results = self.train_models(X_train, X_test, y_train, y_test, 'weed')
        
        # Find best model
        best_name = max(results.keys(), key=lambda k: results[k]['test_accuracy'])
        best_model = results[best_name]
        best_model['name'] = best_name
        
        # Save best model
        model_path = self.save_model(best_model, metadata, 'weed')
        
        print(f"\n🏆 Best weed model: {best_name} (Accuracy: {best_model['test_accuracy']:.3f})")
        return best_model, metadata
    
    def train_all(self):
        """Train all plant health models"""
        print("🌱 AGRISENSE ENHANCED ML TRAINING PIPELINE")
        print("="*70)
        
        # Train disease models
        disease_model, disease_metadata = self.train_disease_models()
        
        # Train weed models
        weed_model, weed_metadata = self.train_weed_models()
        
        print(f"\n🎉 TRAINING COMPLETE!")
        print(f"="*70)
        print(f"✅ Disease Detection: {disease_model['name']} (Accuracy: {disease_model['test_accuracy']:.3f})")
        print(f"✅ Weed Management: {weed_model['name']} (Accuracy: {weed_model['test_accuracy']:.3f})")
        print(f"📁 Models saved to: {self.output_dir}")
        
        return {
            'disease': (disease_model, disease_metadata),
            'weed': (weed_model, weed_metadata)
        }

def main():
    """Main training function"""
    trainer = PlantHealthMLTrainer()
    results = trainer.train_all()
    
    print(f"\n🔧 NEXT STEPS:")
    print(f"1. ✅ Models trained and saved successfully")
    print(f"2. 🔄 Update backend engines to use new models")
    print(f"3. 🧪 Test with API endpoints")
    print(f"4. 🎯 Verify frontend integration")
    
    return results

if __name__ == '__main__':
    results = main()