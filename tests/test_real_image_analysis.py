#!/usr/bin/env python3
"""
Test image analysis endpoints with a real image format
"""

import base64
import io
import requests
from PIL import Image
import json

def create_test_image():
    """Create a simple RGB test image"""
    # Create a 100x100 green image (simulating healthy leaf)
    img = Image.new('RGB', (100, 100), color=(34, 139, 34))  # Forest green
    
    # Add some brown spots (simulating disease)
    for x in range(20, 30):
        for y in range(20, 30):
            img.putpixel((x, y), (139, 69, 19))  # Saddle brown
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def test_disease_detection():
    """Test disease detection endpoint"""
    print("Testing disease detection...")
    
    image_data = create_test_image()
    
    payload = {
        "image_data": image_data,  # No data URL prefix - just base64
        "crop_type": "tomato",
        "field_info": {
            "growth_stage": "flowering"
        }
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8004/disease/detect",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response structure:")
            print(json.dumps(result, indent=2))
            
            # Check if it has the expected structure
            if "primary_disease" in result:
                print("✅ Success: Valid disease detection response")
            else:
                print("❌ Error: Missing expected fields")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_weed_analysis():
    """Test weed analysis endpoint"""
    print("\nTesting weed analysis...")
    
    image_data = create_test_image()
    
    payload = {
        "image_data": image_data,  # No data URL prefix - just base64
        "field_info": {
            "crop_type": "wheat",
            "field_size_acres": 2.5
        }
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8004/weed/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response structure:")
            print(json.dumps(result, indent=2))
            
            # Check if it has the expected structure
            if "weed_types" in result or "total_weeds" in result:
                print("✅ Success: Valid weed analysis response")
            else:
                print("❌ Error: Missing expected fields")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_disease_detection()
    test_weed_analysis()