"""
AgriSense Project Cleanup Script
Removes temporary files and performs final cleanup
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Perform final project cleanup"""
    project_root = Path(__file__).parent
    
    print("🧹 Starting AgriSense project cleanup...")
    
    # Remove temp_cleanup directory if it exists
    temp_cleanup = project_root / "temp_cleanup"
    if temp_cleanup.exists():
        print(f"🗑️  Removing temporary files from {temp_cleanup}")
        shutil.rmtree(temp_cleanup)
        print("✅ Temporary files removed")
    
    # Remove __pycache__ directories
    for pycache in project_root.rglob("__pycache__"):
        print(f"🗑️  Removing cache: {pycache}")
        shutil.rmtree(pycache)
    
    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        print(f"🗑️  Removing compiled Python file: {pyc_file}")
        pyc_file.unlink()
    
    # Remove empty ml_models directory in backend if it exists and is empty
    backend_ml_models = project_root / "agrisense_app" / "backend" / "ml_models"
    if backend_ml_models.exists() and not any(backend_ml_models.iterdir()):
        print(f"🗑️  Removing empty directory: {backend_ml_models}")
        backend_ml_models.rmdir()
    
    # Clean up node_modules cache (optional - keep for faster rebuilds)
    # frontend_node_modules = project_root / "agrisense_app" / "frontend" / "farm-fortune-frontend-main" / "node_modules"
    # if frontend_node_modules.exists():
    #     print(f"🗑️  Removing node_modules: {frontend_node_modules}")
    #     shutil.rmtree(frontend_node_modules)
    
    print("\\n✨ Project cleanup completed!")
    print("\\n📁 Current project structure is now clean and organized:")
    print("   ├── agrisense_app/          # Main application")
    print("   ├── AGRISENSE_IoT/          # IoT components")
    print("   ├── ml_models/              # Organized ML models")
    print("   ├── datasets/               # Training data")
    print("   ├── tests/                  # Test files")
    print("   ├── config/                 # Configuration")
    print("   ├── documentation/          # Documentation")
    print("   ├── scripts/                # Utility scripts")
    print("   └── dev_launcher.py         # Development launcher")

if __name__ == "__main__":
    cleanup_project()