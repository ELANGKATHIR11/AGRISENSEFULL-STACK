#!/usr/bin/env python3
"""
Unified AgriSense Server Startup Script
Builds frontend and starts backend server on a single port
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == "win32":
    import locale
    import codecs
    # Safely set the preferred encoding for stdout/stderr across Python versions.
    preferred_enc = locale.getpreferredencoding()
    try:
        # Prefer reconfigure() when available (Python 3.7+). Use a try/except
        # rather than hasattr checks so static analyzers don't complain.
        try:
            sys.stdout.reconfigure(encoding=preferred_enc)  # type: ignore[attr-defined]
        except Exception:
            # Fallback: try to wrap the binary buffer if available, otherwise try detach().
            try:
                binary_stdout = getattr(sys.stdout, "buffer", None)
                if binary_stdout is None:
                    try:
                        binary_stdout = sys.stdout.detach()  # type: ignore[attr-defined]
                    except Exception:
                        binary_stdout = None
                if binary_stdout is not None:
                    sys.stdout = codecs.getwriter(preferred_enc)(binary_stdout)
            except Exception:
                # If no binary stream could be obtained, leave sys.stdout as-is.
                pass

        try:
            sys.stderr.reconfigure(encoding=preferred_enc)  # type: ignore[attr-defined]
        except Exception:
            try:
                binary_stderr = getattr(sys.stderr, "buffer", None)
                if binary_stderr is None:
                    try:
                        binary_stderr = sys.stderr.detach()  # type: ignore[attr-defined]
                    except Exception:
                        binary_stderr = None
                if binary_stderr is not None:
                    sys.stderr = codecs.getwriter(preferred_enc)(binary_stderr)
            except Exception:
                pass
    except Exception:
        # Be defensive: if any adjustment fails, continue without crashing.
        pass

def print_status(message: str, status: str = "INFO"):
    """Print formatted status message"""
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, colors['INFO'])}[{status}] {message}{colors['RESET']}")

def check_node_and_npm():
    """Check if Node.js and npm are available"""
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_frontend():
    """Build the frontend for production"""
    frontend_dir = Path("agrisense_app/frontend/farm-fortune-frontend-main")
    
    if not frontend_dir.exists():
        print_status("Frontend directory not found", "ERROR")
        return False
    
    print_status("Building frontend for production...", "INFO")
    
    # Change to frontend directory
    original_cwd = os.getcwd()
    os.chdir(frontend_dir)
    
    try:
        # Check if node_modules exists, if not install dependencies
        if not Path("node_modules").exists():
            print_status("Installing frontend dependencies...", "INFO")
            result = subprocess.run(["npm", "install"], check=True, capture_output=True, text=True)
            print_status("Dependencies installed successfully", "SUCCESS")
        
        # Build the frontend
        print_status("Building frontend assets...", "INFO")
        result = subprocess.run(["npm", "run", "build"], check=True, capture_output=True, text=True)
        print_status("Frontend built successfully", "SUCCESS")
        
        # Verify dist directory exists
        if Path("dist").exists():
            print_status("Frontend build artifacts created in dist/", "SUCCESS")
            return True
        else:
            print_status("Frontend build completed but dist/ not found", "WARNING")
            return False
            
    except subprocess.CalledProcessError as e:
        print_status(f"Frontend build failed: {e}", "ERROR")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False
    finally:
        os.chdir(original_cwd)

def start_backend_server(port: int = 8004, reload: bool = False):
    """Start the FastAPI backend server"""
    print_status(f"Starting AgriSense backend server on port {port}...", "INFO")
    
    # Set environment variables
    env = os.environ.copy()
    # Enable ML features for full functionality
    if "AGRISENSE_DISABLE_ML" in env:
        del env["AGRISENSE_DISABLE_ML"]
    
    # Build uvicorn command
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "agrisense_app.backend.main:app", 
        "--port", str(port),
        "--host", "0.0.0.0"
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        print_status("Backend server starting...", "INFO")
        print_status(f"Access your application at: http://localhost:{port}/ui", "SUCCESS")
        print_status(f"API documentation at: http://localhost:{port}/docs", "INFO")
        print_status("Press Ctrl+C to stop the server", "INFO")
        
        # Start the server (this will block)
        subprocess.run(cmd, env=env, check=True)
        
    except KeyboardInterrupt:
        print_status("Server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        print_status(f"Server failed to start: {e}", "ERROR")
        return False
    
    return True

def check_backend_health(port: int = 8004, timeout: int = 30):
    """Check if backend is healthy"""
    import requests
    import time
    
    url = f"http://localhost:{port}/health"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    
    return False

def main():
    """Main startup function"""
    print_status("AgriSense Unified Server Startup", "SUCCESS")
    print_status("=" * 50, "INFO")
    
    # Check if we're in the right directory
    if not Path("agrisense_app").exists():
        print_status("Please run this script from the project root directory", "ERROR")
        sys.exit(1)
    
    # Check Node.js availability
    if not check_node_and_npm():
        print_status("Node.js/npm not found. Frontend will use existing build if available.", "WARNING")
        frontend_built = Path("agrisense_app/frontend/farm-fortune-frontend-main/dist").exists()
    else:
        # Build frontend
        frontend_built = build_frontend()
    
    if not frontend_built:
        print_status("Frontend build not available. API-only mode.", "WARNING")
    else:
        print_status("Frontend ready - will be served at /ui", "SUCCESS")
    
    # Determine if we should enable reload (development mode)
    reload_mode = "--reload" in sys.argv or "--dev" in sys.argv
    
    if reload_mode:
        print_status("Development mode enabled (--reload)", "INFO")
    
    # Start backend server
    port = 8004
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port")
            port = int(sys.argv[port_idx + 1])
        except (IndexError, ValueError):
            print_status("Invalid port specified, using default 8004", "WARNING")
    
    print_status(f"Starting unified server on port {port}", "INFO")
    print_status("Frontend and Backend will be available at:", "SUCCESS")
    print_status(f"  Web Interface: http://localhost:{port}/ui", "SUCCESS")
    print_status(f"  API Docs: http://localhost:{port}/docs", "SUCCESS")
    print_status(f"  Debug Page: http://localhost:{port}/debug", "SUCCESS")
    print_status(f"  Health Check: http://localhost:{port}/health", "SUCCESS")
    print_status("", "INFO")
    
    # Start the server
    success = start_backend_server(port, reload_mode)
    
    if success:
        print_status("Server stopped successfully", "SUCCESS")
    else:
        print_status("Server startup failed", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()