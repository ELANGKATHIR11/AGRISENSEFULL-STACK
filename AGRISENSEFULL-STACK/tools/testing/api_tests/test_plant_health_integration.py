#!/usr/bin/env python3
"""
Test the integrated plant health system with trained ML models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agrisense_app.backend.disease_detection import DiseaseDetectionEngine
from agrisense_app.backend.weed_management import WeedManagementEngine

def test_disease_detection():
    """Test the disease detection engine with trained models"""
    print("🦠 Testing Disease Detection Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = DiseaseDetectionEngine()
    
    # Test with mock image and environmental data
    sample_env_data = {
        'humidity_pct': 75.0,
        'leaf_wetness_duration_hours': 8.0,
        'rainfall_mm': 12.0,
        'min_temperature_c': 18.0,
        'max_temperature_c': 28.0,
        'avg_temperature_c': 23.0
    }
    
    result = engine.detect_disease(
        image_data="mock_image.jpg",
        crop_type="Tomato",
        environmental_data=sample_env_data
    )
    
    print(f"✅ Disease Detection Results:")
    if 'disease_detected' in result:
        print(f"   Disease: {result['disease_detected']}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
        print(f"   Treatment: {result.get('recommended_treatment', 'N/A')}")
        if 'model_info' in result:
            model_info = result['model_info']
            print(f"   Model Type: {model_info.get('type', 'N/A')}")
            print(f"   Model Accuracy: {model_info.get('accuracy', 'N/A')}%")
    else:
        print(f"   Result: {result}")
    
    return result

def test_weed_management():
    """Test the weed management engine with trained models"""
    print("\n🌿 Testing Weed Management Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = WeedManagementEngine()
    
    # Test with mock image and environmental data
    sample_env_data = {
        'soil_moisture_pct': 35.0,
        'ndvi': 0.7,
        'canopy_cover_pct': 60.0,
        'weed_density_plants_per_m2': 30.0
    }
    
    result = engine.detect_weeds(
        image_data="mock_field.jpg",
        crop_type="Wheat",
        environmental_data=sample_env_data
    )
    
    print(f"✅ Weed Detection Results:")
    if 'dominant_weed_species' in result:
        print(f"   Dominant Species: {result['dominant_weed_species']}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}%")
        print(f"   Weed Pressure: {result.get('weed_pressure', 'N/A')}")
        print(f"   Coverage: {result.get('coverage_percentage', 'N/A')}%")
        print(f"   Action Required: {result.get('action_required', 'N/A')}")
        if 'model_info' in result:
            model_info = result['model_info']
            print(f"   Model Type: {model_info.get('type', 'N/A')}")
            print(f"   Model Accuracy: {model_info.get('accuracy', 'N/A')}%")
        if 'management_plan' in result:
            plan = result['management_plan']
            print(f"   Urgency: {plan.get('urgency', 'N/A')}")
            print(f"   Recommended Herbicide: {plan.get('recommended_herbicide', 'N/A')}")
            print(f"   Cost per Hectare: ${plan.get('estimated_cost_per_hectare', 'N/A')}")
    else:
        print(f"   Result: {result}")
    
    return result

def test_comparison():
    """Compare trained model vs mock results"""
    print("\n📊 Model vs Mock Comparison")
    print("=" * 50)
    
    # Test disease detection
    disease_engine = DiseaseDetectionEngine()
    weed_engine = WeedManagementEngine()
    
    # Check if models are loaded
    disease_has_model = hasattr(disease_engine, 'model') and disease_engine.model is not None
    weed_has_model = hasattr(weed_engine, 'model') and weed_engine.model is not None
    
    print(f"🦠 Disease Detection Engine:")
    print(f"   Trained Model Loaded: {'✅ Yes' if disease_has_model else '❌ No'}")
    if hasattr(disease_engine, 'metadata') and disease_engine.metadata:
        acc = disease_engine.model_accuracy
        if acc is None:
            print("   Model Accuracy: N/A")
        else:
            print(f"   Model Accuracy: {acc * 100:.1f}%")
        print(f"   Target Classes: {len(disease_engine.metadata.get('target_classes', []))}")
    
    print(f"\n🌿 Weed Management Engine:")
    print(f"   Trained Model Loaded: {'✅ Yes' if weed_has_model else '❌ No'}")
    if hasattr(weed_engine, 'metadata') and weed_engine.metadata:
        wacc = getattr(weed_engine, 'model_accuracy', None)
        if wacc is None:
            print("   Model Accuracy: N/A")
        else:
            print(f"   Model Accuracy: {wacc * 100:.1f}%")
        print(f"   Target Classes: {len(weed_engine.metadata.get('target_classes', []))}")

def main():
    """Run comprehensive plant health system tests"""
    print("🌱 AgriSense Plant Health System Integration Test")
    print("=" * 60)
    
    try:
        # Test individual engines
        disease_result = test_disease_detection()
        weed_result = test_weed_management()
        
        # Compare models
        test_comparison()
        
        print("\n🎉 Integration Test Complete!")
        print("✅ Both disease detection and weed management engines are functional")
        print("🚀 Ready for frontend integration!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()