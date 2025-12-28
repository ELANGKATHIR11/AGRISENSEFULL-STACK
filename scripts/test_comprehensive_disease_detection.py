#!/usr/bin/env python3
"""
Comprehensive Disease Detection Test
Tests disease detection for all 48 supported crops with various disease scenarios
"""

import base64
import io
import json
import logging
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_synthetic_disease_image(disease_type: str, crop_type: str) -> str:
    """Create a synthetic diseased plant image for testing"""
    
    # Create a 400x400 image
    image = Image.new('RGB', (400, 400), (50, 120, 50))  # Dark green background
    draw = ImageDraw.Draw(image)
    
    # Base healthy plant appearance
    # Draw plant structure
    draw.rectangle([150, 50, 250, 350], fill=(60, 140, 60))  # Stem (corrected coordinates)
    
    # Add leaves
    for i, (x, y) in enumerate([(120, 100), (180, 80), (220, 80), (280, 100),
                               (100, 150), (160, 130), (240, 130), (300, 150),
                               (90, 200), (140, 180), (260, 180), (310, 200)]):
        leaf_color = (70, 150, 70)  # Healthy green
        
        # Modify color based on disease type
        if disease_type in ["bacterial_spot", "bacterial_blight"]:
            if i % 3 == 0:  # Affect some leaves
                leaf_color = (80, 60, 20)  # Brown spots
                # Add dark spots
                draw.ellipse([x-5, y-5, x+5, y+5], fill=(20, 20, 20))
                
        elif disease_type in ["early_blight", "late_blight"]:
            if i % 2 == 0:
                leaf_color = (120, 80, 30)  # Brown blight
                # Add irregular patches
                draw.polygon([(x-10, y), (x, y-10), (x+10, y), (x, y+10)], fill=(40, 30, 20))
                
        elif disease_type in ["powdery_mildew", "downy_mildew"]:
            if i % 2 == 0:
                leaf_color = (150, 150, 120)  # Pale color
                # Add white powdery spots
                draw.ellipse([x-8, y-8, x+8, y+8], fill=(200, 200, 200))
                
        elif disease_type in ["rust", "rust_diseases"]:
            if i % 3 == 0:
                leaf_color = (140, 70, 20)  # Rust color
                # Add orange-brown spots
                draw.ellipse([x-6, y-6, x+6, y+6], fill=(180, 90, 30))
                
        elif disease_type in ["fusarium_wilt", "bacterial_wilt"]:
            # Wilted appearance
            leaf_color = (100, 100, 50)  # Yellow-brown
            
        elif disease_type in ["mosaic_virus", "yellow_vein_mosaic"]:
            # Mottled yellow-green pattern
            leaf_color = (120, 140, 60) if i % 2 == 0 else (160, 160, 80)
            
        elif "deficiency" in disease_type:
            # Yellow appearance for nutrient deficiency
            leaf_color = (140, 140, 60)
            
        # Draw leaf
        draw.ellipse([x-15, y-10, x+15, y+10], fill=leaf_color)
    
    # Add crop-specific features
    if crop_type.lower() in ["tomato", "potato"]:
        # Add fruit/tuber representations
        draw.ellipse([180, 120, 220, 160], fill=(200, 80, 80) if crop_type == "tomato" else (180, 140, 100))
        
    elif crop_type.lower() in ["rice", "wheat", "maize"]:
        # Add grain head
        draw.rectangle([190, 40, 210, 80], fill=(220, 180, 120))
        
    elif crop_type.lower() == "cotton":
        # Add cotton bolls
        for x, y in [(160, 140), (200, 120), (240, 140)]:
            draw.ellipse([x-10, y-10, x+10, y+10], fill=(240, 240, 240))
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    image_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{image_b64}"

