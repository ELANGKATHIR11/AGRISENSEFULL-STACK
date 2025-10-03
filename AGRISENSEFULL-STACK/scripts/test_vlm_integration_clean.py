#!/usr/bin/env python3
"""
Test script for VLM integration in AgriSense
Tests the Vision Language Model endpoints and functionality
"""

import sys
import os
import json
import base64
import requests
from pathlib import Path
from PIL import Image
import io
import numpy as np

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "agrisense_app" / "backend"
sys.path.insert(0, str(backend_dir))

def create_test_image():
    """Create a simple test image for analysis"""
    # Create a simple green field image with some brown spots
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    
    # Green background (healthy crop)
    img[:, :, 1] = 120  # Green channel
    img[:, :, 0] = 50   # Red channel
    img[:, :, 2] = 30   # Blue channel
    
    # Add some brown spots (potential disease/weed areas)
    for i in range(5):
        x, y = np.random.randint(20, 200, 2)
        size = np.random.randint(10, 30)
        img[y:y+size, x:x+size, 0] = 139  # Brown color
        img[y:y+size, x:x+size, 1] = 69
        img[y:y+size, x:x+size, 2] = 19
    
    # Convert to PIL Image
    pil_img = Image.fromarray(img)
    
    # Convert to base64
    buffer = io.BytesIO()
    pil_img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_base64

def test_vlm_engine_import():
    """Test if VLM engine can be imported"""
    print("Testing VLM engine import...")
    try:
        from vlm_engine import get_vlm_engine, analyze_with_vlm
        engine = get_vlm_engine()
        print("[SUCCESS] VLM engine imported successfully")
        print(f"   Knowledge base loaded: {len(engine.knowledge_base)} categories")
        return True
    except Exception as e:
        print(f"[ERROR] VLM engine import failed: {e}")
        return False

def test_vlm_analysis():
    """Test VLM analysis functionality"""
    print("\nTesting VLM analysis...")
    try:
        from vlm_engine import analyze_with_vlm
        
        # Create test image
        test_image = create_test_image()
        
        # Test disease analysis
        print("  Testing disease analysis...")
        disease_result = analyze_with_vlm(
            image_input=test_image,
            analysis_type='disease',
            crop_type='tomato'
        )
        
        print(f"  [SUCCESS] Disease analysis completed")
        print(f"     Confidence: {disease_result.get('confidence_score', 0):.2f}")
        print(f"     Recommendations: {len(disease_result.get('recommendations', {}).get('immediate_actions', []))}")
        
        # Test weed analysis
        print("  Testing weed analysis...")
        weed_result = analyze_with_vlm(
            image_input=test_image,
            analysis_type='weed',
            crop_type='corn'
        )
        
        print(f"  [SUCCESS] Weed analysis completed")
        print(f"     Confidence: {weed_result.get('confidence_score', 0):.2f}")
        print(f"     Recommendations: {len(weed_result.get('recommendations', {}).get('immediate_actions', []))}")
        
        return True
    except Exception as e:
        print(f"  [ERROR] VLM analysis failed: {e}")
        return False

def test_api_endpoints(base_url="http://localhost:8004"):
    """Test VLM API endpoints"""
    print(f"\nTesting VLM API endpoints at {base_url}...")
    
    # Create test payload
    test_image = create_test_image()
    payload = {
        "image_data": test_image,
        "crop_type": "tomato",
        "field_info": {
            "crop_type": "tomato",
            "field_size_acres": 2.5
        }
    }
    
    # Test VLM status endpoint
    try:
        print("  Testing VLM status endpoint...")
        response = requests.get(f"{base_url}/api/vlm/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"  [SUCCESS] VLM Status: {status_data.get('status', 'unknown')}")
            print(f"     Available: {status_data.get('vlm_available', False)}")
            print(f"     Capabilities: {len(status_data.get('capabilities', []))}")
        else:
            print(f"  [ERROR] Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"  [ERROR] Status endpoint error: {e}")
    
    # Test disease detection endpoint
    try:
        print("  Testing disease detection endpoint...")
        response = requests.post(
            f"{base_url}/api/disease/detect",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  [SUCCESS] Disease detection successful")
            print(f"     Disease: {result.get('primary_disease', 'unknown')}")
            print(f"     Confidence: {result.get('confidence', 0):.2f}")
            if 'vlm_analysis' in result:
                print(f"     VLM Enhanced: {result['vlm_analysis'].get('knowledge_matches', 0)} matches")
        else:
            print(f"  [ERROR] Disease detection failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] Disease detection error: {e}")
    
    # Test weed analysis endpoint
    try:
        print("  Testing weed analysis endpoint...")
        response = requests.post(
            f"{base_url}/api/weed/analyze",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  [SUCCESS] Weed analysis successful")
            print(f"     Coverage: {result.get('weed_coverage_percentage', 0):.1f}%")
            print(f"     Pressure: {result.get('weed_pressure', 'unknown')}")
            if 'vlm_analysis' in result:
                print(f"     VLM Enhanced: {result['vlm_analysis'].get('knowledge_matches', 0)} matches")
        else:
            print(f"  [ERROR] Weed analysis failed: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] Weed analysis error: {e}")

def test_knowledge_base():
    """Test knowledge base functionality"""
    print("\nTesting knowledge base...")
    try:
        from vlm_engine import get_vlm_engine
        
        engine = get_vlm_engine()
        
        # Test knowledge base search
        disease_results = engine.search_knowledge_base("leaf spot", "disease")
        weed_results = engine.search_knowledge_base("broadleaf", "weed")
        
        print(f"  [SUCCESS] Knowledge base search working")
        print(f"     Disease results: {len(disease_results)}")
        print(f"     Weed results: {len(weed_results)}")
        
        # Test knowledge base categories
        kb = engine.knowledge_base
        print(f"  Knowledge base categories:")
        for category, data in kb.items():
            if isinstance(data, dict):
                print(f"     {category}: {len(data)} items")
            elif isinstance(data, list):
                print(f"     {category}: {len(data)} items")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Knowledge base test failed: {e}")
        return False

def main():
    """Run all VLM integration tests"""
    print("AgriSense VLM Integration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: VLM Engine Import
    results.append(test_vlm_engine_import())
    
    # Test 2: VLM Analysis
    results.append(test_vlm_analysis())
    
    # Test 3: Knowledge Base
    results.append(test_knowledge_base())
    
    # Test 4: API Endpoints (if server is running)
    print("\nChecking if server is running...")
    try:
        response = requests.get("http://localhost:8004/health", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] Server is running, testing API endpoints...")
            test_api_endpoints()
        else:
            print("[WARNING] Server not responding properly, skipping API tests")
    except Exception as e:
        print("[WARNING] Server not running, skipping API tests")
        print("   Start the server with: uvicorn main:app --host 0.0.0.0 --port 8004")
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total} core tests")
    
    if passed == total:
        print("[SUCCESS] All core VLM tests passed!")
        print("\nVLM integration is ready for use!")
        print("\nKey Features Available:")
        print("   - Enhanced disease detection with knowledge base")
        print("   - Advanced weed analysis with visual features")
        print("   - Agricultural knowledge integration")
        print("   - Comprehensive plant health assessment")
    else:
        print("[ERROR] Some tests failed. Check the output above for details.")
        print("\nTroubleshooting:")
        print("   - Ensure all VLM dependencies are installed")
        print("   - Check that the knowledge base files are present")
        print("   - Verify PyTorch and transformers are working")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
