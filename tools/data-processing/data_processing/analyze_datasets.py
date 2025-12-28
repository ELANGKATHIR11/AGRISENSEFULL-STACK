#!/usr/bin/env python3
"""
Dataset Analysis Script for AgriSense Plant Health ML Training
Analyzes crop disease and weed management datasets for ML model training
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

def analyze_crop_disease_dataset():
    """Analyze the crop disease dataset"""
    print('🔬 CROP DISEASE DATASET ANALYSIS')
    print('=' * 50)
    
    df = pd.read_csv('crop_disease_dataset.csv')
    
    print(f'📋 Dataset Overview:')
    print(f'  • Total samples: {len(df)}')
    print(f'  • Features: {len(df.columns)}')
    print(f'  • Missing values: {df.isnull().sum().sum()}')
    
    print(f'\n🦠 Disease Classes:')
    disease_counts = df['disease_label'].value_counts()
    print(f'  • Unique diseases: {len(disease_counts)}')
    for disease, count in disease_counts.items():
        print(f'    - {disease}: {count} samples ({count/len(df)*100:.1f}%)')
    
    print(f'\n🌱 Crop Types:')
    crop_counts = df['crop_type'].value_counts()
    for crop, count in crop_counts.items():
        print(f'    - {crop}: {count} samples ({count/len(df)*100:.1f}%)')
    
    print(f'\n📊 Feature Statistics:')
    numeric_features = ['temperature_c', 'humidity_pct', 'leaf_wetness_hours', 
                       'ndvi', 'lesion_count_per_leaf', 'severity_percent']
    
    for feature in numeric_features:
        if feature in df.columns:
            print(f'  • {feature}: mean={df[feature].mean():.2f}, std={df[feature].std():.2f}')
    
    return df

def analyze_weed_management_dataset():
    """Analyze the weed management dataset"""
    print('\n🌿 WEED MANAGEMENT DATASET ANALYSIS')
    print('=' * 50)
    
    df = pd.read_csv('weed_management_dataset.csv')
    
    print(f'📋 Dataset Overview:')
    print(f'  • Total samples: {len(df)}')
    print(f'  • Features: {len(df.columns)}')
    print(f'  • Missing values: {df.isnull().sum().sum()}')
    
    print(f'\n🌾 Weed Species:')
    weed_counts = df['dominant_weed_species'].value_counts()
    print(f'  • Unique species: {len(weed_counts)}')
    for weed, count in weed_counts.items():
        print(f'    - {weed}: {count} samples ({count/len(df)*100:.1f}%)')
    
    print(f'\n🌱 Crop Types:')
    crop_counts = df['crop_type'].value_counts()
    for crop, count in crop_counts.items():
        print(f'    - {crop}: {count} samples ({count/len(df)*100:.1f}%)')
    
    print(f'\n📊 Feature Statistics:')
    numeric_features = ['soil_moisture_pct', 'ndvi', 'canopy_cover_pct', 'weed_density_plants_per_m2']
    
    for feature in numeric_features:
        if feature in df.columns:
            print(f'  • {feature}: mean={df[feature].mean():.2f}, std={df[feature].std():.2f}')
    
    return df

def prepare_training_data(disease_df, weed_df):
    """Prepare data for ML training"""
    print('\n🔧 TRAINING DATA PREPARATION')
    print('=' * 50)
    
    # Disease data preparation
    disease_features = ['temperature_c', 'humidity_pct', 'leaf_wetness_hours', 
                       'ndvi', 'lesion_count_per_leaf', 'severity_percent']
    
    # Encode categorical features
    le_crop = LabelEncoder()
    le_growth = LabelEncoder()
    le_disease = LabelEncoder()
    
    disease_df_processed = disease_df.copy()
    disease_df_processed['crop_type_encoded'] = le_crop.fit_transform(disease_df['crop_type'])
    disease_df_processed['growth_stage_encoded'] = le_growth.fit_transform(disease_df['growth_stage'])
    disease_df_processed['disease_encoded'] = le_disease.fit_transform(disease_df['disease_label'])
    
    # Weed data preparation
    weed_features = ['soil_moisture_pct', 'ndvi', 'canopy_cover_pct', 'weed_density_plants_per_m2']
    
    le_weed_crop = LabelEncoder()
    le_weed_growth = LabelEncoder()
    le_weed_species = LabelEncoder()
    
    weed_df_processed = weed_df.copy()
    weed_df_processed['crop_type_encoded'] = le_weed_crop.fit_transform(weed_df['crop_type'])
    weed_df_processed['growth_stage_encoded'] = le_weed_growth.fit_transform(weed_df['growth_stage'])
    weed_df_processed['weed_encoded'] = le_weed_species.fit_transform(weed_df['dominant_weed_species'])
    
    print(f'✅ Disease dataset prepared: {len(disease_features)} numeric features + 2 categorical')
    print(f'✅ Weed dataset prepared: {len(weed_features)} numeric features + 2 categorical')
    
    return {
        'disease': {
            'df': disease_df_processed,
            'features': disease_features + ['crop_type_encoded', 'growth_stage_encoded'],
            'target': 'disease_encoded',
            'classes': list(le_disease.classes_),
            'encoders': {'crop': le_crop, 'growth': le_growth, 'disease': le_disease}
        },
        'weed': {
            'df': weed_df_processed,
            'features': weed_features + ['crop_type_encoded', 'growth_stage_encoded'],
            'target': 'weed_encoded',
            'classes': list(le_weed_species.classes_),
            'encoders': {'crop': le_weed_crop, 'growth': le_weed_growth, 'weed': le_weed_species}
        }
    }

def main():
    """Main analysis function"""
    print('🚀 AGRISENSE ML DATASET ANALYSIS')
    print('=' * 70)
    
    # Analyze datasets
    disease_df = analyze_crop_disease_dataset()
    weed_df = analyze_weed_management_dataset()
    
    # Prepare training data
    prepared_data = prepare_training_data(disease_df, weed_df)
    
    print('\n🎯 ML TRAINING RECOMMENDATIONS')
    print('=' * 50)
    print('✅ Disease Classification:')
    print(f'  • Input features: {len(prepared_data["disease"]["features"])}')
    print(f'  • Output classes: {len(prepared_data["disease"]["classes"])}')
    print(f'  • Recommended model: Random Forest or XGBoost')
    
    print('\n✅ Weed Detection:')
    print(f'  • Input features: {len(prepared_data["weed"]["features"])}')
    print(f'  • Output classes: {len(prepared_data["weed"]["classes"])}')
    print(f'  • Recommended model: Random Forest or Neural Network')
    
    print('\n🔄 Next Steps:')
    print('  1. Create ML training pipeline')
    print('  2. Train models with cross-validation')
    print('  3. Integrate trained models with backend')
    print('  4. Test with frontend plant health tabs')
    
    return prepared_data

if __name__ == '__main__':
    prepared_data = main()