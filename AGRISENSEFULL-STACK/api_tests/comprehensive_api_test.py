#!/usr/bin/env python3
"""
Comprehensive API integration test for the trained plant health models
"""

import sys
import os
import requests
import json
import base64
from typing import Dict, Any

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agrisense_app', 'backend'))

BASE_URL = "http://127.0.0.1:8004"

def encode_mock_image() -> str:
    """Create a mock base64 encoded image for testing"""
    # Create a small mock image data
    mock_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    return base64.b64encode(mock_image_data).decode('utf-8')

def test_backend_health() -> bool:
    """Test if the backend is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_disease_detection_api() -> Dict[str, Any]:
    """Test the disease detection API with trained models"""
    print("\n🦠 Testing Disease Detection API")
    print("-" * 45)
    
    # Prepare test data with crop type and environmental data
    test_data = {
        "image_data": encode_mock_image(),
        "crop_type": "Tomato",
        "environmental_data": {
            "humidity_pct": 75.0,
            "leaf_wetness_duration_hours": 8.0,
            "rainfall_mm": 12.0,
            "min_temperature_c": 18.0,
            "max_temperature_c": 28.0,
            "avg_temperature_c": 23.0
        },
        "field_info": {
            "location": "test_field",
            "growth_stage": "flowering"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/disease/detect",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Disease Detection API Success!")
            print(f"   Disease Type: {result.get('disease_type', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}%")
            print(f"   Severity: {result.get('severity', 'N/A')}")
            print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
            
            # Check if it's using the trained model
            model_info = result.get('model_info', {})
            print(f"   Model Type: {model_info.get('type', 'N/A')}")
            if 'accuracy' in model_info:
                print(f"   Model Accuracy: {model_info['accuracy']}%")
            
            # Check treatment recommendations
            treatment = result.get('treatment', {})
            if treatment:
                print(f"   Treatment Available: ✅")
                
            return {"success": True, "using_trained_model": model_info.get('type') != 'Mock Model', "result": result}
        else:
            print(f"❌ Disease Detection Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Disease Detection Connection Error: {e}")
        return {"success": False, "error": str(e)}

def test_weed_management_api() -> Dict[str, Any]:
    """Test the weed management API with trained models"""
    print("\n🌿 Testing Weed Management API")
    print("-" * 45)
    
    # Prepare test data with crop type and environmental data
    test_data = {
        "image_data": encode_mock_image(),
        "crop_type": "Wheat",
        "environmental_data": {
            "soil_moisture_pct": 35.0,
            "ndvi": 0.7,
            "canopy_cover_pct": 60.0,
            "weed_density_plants_per_m2": 30.0
        },
        "field_info": {
            "location": "test_field",
            "growth_stage": "vegetative"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/weed/analyze",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Weed Management API Success!")
            
            # Check different result formats (both new and old)
            if 'dominant_weed_species' in result:
                # New trained model format
                print(f"   Dominant Species: {result.get('dominant_weed_species', 'N/A')}")
                print(f"   Confidence: {result.get('confidence', 'N/A')}%")
                print(f"   Weed Pressure: {result.get('weed_pressure', 'N/A')}")
                print(f"   Coverage: {result.get('coverage_percentage', 'N/A')}%")
                print(f"   Action Required: {result.get('action_required', 'N/A')}")
                
                # Check model info
                model_info = result.get('model_info', {})
                print(f"   Model Type: {model_info.get('type', 'N/A')}")
                if 'accuracy' in model_info:
                    print(f"   Model Accuracy: {model_info['accuracy']}%")
                    
                # Check management plan
                plan = result.get('management_plan', {})
                if plan:
                    print(f"   Urgency: {plan.get('urgency', 'N/A')}")
                    print(f"   Herbicide: {plan.get('recommended_herbicide', 'N/A')}")
                    print(f"   Cost/ha: ${plan.get('estimated_cost_per_hectare', 'N/A')}")
                    
                return {"success": True, "using_trained_model": True, "result": result}
            else:
                # Old format
                print(f"   Coverage: {result.get('weed_coverage_percentage', 'N/A')}%")
                print(f"   Pressure: {result.get('weed_pressure', 'N/A')}")
                print(f"   Regions: {len(result.get('weed_regions', []))}")
                return {"success": True, "using_trained_model": False, "result": result}
                
        else:
            print(f"❌ Weed Management Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Weed Management Connection Error: {e}")
        return {"success": False, "error": str(e)}

def test_comprehensive_health_api() -> Dict[str, Any]:
    """Test the comprehensive health assessment API"""
    print("\n🏥 Testing Comprehensive Health Assessment API")
    print("-" * 50)
    
    # Prepare test data
    test_data = {
        "image_data": encode_mock_image(),
        "crop_type": "Tomato",
        "environmental_data": {
            "humidity_pct": 75.0,
            "leaf_wetness_duration_hours": 8.0,
            "rainfall_mm": 12.0,
            "min_temperature_c": 18.0,
            "max_temperature_c": 28.0,
            "avg_temperature_c": 23.0,
            "soil_moisture_pct": 35.0,
            "ndvi": 0.7,
            "canopy_cover_pct": 60.0,
            "weed_density_plants_per_m2": 30.0
        },
        "field_info": {
            "location": "integrated_test_field",
            "growth_stage": "flowering",
            "field_size_hectares": 2.5
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/health/assess",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Comprehensive Health Assessment Success!")
            print(f"   Assessment ID: {result.get('assessment_id', 'N/A')}")
            print(f"   Overall Health Score: {result.get('overall_health_score', 'N/A')}/100")
            print(f"   Alert Level: {result.get('alert_level', 'N/A')}")
            
            # Check disease analysis
            disease_analysis = result.get('disease_analysis', {})
            if disease_analysis:
                print(f"   Disease Status: {disease_analysis.get('disease_type', 'N/A')}")
                
            # Check weed analysis  
            weed_analysis = result.get('weed_analysis', {})
            if weed_analysis:
                if 'dominant_weed_species' in weed_analysis:
                    print(f"   Weed Species: {weed_analysis.get('dominant_weed_species', 'N/A')}")
                else:
                    print(f"   Weed Coverage: {weed_analysis.get('weed_coverage_percentage', 'N/A')}%")
                
            # Check recommendations
            recommendations = result.get('recommendations', {})
            if recommendations:
                print(f"   Recommendations: ✅ Available")
                
            return {"success": True, "result": result}
        else:
            print(f"❌ Comprehensive Assessment Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return {"success": False, "error": response.text}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Comprehensive Assessment Connection Error: {e}")
        return {"success": False, "error": str(e)}

def test_direct_engine_integration():
    """Test the engines directly to verify they're using trained models"""
    print("\n🔧 Testing Direct Engine Integration")
    print("-" * 45)
    
    try:
        from agrisense_app.backend.disease_detection import DiseaseDetectionEngine
        from agrisense_app.backend.weed_management import WeedManagementEngine
        
        # Test disease engine
        disease_engine = DiseaseDetectionEngine()
        disease_has_trained = hasattr(disease_engine, 'model') and disease_engine.model is not None
        disease_accuracy = getattr(disease_engine, 'model_accuracy', 0) * 100 if disease_has_trained else 0
        
        # Test weed engine
        weed_engine = WeedManagementEngine()
        weed_has_trained = hasattr(weed_engine, 'model') and weed_engine.model is not None
        weed_accuracy = getattr(weed_engine, 'model_accuracy', 0) * 100 if weed_has_trained else 0
        
        print(f"✅ Disease Engine - Trained Model: {'Yes' if disease_has_trained else 'No'}")
        if disease_has_trained:
            print(f"   Disease Model Accuracy: {disease_accuracy:.1f}%")
            
        print(f"✅ Weed Engine - Trained Model: {'Yes' if weed_has_trained else 'No'}")
        if weed_has_trained:
            print(f"   Weed Model Accuracy: {weed_accuracy:.1f}%")
            
        return {
            "disease_engine_ready": disease_has_trained,
            "weed_engine_ready": weed_has_trained,
            "disease_accuracy": disease_accuracy,
            "weed_accuracy": weed_accuracy
        }
        
    except Exception as e:
        print(f"❌ Direct engine test failed: {e}")
        return {"error": str(e)}

