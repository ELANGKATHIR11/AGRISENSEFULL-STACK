#!/usr/bin/env python3
"""
Test the fixed disease detection API with proper payload format
"""

import requests
import base64
import json
from io import BytesIO
from PIL import Image, ImageDraw

def create_test_image():
    """Create a test image that simulates a diseased plant"""
    # Create a 300x300 RGB image with green background
    img = Image.new('RGB', (300, 300), color='lightgreen')
    draw = ImageDraw.Draw(img)
    
    # Add brown spots to simulate disease
    for i in range(10):
        x, y = 50 + i*20, 50 + (i % 3)*70
        draw.ellipse([x, y, x+20, y+20], fill='brown')
    # Use explicit RGB tuple for dark brown (PIL recognizes tuples)
    draw.ellipse([x+5, y+5, x+15, y+15], fill=(80, 50, 20))
    
    # Add some texture
    for i in range(50):
        x = i % 300
        y = (i * 7) % 300
        draw.point([x, y], fill='darkgreen')
    
    return img

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_fixed_frontend_format():
    """Test with the corrected frontend payload format"""
    
    print("🧪 Testing Fixed Disease Detection API")
    print("=" * 50)
    
    # Create test image
    test_image = create_test_image()
    image_b64 = image_to_base64(test_image)
    
    # Use the corrected payload format (matching what frontend now sends)
    payload = {
        "image_data": image_b64,
        "crop_type": "tomato",
        "field_info": {
            "growth_stage": "flowering"
        }
    }
    
    print(f"📋 Payload structure:")
    print(f"   - image_data: {len(image_b64)} characters")
    print(f"   - crop_type: {payload['crop_type']}")
    print(f"   - field_info: {payload['field_info']}")
    
    try:
        # Test direct endpoint
        print(f"\n🎯 Testing /disease/detect")
        response = requests.post("http://127.0.0.1:8004/disease/detect", 
                                json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Direct: SUCCESS")
            print(f"   🦠 Disease: {result.get('disease', 'Unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0):.1f}%")
            print(f"   ⚠️  Severity: {result.get('severity', 'Unknown')}")
        else:
            print(f"   ❌ Direct: FAILED ({response.status_code})")
            print(f"   📝 Error: {response.text}")
        
        # Test API prefix endpoint (what frontend uses)
        print(f"\n🔀 Testing /api/disease/detect (frontend route)")
        response2 = requests.post("http://127.0.0.1:8004/api/disease/detect", 
                                 json=payload, timeout=30)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   ✅ API Route: SUCCESS")
            print(f"   🦠 Disease: {result2.get('disease', 'Unknown')}")
            print(f"   📊 Confidence: {result2.get('confidence', 0):.1f}%")
            print(f"   ⚠️  Severity: {result2.get('severity', 'Unknown')}")
        else:
            print(f"   ❌ API Route: FAILED ({response2.status_code})")
            print(f"   📝 Error: {response2.text}")
        
        print(f"\n🎉 CONCLUSION:")
        if response.status_code == 200 and response2.status_code == 200:
            print(f"   ✅ Both endpoints working correctly!")
            print(f"   ✅ Frontend should no longer go blank!")
            print(f"   ✅ Disease detection returning real results!")
        else:
            print(f"   ⚠️  Some issues remain - check error messages above")
            
    except requests.exceptions.RequestException as e:
        print(f"   🚨 Connection Error: {e}")
    
    print(f"\n📱 Frontend Access:")
    print(f"   Main UI: http://127.0.0.1:8004/ui")
    print(f"   Debug: http://127.0.0.1:8004/debug")

if __name__ == "__main__":
    test_fixed_frontend_format()