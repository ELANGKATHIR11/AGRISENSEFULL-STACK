#!/usr/bin/env python3
"""
Quick script to start backend and run tests
"""
import subprocess
import time
import requests
import sys
import os

os.chdir(r"d:\AGRISENSE FULL-STACK\AGRISENSEFULL-STACK")
os.environ['AGRISENSE_DISABLE_ML'] = '1'

# Kill any existing processes on port 8004
print("Cleaning up port 8004...")
subprocess.run(['powershell.exe', '-Command', 
    'Get-NetTCPConnection -LocalPort 8004 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }'],
    capture_output=True)
time.sleep(2)

# Start backend
print("Starting backend uvicorn...")
backend_proc = subprocess.Popen(
    ['.venv\\Scripts\\python.exe', '-m', 'uvicorn', 
     'agrisense_app.backend.main:app', '--host', '0.0.0.0', '--port', '8004', '--log-level', 'error'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for backend to initialize
print("Waiting 15 seconds for backend to initialize...")
time.sleep(15)

# Check health
print("Checking backend health...")
try:
    resp = requests.get('http://localhost:8004/health', timeout=5)
    if resp.status_code == 200:
        print("✅ Backend is healthy!")
    else:
        print(f"⚠️  Backend returned status {resp.status_code}")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    backend_proc.terminate()
    sys.exit(1)

# Run E2E tests
print("\nRunning comprehensive E2E tests...")
print("=" * 70)
try:
    result = subprocess.run(
        ['.venv\\Scripts\\python.exe', '-X', 'utf8', 'comprehensive_e2e_test.py'],
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    )
    exit_code = result.returncode
except Exception as e:
    print(f"Test execution failed: {e}")
    exit_code = 1

# Stop backend
print("=" * 70)
print("Stopping backend...")
backend_proc.terminate()
time.sleep(2)
backend_proc.kill()

print("Done!")
sys.exit(exit_code)
