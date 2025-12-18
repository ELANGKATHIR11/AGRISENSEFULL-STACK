"""
SCOLD VLM Integration Test Suite
=================================

Tests the complete SCOLD VLM integration with AgriSense:
1. SCOLD server availability
2. Disease detection via backend
3. Weed identification via backend
4. Hybrid AI multimodal analysis
"""

import base64
import io
import requests
import time
from pathlib import Path
from PIL import Image, ImageDraw

# Configuration
SCOLD_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8004"

def create_test_image(label: str) -> bytes:
    """Create a test image with label"""
    img = Image.new('RGB', (640, 480), color='green')
    draw = ImageDraw.Draw(img)
    draw.text((250, 220), label, fill='white')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_scold_health():
    """Test 1: SCOLD server health check"""
    print("\n" + "="*60)
    print("Test 1: SCOLD Server Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{SCOLD_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SCOLD server is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Model Loaded: {data.get('model_loaded')}")
            return True
        else:
            print(f"❌ SCOLD server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SCOLD server not accessible: {e}")
        print(f"   Make sure SCOLD is running on port 8001")
        return False

def test_scold_status():
    """Test 2: SCOLD server status"""
    print("\n" + "="*60)
    print("Test 2: SCOLD Server Status")
    print("="*60)
    
    try:
        response = requests.get(f"{SCOLD_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SCOLD status retrieved")
            print(f"   Model Loaded: {data.get('model_loaded')}")
            print(f"   Model Path: {data.get('model_path')}")
            print(f"   Device: {data.get('device')}")
            print(f"   Available Endpoints:")
            for endpoint in data.get('available_endpoints', []):
                print(f"     - {endpoint}")
            return True
        else:
            print(f"❌ Status request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status request error: {e}")
        return False

def test_backend_health():
    """Test 3: Backend health check"""
    print("\n" + "="*60)
    print("Test 3: Backend Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        print(f"   Make sure backend is running on port 8004")
        return False

def test_disease_detection():
    """Test 4: Disease detection with SCOLD"""
    print("\n" + "="*60)
    print("Test 4: Disease Detection (via Backend)")
    print("="*60)
    
    try:
        # Create test image
        image_bytes = create_test_image("Test Tomato Leaf")
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Call backend disease detection endpoint
        payload = {
            "image_data": image_b64,
            "crop_type": "tomato"
        }
        
        print("📤 Sending disease detection request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/disease/detect",
            json=payload,
            timeout=30
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Disease detection completed in {elapsed:.0f}ms")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Analysis Method: {data.get('analysis_method', 'unknown')}")
            print(f"   Detections: {len(data.get('detections', []))}")
            
            if data.get('detections'):
                print(f"   Detected Diseases:")
                for det in data['detections'][:3]:  # Show first 3
                    print(f"     - {det.get('disease_name')}: "
                          f"{det.get('confidence', 0)*100:.1f}% "
                          f"({det.get('severity', 'unknown')})")
            
            if data.get('recommendations'):
                print(f"   Recommendations:")
                for rec in data['recommendations'][:3]:
                    print(f"     - {rec}")
            
            return True
        else:
            print(f"❌ Disease detection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Disease detection error: {e}")
        return False

def test_weed_identification():
    """Test 5: Weed identification with SCOLD"""
    print("\n" + "="*60)
    print("Test 5: Weed Identification (via Backend)")
    print("="*60)
    
    try:
        # Create test image
        image_bytes = create_test_image("Test Field with Weeds")
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Call backend weed detection endpoint
        payload = {
            "image_data": image_b64,
            "crop_type": "wheat"
        }
        
        print("📤 Sending weed identification request...")
        start_time = time.time()
        
        response = requests.post(
            f"{BACKEND_URL}/api/weed/analyze",
            json=payload,
            timeout=30
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Weed identification completed in {elapsed:.0f}ms")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Analysis Method: {data.get('analysis_method', 'unknown')}")
            print(f"   Weeds Detected: {data.get('weed_count', 0)}")
            print(f"   Coverage: {data.get('coverage_percentage', 0):.1f}%")
            
            if data.get('weeds_detected'):
                print(f"   Detected Weeds:")
                for weed in data['weeds_detected'][:3]:  # Show first 3
                    print(f"     - {weed.get('common_name')}: "
                          f"{weed.get('confidence', 0)*100:.1f}% "
                          f"({weed.get('coverage_percent', 0):.1f}% coverage)")
            
            if data.get('recommendations'):
                print(f"   Treatment Options:")
                for rec in data['recommendations'][:3]:
                    print(f"     - {rec}")
            
            return True
        else:
            print(f"❌ Weed identification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Weed identification error: {e}")
        return False

def test_hybrid_ai_status():
    """Test 6: Hybrid AI system status"""
    print("\n" + "="*60)
    print("Test 6: Hybrid AI System Status")
    print("="*60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/hybrid/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hybrid AI status retrieved")
            print(f"   Hybrid AI Available: {data.get('hybrid_ai_available')}")
            print(f"   Phi LLM Available: {data.get('phi_llm_available')}")
            print(f"   SCOLD VLM Available: {data.get('scold_vlm_available')}")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Configuration:")
            config = data.get('config', {})
            print(f"     - SCOLD Endpoint: {config.get('scold_endpoint')}")
            print(f"     - Phi Endpoint: {config.get('phi_endpoint')}")
            print(f"     - Timeout: {config.get('timeout')}s")
            return True
        else:
            print(f"⚠️  Hybrid AI status endpoint not available: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Hybrid AI status error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 SCOLD VLM Integration Test Suite")
    print("="*70)
    print(f"SCOLD URL: {SCOLD_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    
    tests = [
        ("SCOLD Health", test_scold_health),
        ("SCOLD Status", test_scold_status),
        ("Backend Health", test_backend_health),
        ("Disease Detection", test_disease_detection),
        ("Weed Identification", test_weed_identification),
        ("Hybrid AI Status", test_hybrid_ai_status),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    print("="*70)
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