def main():
    """Run comprehensive integration tests"""
    print("🌱 AgriSense Plant Health API Integration Tests")
    print("=" * 60)
    print("Testing trained ML models integration with API endpoints")
    print("=" * 60)
    
    # Test results storage
    results = {
        "backend_health": False,
        "disease_api": {"success": False},
        "weed_api": {"success": False},
        "comprehensive_api": {"success": False},
        "direct_engines": {}
    }
    
    # 1. Test backend health
    print("\n1️⃣ BACKEND HEALTH CHECK")
    results["backend_health"] = test_backend_health()
    
    if not results["backend_health"]:
        print("\n💡 To start the backend, run:")
        print("   uvicorn agrisense_app.backend.main:app --reload --port 8004")
        return results
    
    # 2. Test direct engines
    print("\n2️⃣ DIRECT ENGINE INTEGRATION")
    results["direct_engines"] = test_direct_engine_integration()
    
    # 3. Test individual APIs
    print("\n3️⃣ API ENDPOINT TESTS")
    results["disease_api"] = test_disease_detection_api()
    results["weed_api"] = test_weed_management_api()
    results["comprehensive_api"] = test_comprehensive_health_api()
    
    # 4. Generate comprehensive report
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"🏥 Backend Health: {'✅ PASS' if results['backend_health'] else '❌ FAIL'}")
    print(f"🦠 Disease Detection API: {'✅ PASS' if results['disease_api']['success'] else '❌ FAIL'}")
    print(f"🌿 Weed Management API: {'✅ PASS' if results['weed_api']['success'] else '❌ FAIL'}")
    print(f"🏥 Comprehensive Health API: {'✅ PASS' if results['comprehensive_api']['success'] else '❌ FAIL'}")
    
    # Model status
    if 'disease_engine_ready' in results['direct_engines']:
        disease_ready = results['direct_engines']['disease_engine_ready']
        weed_ready = results['direct_engines']['weed_engine_ready']
        print(f"🤖 Disease Model Integration: {'✅ TRAINED' if disease_ready else '❌ MOCK'}")
        print(f"🤖 Weed Model Integration: {'✅ TRAINED' if weed_ready else '❌ MOCK'}")
        
        if disease_ready:
            print(f"   Disease Model Accuracy: {results['direct_engines']['disease_accuracy']:.1f}%")
        if weed_ready:
            print(f"   Weed Model Accuracy: {results['direct_engines']['weed_accuracy']:.1f}%")
    
    # Overall status
    all_pass = (
        results["backend_health"] and
        results["disease_api"]["success"] and
        results["weed_api"]["success"] and
        results["comprehensive_api"]["success"]
    )
    
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 ALL TESTS PASSED! Plant Health API Integration Complete!")
        print("✅ Your AgriSense system is ready for production use!")
        print("🚀 Frontend can now connect to trained ML models via API!")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        print("💡 Ensure the backend is running and models are trained.")
    
    print("=" * 60)
    return results

if __name__ == "__main__":
    main()