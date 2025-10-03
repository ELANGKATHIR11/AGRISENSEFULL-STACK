#!/usr/bin/env python3
"""
Simple Disease Detection Test
Quick test of the comprehensive disease detection system
"""

import requests
import base64
import io
from PIL import Image, ImageDraw

def simple_test():
    # Create a simple test image
    img = Image.new('RGB', (200, 200), (50, 120, 50))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill=(80, 60, 20))  # Brown spot
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    # Test disease detection
    payload = {
        'image_data': img_b64,
        'crop_type': 'Cotton',
        'environmental_data': {'temperature': 25, 'humidity': 70}
    }

    print("🧪 Testing comprehensive disease detection...")
    response = requests.post('http://127.0.0.1:8004/disease/detect', json=payload)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'✅ Disease Detection Success!')
        print(f'  Disease: {result.get("disease_type", "unknown")}')
        print(f'  Confidence: {result.get("confidence", 0):.1%}')
        print(f'  Crop: {result.get("crop_type", "unknown")}')
        print(f'  Severity: {result.get("severity", "unknown")}')
        print(f'  Analysis Method: {result.get("analysis_method", "unknown")}')
        
        # Check if comprehensive detector was used
        if result.get("model_info", {}).get("type") == "Comprehensive Disease Detector":
            print(f'  ✅ Using Comprehensive Disease Detector!')
        
        # Show treatment recommendations
        treatment = result.get("treatment", {})
        if treatment:
            print(f'  💊 Treatment Available: {len(treatment)} categories')
            if treatment.get("immediate"):
                print(f'    Immediate: {treatment["immediate"][0]}')
    else:
        print(f'❌ Error: {response.text}')

    # Test multiple crops
    crops_to_test = ["Rice", "Wheat", "Tomato", "Potato", "Maize"]
    print(f"\n🌱 Testing multiple crops:")
    
    for crop in crops_to_test:
        payload['crop_type'] = crop
        response = requests.post('http://127.0.0.1:8004/disease/detect', json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f'  {crop}: {result.get("disease_type", "unknown")} ({result.get("confidence", 0):.1%})')
        else:
            print(f'  {crop}: ERROR')

if __name__ == "__main__":
    simple_test()