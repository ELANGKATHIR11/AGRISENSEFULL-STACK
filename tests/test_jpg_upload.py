#!/usr/bin/env python3
"""
Test script to verify JPG image upload and disease detection workflow
"""
import base64
import requests
import json
import os
from pathlib import Path

def test_jpg_upload():
    """Test uploading a JPG image and getting disease detection results"""
    
    # Test image path
    test_image_path = Path("tools/data-processing/agricultural_ml_datasets/disease_images/black_rot_bean_moderate_1.jpg")
    
    if not test_image_path.exists():
        print("❌ Test image not found!")
        return False
    
    print(f"📸 Testing with image: {test_image_path}")
    print(f"📏 Image size: {test_image_path.stat().st_size / 1024:.1f} KB")
    
    # Read and encode image
    with open(test_image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Prepare payload (same as frontend)
    payload = {
        "image_data": image_data,
        "crop_type": "bean",
        "field_info": {
            "growth_stage": "mature"
        }
    }
    
    print("🚀 Sending request to API...")
    
    try:
        # Send request to API
        response = requests.post(
            'http://127.0.0.1:8004/api/disease/detect',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ SUCCESS! Disease detection results:")
            print(f"🦠 Disease: {result['disease']}")
            print(f"🎯 Confidence: {result['confidence']:.2f}%")
            print(f"📊 Severity: {result['severity']}")
            print(f"🌱 Crop: {result['crop_type']}")
            print(f"🔬 Analysis Method: {result['analysis_method']}")
            print(f"📅 Timestamp: {result['timestamp']}")
            
            if result.get('treatment_plan'):
                print("\n💊 Treatment Plan:")
                for category, treatments in result['treatment_plan'].items():
                    if treatments:
                        print(f"  {category.title()}: {treatments}")
            
            print("\n🎉 JPG image upload and analysis working perfectly!")
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_multiple_formats():
    """Test different image formats"""
    
    # Look for different image formats
    image_dir = Path("tools/data-processing/agricultural_ml_datasets/disease_images/")
    
    formats_to_test = ['.jpg', '.jpeg', '.png']
    found_formats = []
    
    for fmt in formats_to_test:
        image_files = list(image_dir.glob(f"*{fmt}"))
        if image_files:
            found_formats.append((fmt, image_files[0]))
    
    print(f"\n🧪 Testing {len(found_formats)} image formats...")
    
    success_count = 0
    for fmt, image_path in found_formats:
        print(f"\n📸 Testing {fmt.upper()} format: {image_path.name}")
        
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "image_data": image_data,
                "crop_type": "tomato"
            }
            
            response = requests.post(
                'http://127.0.0.1:8004/api/disease/detect',
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {fmt.upper()}: {result['disease']} ({result['confidence']:.1f}%)")
                success_count += 1
            else:
                print(f"  ❌ {fmt.upper()}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"  ❌ {fmt.upper()}: Error - {e}")
    
    print(f"\n📊 Results: {success_count}/{len(found_formats)} formats working")
    return success_count == len(found_formats)

if __name__ == "__main__":
    print("🔬 AgriSense JPG Upload Test")
    print("=" * 40)
    
    # Test primary JPG functionality
    jpg_success = test_jpg_upload()
    
    # Test multiple formats
    formats_success = test_multiple_formats()
    
    print("\n" + "=" * 40)
    if jpg_success and formats_success:
        print("🎉 ALL TESTS PASSED! JPG upload and disease detection working!")
    elif jpg_success:
        print("✅ JPG upload working, some other formats may have issues")
    else:
        print("❌ JPG upload test failed")