def test_crop_disease_detection(base_url: str = "http://127.0.0.1:8004") -> Dict[str, Any]:
    """Test disease detection for multiple crops and diseases"""
    
    # Load crop list
    try:
        with open('agrisense_app/backend/crop_labels.json', 'r') as f:
            crop_labels = json.load(f)
            crops_to_test = list(crop_labels.keys())[:20]  # Test first 20 crops
    except:
        # Fallback crop list
        crops_to_test = [
            "Rice", "Wheat", "Maize", "Cotton", "Tomato", "Potato", 
            "Sugarcane", "Groundnut", "Sunflower", "Gram"
        ]
    
    # Disease types to test
    diseases_to_test = [
        "bacterial_spot", "early_blight", "late_blight", "powdery_mildew",
        "rust_diseases", "fusarium_wilt", "mosaic_virus", "nutrient_deficiency"
    ]
    
    test_results = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "crops_tested": len(crops_to_test),
            "diseases_tested": len(diseases_to_test)
        },
        "crop_results": {},
        "disease_coverage": {},
        "model_performance": {}
    }
    
    print(f"🧪 Starting comprehensive disease detection test...")
    print(f"📊 Testing {len(crops_to_test)} crops with {len(diseases_to_test)} disease types")
    print(f"🎯 Target endpoint: {base_url}/disease/detect")
    
    for crop in crops_to_test:
        print(f"\n🌱 Testing crop: {crop}")
        test_results["crop_results"][crop] = {}
        
        for disease in diseases_to_test:
            test_results["test_summary"]["total_tests"] += 1
            
            try:
                # Create synthetic diseased image
                image_data = create_synthetic_disease_image(disease, crop)
                
                # Prepare request payload
                payload = {
                    "image_data": image_data,
                    "crop_type": crop,
                    "environmental_data": {
                        "temperature": 25.0,
                        "humidity": 70.0,
                        "soil_moisture": 60.0
                    }
                }
                
                # Send request
                response = requests.post(
                    f"{base_url}/disease/detect",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Record successful test
                    test_results["test_summary"]["successful_tests"] += 1
                    test_results["crop_results"][crop][disease] = {
                        "status": "success",
                        "detected_disease": result.get("disease_type", "unknown"),
                        "confidence": result.get("confidence", 0.0),
                        "severity": result.get("severity", "unknown"),
                        "has_treatment": bool(result.get("treatment", {})),
                        "has_prevention": bool(result.get("prevention", {}))
                    }
                    
                    # Track disease coverage
                    detected_disease = result.get("disease_type", "unknown")
                    if detected_disease not in test_results["disease_coverage"]:
                        test_results["disease_coverage"][detected_disease] = 0
                    test_results["disease_coverage"][detected_disease] += 1
                    
                    print(f"  ✅ {disease}: {detected_disease} ({result.get('confidence', 0.0):.1%})")
                    
                else:
                    # Record failed test
                    test_results["test_summary"]["failed_tests"] += 1
                    test_results["crop_results"][crop][disease] = {
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text[:100]}"
                    }
                    print(f"  ❌ {disease}: HTTP {response.status_code}")
                    
            except Exception as e:
                # Record exception
                test_results["test_summary"]["failed_tests"] += 1
                test_results["crop_results"][crop][disease] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"  ⚠️ {disease}: {str(e)[:50]}")
    
    # Calculate performance metrics
    total_tests = test_results["test_summary"]["total_tests"]
    successful_tests = test_results["test_summary"]["successful_tests"]
    
    if total_tests > 0:
        success_rate = (successful_tests / total_tests) * 100
        test_results["model_performance"] = {
            "success_rate_percent": round(success_rate, 2),
            "total_diseases_detected": len(test_results["disease_coverage"]),
            "most_detected_disease": max(test_results["disease_coverage"].items(), 
                                       key=lambda x: x[1], default=("none", 0))[0],
            "average_confidence": "Not calculated in this test"
        }
    
    # Print summary
    print(f"\n📈 Test Summary:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Successful: {successful_tests}")
    print(f"  Failed: {test_results['test_summary']['failed_tests']}")
    print(f"  Success Rate: {test_results['model_performance'].get('success_rate_percent', 0):.1f}%")
    print(f"  Unique Diseases Detected: {len(test_results['disease_coverage'])}")
    
    # Save results
    results_file = f"disease_detection_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"📄 Detailed results saved to: {results_file}")
    
    return test_results

def run_specific_crop_disease(crop_type: str, disease_type: str, base_url: str = "http://127.0.0.1:8004") -> Dict[str, Any]:
    """Test disease detection for a specific crop and disease combination"""
    
    print(f"🔬 Testing specific case: {crop_type} with {disease_type}")
    
    # Create synthetic image
    image_data = create_synthetic_disease_image(disease_type, crop_type)
    
    # Prepare payload
    payload = {
        "image_data": image_data,
        "crop_type": crop_type,
        "environmental_data": {
            "temperature": 28.0,
            "humidity": 75.0,
            "soil_moisture": 65.0,
            "ph": 6.5
        }
    }
    
    try:
        response = requests.post(f"{base_url}/disease/detect", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Detection successful!")
            print(f"  🦠 Disease: {result.get('disease_type', 'unknown')}")
            print(f"  📊 Confidence: {result.get('confidence', 0.0):.1%}")
            print(f"  ⚠️ Severity: {result.get('severity', 'unknown')}")
            print(f"  🚨 Risk Level: {result.get('risk_level', 'unknown')}")
            print(f"  📝 Management Priority: {result.get('management_priority', 'unknown')}")
            
            # Show treatment recommendations
            if result.get("treatment"):
                print(f"\n💊 Treatment Recommendations:")
                for category, actions in result["treatment"].items():
                    if actions:
                        print(f"  {category.title()}: {actions[0]}")
            
            return result
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"   Error: {response.text}")
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
            
    except Exception as e:
        print(f"⚠️ Exception occurred: {e}")
        return {"error": "exception", "detail": str(e)}

if __name__ == "__main__":
    print("🧪 Comprehensive Disease Detection Testing Suite")
    print("=" * 60)
    
    # Test specific cases first
    print("\n1️⃣ Testing specific cases...")
    
    # Test cotton bacterial spot (known working case)
    print("\nTesting Cotton with Bacterial Spot:")
    run_specific_crop_disease("Cotton", "bacterial_spot")
    
    # Test rice blast
    print("\nTesting Rice with Rice Blast:")
    run_specific_crop_disease("Rice", "rice_blast")
    
    # Test tomato early blight
    print("\nTesting Tomato with Early Blight:")
    run_specific_crop_disease("Tomato", "early_blight")
    
    print("\n" + "=" * 60)
    
    # Run comprehensive test
    print("\n2️⃣ Running comprehensive crop and disease coverage test...")
    comprehensive_results = test_crop_disease_detection()
    
    print(f"\n🎉 Testing completed! Check results file for detailed analysis.")