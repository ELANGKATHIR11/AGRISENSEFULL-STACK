#!/usr/bin/env python3
"""
Treatment Recommendations Validation Test
Validates that disease detection provides comprehensive treatment recommendations
"""

import requests
import base64
import io
from PIL import Image, ImageDraw
import json

def create_disease_image(disease_pattern="spots"):
    """Create a synthetic diseased plant image"""
    img = Image.new('RGB', (300, 300), (50, 120, 50))  # Dark green background
    draw = ImageDraw.Draw(img)
    
    # Draw plant structure
    draw.rectangle([140, 50, 160, 250], fill=(60, 140, 60))  # Stem
    
    # Add leaves with disease patterns
    leaves = [(100, 80), (200, 80), (80, 130), (220, 130), (90, 180), (210, 180)]
    
    for i, (x, y) in enumerate(leaves):
        # Base leaf
        draw.ellipse([x-20, y-15, x+20, y+15], fill=(70, 150, 70))
        
        # Add disease pattern
        if disease_pattern == "spots":
            # Dark spots for bacterial/fungal diseases
            if i % 2 == 0:
                draw.ellipse([x-8, y-8, x+8, y+8], fill=(40, 30, 20))
                draw.ellipse([x-5, y+5, x+5, y+15], fill=(60, 40, 20))
        elif disease_pattern == "yellowing":
            # Yellow patches for nutrient deficiency
            if i % 3 == 0:
                draw.ellipse([x-15, y-10, x+15, y+10], fill=(160, 160, 80))
        elif disease_pattern == "wilting":
            # Brown edges for wilt diseases
            if i % 2 == 0:
                draw.ellipse([x-20, y-15, x+20, y+15], fill=(100, 80, 50))
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def test_treatment_recommendations():
    """Test treatment recommendations for various crops and diseases"""
    
    print("🧪 Testing Treatment Recommendations Validation")
    print("=" * 60)
    
    # Test cases: crop, disease pattern, expected treatment categories
    test_cases = [
        ("Cotton", "spots", "Bacterial disease treatment"),
        ("Rice", "spots", "Fungal disease treatment"),
        ("Tomato", "spots", "Bacterial/fungal treatment"),
        ("Wheat", "yellowing", "Nutrient management"),
        ("Potato", "wilting", "Wilt disease management"),
        ("Maize", "spots", "Leaf disease treatment"),
        ("Sugarcane", "spots", "Disease management"),
        ("Groundnut", "yellowing", "Nutrient/disease management")
    ]
    
    results = {
        "total_tests": len(test_cases),
        "successful_treatments": 0,
        "comprehensive_treatments": 0,
        "results": []
    }
    
    for crop, pattern, expected_category in test_cases:
        print(f"\n🌱 Testing {crop} with {pattern}...")
        
        # Create test image
        image_data = create_disease_image(pattern)
        
        # Test disease detection
        payload = {
            'image_data': image_data,
            'crop_type': crop,
            'environmental_data': {
                'temperature': 26.0,
                'humidity': 75.0,
                'soil_moisture': 65.0,
                'ph': 6.5
            }
        }
        
        try:
            response = requests.post('http://127.0.0.1:8004/disease/detect', json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract treatment information
                disease_type = result.get("disease_type", "unknown")
                confidence = result.get("confidence", 0.0)
                severity = result.get("severity", "unknown")
                treatment = result.get("treatment", {})
                prevention = result.get("prevention", {})
                management_priority = result.get("management_priority", "unknown")
                
                print(f"  ✅ Disease: {disease_type} ({confidence:.1%} confidence)")
                print(f"     Severity: {severity}")
                print(f"     Priority: {management_priority}")
                
                # Validate treatment completeness
                treatment_score = 0
                treatment_categories = ["immediate", "chemical", "organic", "prevention"]
                
                for category in treatment_categories:
                    if category in treatment and treatment[category]:
                        treatment_score += 1
                        print(f"     {category.title()}: {treatment[category][0]}")
                
                # Validate prevention recommendations
                prevention_score = 0
                if prevention:
                    prevention_categories = ["general", "specific", "next_season", "long_term"]
                    for category in prevention_categories:
                        if category in prevention and prevention[category]:
                            prevention_score += 1
                
                print(f"     Treatment Categories: {treatment_score}/4")
                print(f"     Prevention Categories: {prevention_score}/4")
                
                # Record results
                test_result = {
                    "crop": crop,
                    "disease_pattern": pattern,
                    "detected_disease": disease_type,
                    "confidence": confidence,
                    "severity": severity,
                    "treatment_score": treatment_score,
                    "prevention_score": prevention_score,
                    "management_priority": management_priority,
                    "comprehensive": treatment_score >= 3 and prevention_score >= 2
                }
                
                results["results"].append(test_result)
                
                if treatment_score > 0:
                    results["successful_treatments"] += 1
                
                if test_result["comprehensive"]:
                    results["comprehensive_treatments"] += 1
                    print("     ✅ COMPREHENSIVE TREATMENT DETECTED")
                else:
                    print("     ⚠️ Treatment could be more comprehensive")
                    
            else:
                print(f"  ❌ HTTP Error: {response.status_code}")
                results["results"].append({
                    "crop": crop,
                    "disease_pattern": pattern,
                    "error": f"HTTP {response.status_code}",
                    "comprehensive": False
                })
                
        except Exception as e:
            print(f"  ⚠️ Exception: {str(e)[:50]}")
            results["results"].append({
                "crop": crop,
                "disease_pattern": pattern,
                "error": str(e),
                "comprehensive": False
            })
    
    # Print summary
    print(f"\n📊 Treatment Validation Summary:")
    print(f"  Total Tests: {results['total_tests']}")
    print(f"  Successful Treatments: {results['successful_treatments']}")
    print(f"  Comprehensive Treatments: {results['comprehensive_treatments']}")
    print(f"  Success Rate: {(results['successful_treatments']/results['total_tests']*100):.1f}%")
    print(f"  Comprehensive Rate: {(results['comprehensive_treatments']/results['total_tests']*100):.1f}%")
    
    # Detailed analysis
    print(f"\n📋 Detailed Analysis:")
    for result in results["results"]:
        if not result.get("error"):
            crop = result["crop"]
            disease = result["detected_disease"]
            treatment_score = result["treatment_score"]
            comprehensive = "✅" if result["comprehensive"] else "⚠️"
            print(f"  {comprehensive} {crop}: {disease} (Treatment: {treatment_score}/4)")
    
    # Save results
    timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"treatment_validation_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    test_treatment_recommendations()