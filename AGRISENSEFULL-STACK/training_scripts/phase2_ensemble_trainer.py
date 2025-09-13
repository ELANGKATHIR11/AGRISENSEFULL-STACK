#!/usr/bin/env python3
"""
Advanced Ensemble ML Training System for 100% Accuracy Goal
Phase 2: Train Random Forest, XGBoost, and Gradient Boosting models
Target: 70-75% accuracy improvement from enhanced datasets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import joblib
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import XGBoost, install if needed
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ XGBoost not available - will install and use other ensemble methods")

class AdvancedEnsembleTrainer:
    """Advanced ensemble training system for agricultural ML models"""
    
    def __init__(self):
        self.disease_data: Optional[pd.DataFrame] = None
        self.weed_data: Optional[pd.DataFrame] = None
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        
    def load_enhanced_datasets(self) -> bool:
        """Load the enhanced datasets from yesterday's work"""
        try:
            print("📥 Loading Enhanced Datasets")
            print("=" * 40)
            
            self.disease_data = pd.read_csv('enhanced_disease_dataset.csv')
            self.weed_data = pd.read_csv('enhanced_weed_dataset.csv')
            
            print(f"✅ Disease dataset: {self.disease_data.shape}")
            print(f"✅ Weed dataset: {self.weed_data.shape}")
            
            # Load feature encoders if available
            try:
                self.encoders = joblib.load('feature_encoders.joblib')
                print("✅ Feature encoders loaded")
            except:
                print("⚠️ Feature encoders not found - will create new ones")
                
            return True
        except Exception as e:
            print(f"❌ Error loading datasets: {e}")
            return False
    
    def prepare_data(self, data: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training with proper encoding and scaling"""
        print(f"🔧 Preparing {target_col} data...")
        
        # Separate features and target
        X = data.drop([target_col], axis=1)
        y = data[target_col]
        
        # Handle categorical features
        X_processed = X.copy()
        categorical_cols = X.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            if col in X_processed.columns:
                encoder_key = f"{target_col}_{col}"
                if encoder_key not in self.encoders:
                    self.encoders[encoder_key] = LabelEncoder()
                    X_processed[col] = self.encoders[encoder_key].fit_transform(X[col].astype(str))
                else:
                    try:
                        X_processed[col] = self.encoders[encoder_key].transform(X[col].astype(str))
                    except:
                        # Handle unseen categories
                        self.encoders[encoder_key] = LabelEncoder()
                        X_processed[col] = self.encoders[encoder_key].fit_transform(X[col].astype(str))
        
        # Ensure all features are numeric
        X_processed = X_processed.select_dtypes(include=[np.number])
        
        # Handle any remaining NaN values
        X_processed = X_processed.fillna(X_processed.mean())
        
        # Scale features
        scaler_key = f"{target_col}_scaler"
        if scaler_key not in self.scalers:
            self.scalers[scaler_key] = StandardScaler()
            X_scaled = self.scalers[scaler_key].fit_transform(X_processed)
        else:
            X_scaled = self.scalers[scaler_key].transform(X_processed)
        
        # Encode target variable
        target_encoder_key = f"{target_col}_target"
        if target_encoder_key not in self.encoders:
            self.encoders[target_encoder_key] = LabelEncoder()
            y_encoded = self.encoders[target_encoder_key].fit_transform(y.astype(str))
        else:
            y_encoded = self.encoders[target_encoder_key].transform(y.astype(str))
        
        print(f"   Features shape: {X_scaled.shape}")
        print(f"   Target classes: {len(np.unique(y_encoded))}")
        
        return X_scaled, y_encoded
    
    def train_random_forest(self, X: np.ndarray, y: np.ndarray, model_name: str) -> Dict:
        """Train optimized Random Forest model"""
        print(f"🌳 Training Random Forest for {model_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Optimized Random Forest parameters
        rf_params = {
            'n_estimators': 200,
            'max_depth': 15,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'bootstrap': True,
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Train model
        rf_model = RandomForestClassifier(**rf_params)
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        train_score = rf_model.score(X_train, y_train)
        test_score = rf_model.score(X_test, y_test)
        y_pred = rf_model.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring='accuracy')
        
        results = {
            'model': rf_model,
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'feature_importance': rf_model.feature_importances_
        }
        
        print(f"   🎯 Test Accuracy: {test_score:.3f}")
        print(f"   📊 CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return results
    
    def train_gradient_boosting(self, X: np.ndarray, y: np.ndarray, model_name: str) -> Dict:
        """Train optimized Gradient Boosting model"""
        print(f"⚡ Training Gradient Boosting for {model_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Optimized Gradient Boosting parameters
        gb_params = {
            'n_estimators': 150,
            'learning_rate': 0.1,
            'max_depth': 8,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'subsample': 0.8,
            'random_state': 42
        }
        
        # Train model
        gb_model = GradientBoostingClassifier(**gb_params)
        gb_model.fit(X_train, y_train)
        
        # Evaluate
        train_score = gb_model.score(X_train, y_train)
        test_score = gb_model.score(X_test, y_test)
        y_pred = gb_model.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(gb_model, X_train, y_train, cv=5, scoring='accuracy')
        
        results = {
            'model': gb_model,
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'feature_importance': gb_model.feature_importances_
        }
        
        print(f"   🎯 Test Accuracy: {test_score:.3f}")
        print(f"   📊 CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return results
    
    def train_xgboost(self, X: np.ndarray, y: np.ndarray, model_name: str) -> Optional[Dict]:
        """Train optimized XGBoost model if available"""
        if not XGBOOST_AVAILABLE:
            print(f"⚠️ XGBoost not available for {model_name}")
            return None
            
        print(f"🚀 Training XGBoost for {model_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Optimized XGBoost parameters
        xgb_params = {
            'n_estimators': 200,
            'learning_rate': 0.1,
            'max_depth': 8,
            'min_child_weight': 3,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1,
            'objective': 'multi:softprob' if len(np.unique(y)) > 2 else 'binary:logistic'
        }
        
        # Train model
        xgb_model = xgb.XGBClassifier(**xgb_params)
        xgb_model.fit(X_train, y_train)
        
        # Evaluate
        train_score = xgb_model.score(X_train, y_train)
        test_score = xgb_model.score(X_test, y_test)
        y_pred = xgb_model.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=5, scoring='accuracy')
        
        results = {
            'model': xgb_model,
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'feature_importance': xgb_model.feature_importances_
        }
        
        print(f"   🎯 Test Accuracy: {test_score:.3f}")
        print(f"   📊 CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return results
    
    def create_ensemble_voting_classifier(self, X: np.ndarray, y: np.ndarray, model_name: str) -> Dict:
        """Create ensemble voting classifier combining all models"""
        print(f"🗳️ Creating Ensemble Voting Classifier for {model_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create individual models
        rf_model = RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
        )
        gb_model = GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.1, max_depth=8, random_state=42
        )
        
        estimators = [
            ('random_forest', rf_model),
            ('gradient_boosting', gb_model)
        ]
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            xgb_model = xgb.XGBClassifier(
                n_estimators=200, learning_rate=0.1, max_depth=8, random_state=42, n_jobs=-1
            )
            estimators.append(('xgboost', xgb_model))
        
        # Create voting classifier
        ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft',  # Use probability averaging
            n_jobs=-1
        )
        
        # Train ensemble
        ensemble.fit(X_train, y_train)
        
        # Evaluate
        train_score = ensemble.score(X_train, y_train)
        test_score = ensemble.score(X_test, y_test)
        y_pred = ensemble.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(ensemble, X_train, y_train, cv=5, scoring='accuracy')
        
        results = {
            'model': ensemble,
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'ensemble_models': len(estimators)
        }
        
        print(f"   🎯 Ensemble Test Accuracy: {test_score:.3f}")
        print(f"   📊 Ensemble CV Score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        print(f"   🤝 Combined {len(estimators)} models")
        
        return results
    
    def train_disease_models(self):
        """Train all models for disease detection"""
        print("\n🦠 TRAINING DISEASE DETECTION MODELS")
        print("=" * 50)
        
        if self.disease_data is None:
            print("❌ Disease data not loaded")
            return
        
        X, y = self.prepare_data(self.disease_data, 'disease_label')
        
        # Train individual models
        self.results['disease_rf'] = self.train_random_forest(X, y, 'Disease')
        self.results['disease_gb'] = self.train_gradient_boosting(X, y, 'Disease')
        
        if XGBOOST_AVAILABLE:
            self.results['disease_xgb'] = self.train_xgboost(X, y, 'Disease')
        
        # Train ensemble
        self.results['disease_ensemble'] = self.create_ensemble_voting_classifier(X, y, 'Disease')
        
        # Store best individual model
        best_model_key = max(
            [k for k in self.results.keys() if k.startswith('disease_') and k != 'disease_ensemble'],
            key=lambda k: self.results[k]['test_accuracy']
        )
        self.models['disease_best_individual'] = self.results[best_model_key]['model']
        self.models['disease_ensemble'] = self.results['disease_ensemble']['model']
        
        print(f"\n🏆 Best Disease Model: {best_model_key}")
        print(f"   Individual Best: {self.results[best_model_key]['test_accuracy']:.3f}")
        print(f"   Ensemble Score: {self.results['disease_ensemble']['test_accuracy']:.3f}")
    
    def train_weed_models(self):
        """Train all models for weed management"""
        print("\n🌿 TRAINING WEED MANAGEMENT MODELS")
        print("=" * 50)
        
        if self.weed_data is None:
            print("❌ Weed data not loaded")
            return
        
        X, y = self.prepare_data(self.weed_data, 'dominant_weed_species')
        
        # Train individual models
        self.results['weed_rf'] = self.train_random_forest(X, y, 'Weed')
        self.results['weed_gb'] = self.train_gradient_boosting(X, y, 'Weed')
        
        if XGBOOST_AVAILABLE:
            self.results['weed_xgb'] = self.train_xgboost(X, y, 'Weed')
        
        # Train ensemble
        self.results['weed_ensemble'] = self.create_ensemble_voting_classifier(X, y, 'Weed')
        
        # Store best individual model
        best_model_key = max(
            [k for k in self.results.keys() if k.startswith('weed_') and k != 'weed_ensemble'],
            key=lambda k: self.results[k]['test_accuracy']
        )
        self.models['weed_best_individual'] = self.results[best_model_key]['model']
        self.models['weed_ensemble'] = self.results['weed_ensemble']['model']
        
        print(f"\n🏆 Best Weed Model: {best_model_key}")
        print(f"   Individual Best: {self.results[best_model_key]['test_accuracy']:.3f}")
        print(f"   Ensemble Score: {self.results['weed_ensemble']['test_accuracy']:.3f}")
    
    def save_models_and_results(self):
        """Save trained models and results"""
        print("\n💾 SAVING MODELS AND RESULTS")
        print("=" * 35)
        
        # Save models
        for model_name, model in self.models.items():
            filename = f"{model_name}_model.joblib"
            joblib.dump(model, filename)
            print(f"✅ Saved: {filename}")
        
        # Save scalers and encoders
        joblib.dump(self.scalers, 'ensemble_scalers.joblib')
        joblib.dump(self.encoders, 'ensemble_encoders.joblib')
        print("✅ Saved: ensemble_scalers.joblib")
        print("✅ Saved: ensemble_encoders.joblib")
        
        # Prepare results for JSON (remove model objects)
        json_results = {}
        for key, result in self.results.items():
            json_result = {k: v for k, v in result.items() if k != 'model'}
            # Convert numpy arrays to lists
            for k, v in json_result.items():
                if isinstance(v, np.ndarray):
                    json_result[k] = v.tolist()
            json_results[key] = json_result
        
        # Save results
        with open('ensemble_training_results.json', 'w') as f:
            json.dump(json_results, f, indent=2)
        print("✅ Saved: ensemble_training_results.json")
    
    def generate_training_report(self) -> str:
        """Generate comprehensive training report"""
        # Find best models
        disease_models = {k: v for k, v in self.results.items() if k.startswith('disease_')}
        weed_models = {k: v for k, v in self.results.items() if k.startswith('weed_')}
        
        best_disease = max(disease_models.keys(), key=lambda k: disease_models[k]['test_accuracy'])
        best_weed = max(weed_models.keys(), key=lambda k: weed_models[k]['test_accuracy'])
        
        disease_shape = self.disease_data.shape if self.disease_data is not None else (0, 0)
        weed_shape = self.weed_data.shape if self.weed_data is not None else (0, 0)
        
        report = f"""
# Advanced Ensemble Training Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Training Summary

### Disease Detection Models
- **Data**: {disease_shape[0]} samples, {disease_shape[1]} features
- **Best Model**: {best_disease}
- **Best Accuracy**: {self.results[best_disease]['test_accuracy']:.3f}
- **Ensemble Accuracy**: {self.results['disease_ensemble']['test_accuracy']:.3f}

### Weed Management Models  
- **Data**: {weed_shape[0]} samples, {weed_shape[1]} features
- **Best Model**: {best_weed}
- **Best Accuracy**: {self.results[best_weed]['test_accuracy']:.3f}
- **Ensemble Accuracy**: {self.results['weed_ensemble']['test_accuracy']:.3f}

## Model Performance Comparison

### Disease Detection Results
"""
        
        for model_name, results in disease_models.items():
            report += f"""
**{model_name}**
- Test Accuracy: {results['test_accuracy']:.3f}
- CV Score: {results['cv_mean']:.3f} ± {results['cv_std']:.3f}
- F1 Score: {results['f1_score']:.3f}
"""
        
        report += "\n### Weed Management Results\n"
        
        for model_name, results in weed_models.items():
            report += f"""
**{model_name}**
- Test Accuracy: {results['test_accuracy']:.3f}
- CV Score: {results['cv_mean']:.3f} ± {results['cv_std']:.3f}
- F1 Score: {results['f1_score']:.3f}
"""
        
        # Calculate improvement over baseline
        baseline_disease = 0.175  # From previous analysis
        baseline_weed = 0.225
        
        disease_improvement = (self.results[best_disease]['test_accuracy'] - baseline_disease) / baseline_disease * 100
        weed_improvement = (self.results[best_weed]['test_accuracy'] - baseline_weed) / baseline_weed * 100
        
        report += f"""
## Improvement Analysis

### Disease Detection
- **Baseline**: {baseline_disease:.1%}
- **Current Best**: {self.results[best_disease]['test_accuracy']:.1%}
- **Improvement**: {disease_improvement:.1f}%

### Weed Management
- **Baseline**: {baseline_weed:.1%}
- **Current Best**: {self.results[best_weed]['test_accuracy']:.1%}
- **Improvement**: {weed_improvement:.1f}%

## Phase 1 Target Assessment

- **Target**: 70-75% accuracy
- **Disease Achievement**: {'✅ TARGET MET' if self.results[best_disease]['test_accuracy'] >= 0.70 else '⚠️ Approaching Target'}
- **Weed Achievement**: {'✅ TARGET MET' if self.results[best_weed]['test_accuracy'] >= 0.70 else '⚠️ Approaching Target'}

## Next Steps

1. **Deep Learning Pipeline**: Implement neural networks with enhanced features
2. **AutoML Optimization**: Fine-tune hyperparameters with grid search
3. **Model Integration**: Deploy best models to production backend
4. **Continuous Learning**: Set up model retraining pipeline

## Saved Artifacts

- Individual Models: `*_model.joblib`
- Ensemble Models: `*_ensemble_model.joblib`
- Preprocessing: `ensemble_scalers.joblib`, `ensemble_encoders.joblib`
- Results: `ensemble_training_results.json`
"""
        
        return report
    
    def run_complete_training(self):
        """Run the complete ensemble training pipeline"""
        print("🚀 STARTING ADVANCED ENSEMBLE TRAINING")
        print("=" * 60)
        
        if not self.load_enhanced_datasets():
            return False
        
        # Train all models
        self.train_disease_models()
        self.train_weed_models()
        
        # Save everything
        self.save_models_and_results()
        
        # Generate report
        report = self.generate_training_report()
        with open('ensemble_training_report.md', 'w') as f:
            f.write(report)
        
        print("\n" + "=" * 60)
        print("✅ ENSEMBLE TRAINING COMPLETE")
        print("=" * 60)
        print("🎯 Phase 1 Target: 70-75% accuracy")
        print("📈 Models ready for Phase 2 deep learning")
        print("📋 Training report: ensemble_training_report.md")
        
        return True

def main():
    """Run the advanced ensemble training system"""
    trainer = AdvancedEnsembleTrainer()
    trainer.run_complete_training()

if __name__ == "__main__":
    main()