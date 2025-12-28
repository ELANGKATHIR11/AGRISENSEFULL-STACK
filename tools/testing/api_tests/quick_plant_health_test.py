#!/usr/bin/env python3
"""
Quick test script to verify plant health system integration
"""

import os
import sys
import time
import subprocess
import requests
import signal
import json

def start_server():
    """Start the FastAPI server"""
    os.environ['AGRISENSE_DISABLE_ML'] = '0'
    
    cmd = [
        sys.executable, 
        "-m", "uvicorn", 
        "agrisense_app.backend.main:app", 
        "--reload", 
        "--port", "8004"
    ]
    
    print("🚀 Starting FastAPI server...")
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    return process

def wait_for_server(timeout=30):
    """Wait for server to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://127.0.0.1:8004/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("⏳ Waiting for server...")
        time.sleep(2)
    
    print("❌ Server did not start within timeout")
    return False

def test_plant_health_endpoints():
    """Test the plant health endpoints"""
    base_url = "http://127.0.0.1:8004"
    
    # Test health status
    print("\n🔍 Testing /health/status endpoint...")
    try:
        response = requests.get(f"{base_url}/health/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health Status Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test basic health endpoint
    print("\n🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Basic Health Response:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🧪 AgriSense Plant Health Integration Test")
    print("=" * 50)
    
    # Start server
    server_process = start_server()
    
    try:
        # Wait for server to be ready
        if wait_for_server():
            # Test endpoints
            test_plant_health_endpoints()
        else:
            print("❌ Server failed to start properly")
    
    finally:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        
        # Wait a bit for graceful shutdown
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        
        print("✅ Test completed!")

if __name__ == "__main__":
    main()