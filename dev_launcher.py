"""
AgriSense Unified Development Launcher
Starts all components of the AgriSense platform in development mode
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "agrisense_app" / "backend"
FRONTEND_DIR = PROJECT_ROOT / "agrisense_app" / "frontend" / "farm-fortune-frontend-main"
ARDUINO_BRIDGE = PROJECT_ROOT / "AGRISENSE_IoT" / "arduino_nano_firmware" / "unified_arduino_bridge.py"

def run_command(cmd, cwd=None, env_vars=None):
    """Run a command in a subprocess"""
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return process
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return None

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting AgriSense Backend...")
    
    # Set environment variables for development
    env_vars = {
        "AGRISENSE_DISABLE_ML": "0",  # Enable ML for development
        "AGRISENSE_ADMIN_TOKEN": "dev-admin-token-123",
        "AGRISENSE_BACKEND_URL": "http://127.0.0.1:8004"
    }
    
    # Activate virtual environment and start uvicorn
    if os.name == 'nt':  # Windows
        venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:  # Unix-like
        venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    
    cmd = f'"{venv_python}" -m uvicorn main:app --reload --host 127.0.0.1 --port 8004'
    return run_command(cmd, cwd=BACKEND_DIR, env_vars=env_vars)

def start_frontend():
    """Start the React frontend"""
    print("🎨 Starting AgriSense Frontend...")
    
    # Check if node_modules exists
    if not (FRONTEND_DIR / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        install_process = run_command("npm install", cwd=FRONTEND_DIR)
        if install_process:
            install_process.wait()
    
    cmd = "npm run dev"
    return run_command(cmd, cwd=FRONTEND_DIR)

def start_arduino_bridge():
    """Start the Arduino bridge (optional)"""
    print("🔌 Starting Arduino Bridge...")
    
    # Check if Arduino bridge file exists
    if not ARDUINO_BRIDGE.exists():
        print("⚠️  Arduino bridge not found. Skipping Arduino integration.")
        return None
    
    # Set environment variables for Arduino
    env_vars = {
        "ARDUINO_PORT": "COM3",
        "ARDUINO_BAUD_RATE": "9600",
        "AGRISENSE_BACKEND_URL": "http://127.0.0.1:8004",
        "ARDUINO_DEVICE_ID": "ARDUINO_NANO_DEV_01"
    }
    
    if os.name == 'nt':  # Windows
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:  # Unix-like
        venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    
    cmd = f'"{venv_python}" "{ARDUINO_BRIDGE}"'
    return run_command(cmd, env_vars=env_vars)

def check_requirements():
    """Check if required dependencies are installed"""
    print("🔍 Checking requirements...")
    
    # Check Python
    try:
        python_version = sys.version_info
        if python_version < (3, 9):
            print("❌ Python 3.9+ required")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}")
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except:
        print("❌ Node.js not found")
        return False
    
    # Check virtual environment
    if os.name == 'nt':
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run: python -m venv .venv")
        return False
    
    print("✅ Virtual environment found")
    return True

def main():
    """Main launcher function"""
    print("🌱 AgriSense Development Launcher")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🚀 Starting AgriSense components...")
    
    processes = []
    
    # Start backend
    backend_process = start_backend()
    if backend_process:
        processes.append(("Backend", backend_process))
        time.sleep(3)  # Give backend time to start
    
    # Start frontend
    frontend_process = start_frontend()
    if frontend_process:
        processes.append(("Frontend", frontend_process))
        time.sleep(2)  # Give frontend time to start
    
    # Start Arduino bridge (optional)
    arduino_process = start_arduino_bridge()
    if arduino_process:
        processes.append(("Arduino Bridge", arduino_process))
    
    if not processes:
        print("❌ No processes started successfully")
        sys.exit(1)
    
    print("\\n🎉 AgriSense is starting up!")
    print("=" * 50)
    print("🌐 Backend API: http://127.0.0.1:8004")
    print("🎨 Frontend UI: http://127.0.0.1:5173")
    print("📚 API Docs: http://127.0.0.1:8004/docs")
    print("=" * 50)
    print("\\nPress Ctrl+C to stop all services")
    
    try:
        # Monitor processes
        while True:
            time.sleep(1)
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\\n⚠️  {name} process has stopped")
                    # Optionally restart or handle the stopped process
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down AgriSense...")
        
        # Terminate all processes
        for name, process in processes:
            try:
                process.terminate()
                print(f"✅ Stopped {name}")
            except:
                try:
                    process.kill()
                    print(f"🔥 Force stopped {name}")
                except:
                    print(f"❌ Could not stop {name}")
        
        print("\\n👋 AgriSense development session ended")

if __name__ == "__main__":
    main()