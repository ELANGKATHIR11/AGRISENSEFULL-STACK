"""
AgriSense Project Cleanup and Organization Script
Automatically cleans, organizes, and optimizes the entire full-stack project.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# Base paths
BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent

class ProjectCleaner:
    def __init__(self):
        self.deleted_files = []
        self.moved_files = []
        self.errors = []
        
    def log_action(self, action, path, destination=None):
        """Log cleanup actions"""
        if action == "deleted":
            self.deleted_files.append(str(path))
        elif action == "moved":
            self.moved_files.append(f"{path} -> {destination}")
        elif action == "error":
            self.errors.append(f"{path}: {destination}")
    
    def remove_pycache(self):
        """Remove all __pycache__ directories and .pyc files"""
        print("🗑️  Removing __pycache__ directories and .pyc files...")
        count = 0
        
        for root, dirs, files in os.walk(BASE_DIR):
            # Skip virtual environments
            if '.venv' in root or 'node_modules' in root:
                continue
                
            # Remove __pycache__ directories
            if '__pycache__' in dirs:
                pycache_path = Path(root) / '__pycache__'
                try:
                    shutil.rmtree(pycache_path)
                    self.log_action("deleted", pycache_path)
                    count += 1
                except Exception as e:
                    self.log_action("error", pycache_path, str(e))
            
            # Remove .pyc files
            for file in files:
                if file.endswith('.pyc'):
                    file_path = Path(root) / file
                    try:
                        file_path.unlink()
                        self.log_action("deleted", file_path)
                        count += 1
                    except Exception as e:
                        self.log_action("error", file_path, str(e))
        
        print(f"   ✅ Removed {count} cache files/directories")
    
    def remove_temp_files(self):
        """Remove temporary test files and outputs"""
        print("🗑️  Removing temporary and test output files...")
        
        temp_patterns = [
            'tmp_*.py',
            'pytest-*.txt',
            '*_test_results_*.json',
            'treatment_validation_results_*.json',
            '*.log',
            'tmp_*.html',
        ]
        
        count = 0
        for pattern in temp_patterns:
            for file_path in BASE_DIR.rglob(pattern):
                # Skip files in documentation/reports
                if 'documentation' in str(file_path) and 'reports' in str(file_path):
                    continue
                # Skip files in virtual environments
                if '.venv' in str(file_path) or 'node_modules' in str(file_path):
                    continue
                    
                try:
                    file_path.unlink()
                    self.log_action("deleted", file_path)
                    count += 1
                    print(f"   🗑️  Deleted: {file_path.name}")
                except Exception as e:
                    self.log_action("error", file_path, str(e))
        
        print(f"   ✅ Removed {count} temporary files")
    
    def organize_documentation(self):
        """Organize all documentation files into proper subdirectories"""
        print("📚 Organizing documentation files...")
        
        # Create documentation structure
        doc_structure = {
            'guides': ['DEPLOYMENT_GUIDE.md', 'TESTING_README.md', 
                      'CHATBOT_TESTING_GUIDE.md', 'FRONTEND_TESTING_SETUP.md',
                      'VLM_QUICK_START.md'],
            'summaries': ['PROJECT_BLUEPRINT_UPDATED.md', 'PROJECT_STATUS_FINAL.md',
                         'PROJECT_INTEGRATION_SUMMARY.md', 'MULTILANGUAGE_IMPLEMENTATION_SUMMARY.md',
                         'VLM_IMPLEMENTATION_SUMMARY.md', 'VLM_INTEGRATION_SUMMARY.md',
                         'COMPREHENSIVE_DISEASE_DETECTION_SUMMARY.md', 'CLEANUP_SUMMARY.md',
                         'UPGRADE_SUMMARY.md'],
            'implementation': ['CONVERSATIONAL_CHATBOT_IMPLEMENTATION.md',
                             'CONVERSATIONAL_CHATBOT_COMPLETE.md'],
            'architecture': ['AGRISENSE_BLUEPRINT.md', 'PROBLEM_RESOLUTION.md'],
            'ai_agent': ['AI_AGENT_QUICK_REFERENCE.md', 'AI_AGENT_UPGRADE_SUMMARY.md'],
        }
        
        doc_dir = BASE_DIR / 'documentation'
        count = 0
        
        for category, files in doc_structure.items():
            category_dir = doc_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for filename in files:
                source = BASE_DIR / filename
                if source.exists():
                    destination = category_dir / filename
                    try:
                        shutil.move(str(source), str(destination))
                        self.log_action("moved", source, destination)
                        count += 1
                        print(f"   📄 Moved: {filename} -> documentation/{category}/")
                    except Exception as e:
                        self.log_action("error", source, str(e))
        
        print(f"   ✅ Organized {count} documentation files")
    
    def clean_root_directory(self):
        """Clean up root directory clutter"""
        print("🧹 Cleaning root directory...")
        
        # Remove temporary files from root
        root_temp_files = [
            ROOT_DIR / 'tmp_import_check.py',
            ROOT_DIR / 'tmp_fetch_assets.py',
            ROOT_DIR / 'AGRI SENSE_TMP_import_vlm.py',
            ROOT_DIR / 'AGRI_SENSE_fetch_ui.py',
        ]
        
        count = 0
        for file_path in root_temp_files:
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.log_action("deleted", file_path)
                    count += 1
                    print(f"   🗑️  Deleted: {file_path.name}")
                except Exception as e:
                    self.log_action("error", file_path, str(e))
        
        print(f"   ✅ Cleaned {count} files from root")
    
    def consolidate_duplicate_dirs(self):
        """Check for duplicate backend directory and provide guidance"""
        print("🔍 Checking for duplicate directories...")
        
        backend1 = BASE_DIR / 'backend'
        backend2 = BASE_DIR / 'agrisense_app' / 'backend'
        
        if backend1.exists() and backend2.exists():
            print("   ⚠️  WARNING: Found duplicate backend directories:")
            print(f"      - {backend1}")
            print(f"      - {backend2}")
            print("   ℹ️  Keeping agrisense_app/backend (canonical location)")
            print("   ℹ️  Please manually verify backend/ is not in use before deletion")
        else:
            print("   ✅ No duplicate directories found")
    
    def update_gitignore(self):
        """Update .gitignore with proper exclusions"""
        print("📝 Updating .gitignore...")
        
        gitignore_path = BASE_DIR / '.gitignore'
        
        # Essential gitignore patterns
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
.venv/
.venv-*/
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
.tox/
htmlcov/
*.log
pytest-*.txt
*_test_results_*.json

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Frontend
node_modules/
dist/
.next/
out/
build/

# Database
*.db
*.db-journal
*.sqlite
*.sqlite3

# Environment
.env
.env.local
.env.*.local

# Temporary files
tmp_*
temp_*
*.tmp
*.bak

# Logs
*.log
logs/

# ML Models (large files)
*.h5
*.pkl
*.joblib
*.pt
*.pth
*.onnx

# Keep model metadata
!ml_models/**/metadata.json
!ml_models/**/config.json
"""
        
        try:
            gitignore_path.write_text(gitignore_content)
            print("   ✅ Updated .gitignore")
        except Exception as e:
            self.log_action("error", gitignore_path, str(e))
    
    def generate_report(self):
        """Generate cleanup report"""
        print("\n" + "="*60)
        print("📊 CLEANUP REPORT")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = {
            "timestamp": timestamp,
            "deleted_files_count": len(self.deleted_files),
            "moved_files_count": len(self.moved_files),
            "errors_count": len(self.errors),
            "deleted_files": self.deleted_files[:50],  # First 50
            "moved_files": self.moved_files,
            "errors": self.errors,
        }
        
        # Save report
        report_path = BASE_DIR / 'documentation' / 'developer' / 'reports' / 'cleanup_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {report_path}")
        except Exception as e:
            print(f"   ⚠️  Could not save report: {e}")
        
        # Print summary
        print(f"\n✅ Files deleted: {len(self.deleted_files)}")
        print(f"✅ Files moved: {len(self.moved_files)}")
        if self.errors:
            print(f"⚠️  Errors encountered: {len(self.errors)}")
            for error in self.errors[:10]:
                print(f"   - {error}")
        else:
            print("✅ No errors")
        
        print("\n" + "="*60)
    
    def run_cleanup(self):
        """Run all cleanup operations"""
        print("\n🚀 Starting AgriSense Project Cleanup & Organization")
        print("="*60 + "\n")
        
        try:
            self.remove_pycache()
            self.remove_temp_files()
            self.organize_documentation()
            self.clean_root_directory()
            self.consolidate_duplicate_dirs()
            self.update_gitignore()
            self.generate_report()
            
            print("\n✨ Cleanup completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Review the cleanup report")
            print("   2. Test backend: uvicorn agrisense_app.backend.main:app --port 8004")
            print("   3. Test frontend: cd agrisense_app/frontend/farm-fortune-frontend-main && npm run dev")
            print("   4. Run tests: pytest -v")
            print("   5. Commit changes with: git add . && git commit -m 'chore: cleanup and organize project'")
            
        except Exception as e:
            print(f"\n❌ Cleanup failed with error: {e}")
            raise

if __name__ == "__main__":
    cleaner = ProjectCleaner()
    cleaner.run_cleanup()
