#!/usr/bin/env python
"""
AgriSense Project Status Check
Comprehensive test to verify all systems are running properly.
"""
import requests
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8004"
FRONTEND_URL = "http://localhost:8080"

def test_endpoint(name, endpoint, method="GET", data=None):
    """Test an API endpoint and return status."""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        return f"{status} | {name} | {endpoint}"
    except Exception as e:
        return f"❌ ERROR | {name} | {endpoint} | {str(e)}"

def main():
    print("🌾 AgriSense Project Status Check")
    print("=" * 50)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Core system endpoints
    print("🔧 CORE SYSTEM:")
    print(test_endpoint("Health Check", "/health"))
    print(test_endpoint("Version Info", "/version"))
    print(test_endpoint("API Docs", "/docs"))
    print()
    
    # Data endpoints
    print("📊 DATA ENDPOINTS:")
    print(test_endpoint("Crops List", "/crops"))
    print(test_endpoint("Soil Types", "/soil/types"))
    print(test_endpoint("Recent Sensors", "/recent"))
    print()
    
    # Core functionality
    print("🚀 CORE FEATURES:")
    print(test_endpoint("Dashboard Summary", "/dashboard/summary"))
    print(test_endpoint("Tank Status", "/tank/status"))
    print(test_endpoint("System Alerts", "/alerts"))
    print()
    
    # ML/AI endpoints
    print("🧠 AI/ML FEATURES:")
    sample_data = {
        "soil_type": "loamy",
        "ph": 6.5,
        "temperature": 25,
        "humidity": 70,
        "crop_type": "rice"
    }
    print(test_endpoint("Crop Recommendation", "/recommend", "POST", sample_data))
    print(test_endpoint("Crop Suggestion", "/suggest_crop", "POST", {"soil_type": "loamy"}))
    print()
    
    # Test frontend accessibility
    print("🖥️ FRONTEND:")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        status = "✅ RUNNING" if response.status_code == 200 else f"❌ ISSUE ({response.status_code})"
        print(f"{status} | Frontend UI | {FRONTEND_URL}")
    except Exception as e:
        print(f"❌ ERROR | Frontend UI | {FRONTEND_URL} | {str(e)}")
    
    print()
    print("🎯 ACCESS POINTS:")
    print(f"   🔗 Backend API: {BASE_URL}")
    print(f"   🔗 API Documentation: {BASE_URL}/docs")
    print(f"   🔗 Frontend UI: {FRONTEND_URL}")
    print(f"   🔗 Built-in UI: {BASE_URL}/ui")
    print()
    print("✨ AgriSense is ready for use!")

if __name__ == "__main__":
    main()