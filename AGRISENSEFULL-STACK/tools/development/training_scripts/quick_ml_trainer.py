#!/usr/bin/env python3
"""
Quick ML Training Script - Fix Critical Issues and Train Models
"""

import os
import pandas as pd
import numpy as np
import joblib
import warnings
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

warnings.filterwarnings('ignore')

def main():
    """Quick training to fix critical issues"""
    print("🚀 QUICK ML TRAINING - FIXING CRITICAL ISSUES")
    print("=" * 60)
    
    # Try to load enhanced datasets
    try:
        if os.path.exists('enhanced_disease_dataset.csv'):
            disease_data = pd.read_csv('enhanced_disease_dataset.csv')
            print(f"✅ Disease dataset: {disease_data.shape}")
        else:
            disease_data = pd.read_csv('crop_disease_dataset.csv')
            print(f"⚠️ Using original disease dataset: {disease_data.shape}")
            
        if os.path.exists('enhanced_weed_dataset.csv'):
            weed_data = pd.read_csv('enhanced_weed_dataset.csv')
            print(f"✅ Weed dataset: {weed_data.shape}")
        else:
            weed_data = pd.read_csv('weed_management_dataset.csv')
            print(f"⚠️ Using original weed dataset: {weed_data.shape}")
            
    except Exception as e:
        print(f"❌ Error loading datasets: {e}")
        return
    
    # Train quick disease model
    print("\n🦠 Training Disease Model")
    try:
        X = disease_data.drop(['disease_label'], axis=1)
        y = disease_data['disease_label']
        
        # Encode categorical features
        for col in X.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Encode target
        le_target = LabelEncoder()
        y_encoded = le_target.fit_transform(y.astype(str))
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Disease Model Accuracy: {accuracy:.3f}")
        
        # Save model
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        joblib.dump(rf, f'disease_model_{timestamp}.joblib')
        joblib.dump(scaler, f'disease_scaler_{timestamp}.joblib')
        joblib.dump(le_target, f'disease_encoder_{timestamp}.joblib')
        
        print(f"💾 Disease model saved: disease_model_{timestamp}.joblib")
        
    except Exception as e:
        print(f"❌ Error training disease model: {e}")
    
    # Train quick weed model
    print("\n🌿 Training Weed Model")
    try:
        X = weed_data.drop(['dominant_weed_species'], axis=1)
        y = weed_data['dominant_weed_species']
        
        # Encode categorical features
        for col in X.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Encode target
        le_target = LabelEncoder()
        y_encoded = le_target.fit_transform(y.astype(str))
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Weed Model Accuracy: {accuracy:.3f}")
        
        # Save model
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        joblib.dump(rf, f'weed_model_{timestamp}.joblib')
        joblib.dump(scaler, f'weed_scaler_{timestamp}.joblib')
        joblib.dump(le_target, f'weed_encoder_{timestamp}.joblib')
        
        print(f"💾 Weed model saved: weed_model_{timestamp}.joblib")
        
    except Exception as e:
        print(f"❌ Error training weed model: {e}")
    
    print("\n" + "=" * 60)
    print("✅ QUICK TRAINING COMPLETE")
    print("🎯 Models ready for backend integration")
    print("=" * 60)

if __name__ == "__main__":
    main()