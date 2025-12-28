#!/usr/bin/env python3
"""
Test Disease Detection System with Sample Images
"""

import requests
import base64
import json
from io import BytesIO
from PIL import Image, ImageDraw

def create_test_image(disease_type="healthy"):
    """Create a test image that simulates plant conditions"""
    # Create a 400x400 RGB image
    img = Image.new('RGB', (400, 400), color='lightgreen')
    draw = ImageDraw.Draw(img)
    
    if disease_type == "blight":
        # Add brown/black spots for blight
        for i in range(20):
            x, y = 50 + i*15, 50 + (i % 5)*60
            draw.ellipse([x, y, x+25, y+25], fill='brown')
            draw.ellipse([x+5, y+5, x+15, y+15], fill='black')
    
    elif disease_type == "rust":
        # Add orange/rusty colored spots
        for i in range(15):
            x, y = 60 + i*20, 60 + (i % 4)*70
            draw.ellipse([x, y, x+20, y+20], fill='orange')
            draw.ellipse([x+2, y+2, x+18, y+18], fill='darkorange')
    
    elif disease_type == "mildew":
        # Add white/gray powdery appearance
        for i in range(30):
            x, y = 40 + i*12, 40 + (i % 6)*50
            draw.ellipse([x, y, x+15, y+15], fill='lightgray')
            draw.ellipse([x+3, y+3, x+10, y+10], fill='white')
    
    elif disease_type == "yellowing":
        # Create yellowing effect for nutrient deficiency
        for i in range(0, 400, 20):
            for j in range(0, 400, 20):
                if (i + j) % 60 == 0:
                    draw.rectangle([i, j, i+15, j+15], fill='yellow')
    
    # Add some green texture for realism
    for i in range(100):
        x = i % 400
        y = (i * 7) % 400
        draw.point([x, y], fill='darkgreen')
    
    return img

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_disease_detection():
    """Test the disease detection API with various test images"""
    
    api_url = "http://127.0.0.1:8004/disease/detect"
    
    test_cases = [
        ("tomato", "blight", "Tomato with Blight Symptoms"),
        ("rice", "rust", "Rice with Rust Disease"),
        ("wheat", "mildew", "Wheat with Powdery Mildew"),
        ("potato", "yellowing", "Potato with Nutrient Deficiency"),
        ("maize", "healthy", "Healthy Maize Plant")
    ]
    
    print("🌾 Testing AgriSense Disease Detection System")
    print("=" * 60)
    
    for crop_type, disease_sim, description in test_cases:
        print(f"\n🔬 Testing: {description}")
        print(f"   Crop: {crop_type} | Simulated: {disease_sim}")
        
        # Create test image
        test_image = create_test_image(disease_sim)
        image_b64 = image_to_base64(test_image)
        
        # Prepare request
        payload = {
            "image_data": image_b64,
            "crop_type": crop_type,
            "analysis_type": "comprehensive"
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   ✅ Status: Success")
                print(f"   🦠 Disease: {result.get('disease', 'Unknown')}")
                print(f"   📊 Confidence: {result.get('confidence', 0):.1f}%")
                print(f"   ⚠️  Severity: {result.get('severity', 'Unknown')}")
                print(f"   🎯 Analysis: {result.get('analysis_method', 'Standard')}")
                
                if result.get('treatment_plan'):
                    treatment = result['treatment_plan']
                    print(f"   💊 Treatment: {treatment.get('immediate_action', 'None specified')}")
                
                if result.get('prevention_plan'):
                    prevention = result['prevention_plan']
                    print(f"   🛡️  Prevention: {prevention.get('primary_prevention', 'Standard care')}")
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   📝 Message: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   🚨 Connection Error: {e}")
        
        print("-" * 40)
    
    print("\n🎯 Test Complete!")
    print("\nTo use the web interface:")
    print("1. Main UI (Static):  http://127.0.0.1:8004/ui")
    print("2. Dev UI (Live):     http://localhost:8080")
    print("3. Debug Page:        http://127.0.0.1:8004/debug")

if __name__ == "__main__":
    test_disease_detection()