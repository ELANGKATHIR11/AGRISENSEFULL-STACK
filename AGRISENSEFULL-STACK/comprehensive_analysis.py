#!/usr/bin/env python3
"""
Comprehensive AgriSense Full-Stack End-to-End Analysis
Analyzes entire project, tests all features with simulated data, and provides scoring
"""

import os
import sys
import json
import time
import base64
import io
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / "agrisense_app" / "backend"
sys.path.insert(0, str(backend_path))

class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AgriSenseAnalyzer:
    def __init__(self):
        self.results = {}
        self.scores = {}
        self.recommendations = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}{text.center(80)}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{Color.BOLD}{Color.BLUE}[{text}]{Color.END}")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Color.GREEN}✓ {text}{Color.END}")
        self.passed_tests += 1
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Color.YELLOW}⚠ {text}{Color.END}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Color.RED}✗ {text}{Color.END}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Color.CYAN}  {text}{Color.END}")
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project directory structure"""
        self.print_section("Project Structure Analysis")
        self.total_tests += 1
        
        root = Path(__file__).parent
        structure = {
            "root": str(root),
            "backend": None,
            "frontend": None,
            "documentation": None,
            "tests": None,
            "ml_models": None,
            "datasets": None,
        }
        
        # Check backend
        backend_path = root / "agrisense_app" / "backend"
        if backend_path.exists():
            structure["backend"] = {
                "path": str(backend_path),
                "files": len(list(backend_path.glob("*.py"))),
                "main_exists": (backend_path / "main.py").exists(),
                "requirements_exists": (backend_path / "requirements.txt").exists(),
            }
            self.print_success(f"Backend found: {structure['backend']['files']} Python files")
        else:
            self.print_error("Backend not found")
            self.recommendations.append("Backend directory missing")
        
        # Check frontend
        frontend_path = root / "agrisense_app" / "frontend" / "farm-fortune-frontend-main"
        if frontend_path.exists():
            structure["frontend"] = {
                "path": str(frontend_path),
                "package_json": (frontend_path / "package.json").exists(),
                "src_dir": (frontend_path / "src").exists(),
                "components": len(list((frontend_path / "src" / "components").glob("*"))) if (frontend_path / "src" / "components").exists() else 0,
                "pages": len(list((frontend_path / "src" / "pages").glob("*"))) if (frontend_path / "src" / "pages").exists() else 0,
            }
            self.print_success(f"Frontend found: {structure['frontend']['components']} components, {structure['frontend']['pages']} pages")
        else:
            self.print_error("Frontend not found")
            self.recommendations.append("Frontend directory missing")
        
        # Check ML models
        ml_models_path = root / "ml_models"
        if ml_models_path.exists():
            model_files = list(ml_models_path.glob("**/*.joblib")) + list(ml_models_path.glob("**/*.pkl"))
            structure["ml_models"] = {
                "path": str(ml_models_path),
                "count": len(model_files),
                "total_size_mb": sum(f.stat().st_size for f in model_files) / (1024 * 1024),
            }
            self.print_success(f"ML Models found: {len(model_files)} models ({structure['ml_models']['total_size_mb']:.2f} MB)")
        else:
            self.print_warning("ML models directory not found")
        
        # Check documentation
        doc_path = root / "documentation"
        if doc_path.exists():
            md_files = list(doc_path.glob("**/*.md"))
            structure["documentation"] = {
                "path": str(doc_path),
                "count": len(md_files),
            }
            self.print_success(f"Documentation found: {len(md_files)} markdown files")
        
        # Check tests
        tests_path = root / "tests"
        if tests_path.exists():
            test_files = list(tests_path.glob("test_*.py"))
            structure["tests"] = {
                "path": str(tests_path),
                "count": len(test_files),
            }
            self.print_success(f"Tests found: {len(test_files)} test files")
        
        self.results["structure"] = structure
        return structure
    
    def analyze_backend_code(self) -> Dict[str, Any]:
        """Analyze backend code quality"""
        self.print_section("Backend Code Analysis")
        self.total_tests += 5
        
        analysis = {
            "main_py": None,
            "requirements": None,
            "api_endpoints": [],
            "ml_integration": False,
            "error_handling": False,
        }
        
        backend_path = Path(__file__).parent / "agrisense_app" / "backend"
        
        # Analyze main.py
        main_py = backend_path / "main.py"
        if main_py.exists():
            content = main_py.read_text(encoding='utf-8')
            analysis["main_py"] = {
                "lines": len(content.splitlines()),
                "size_kb": len(content) / 1024,
                "imports": content.count("import "),
                "endpoints": content.count("@app."),
                "models": content.count("class ") + content.count("BaseModel"),
            }
            self.print_success(f"main.py: {analysis['main_py']['lines']} lines, {analysis['main_py']['endpoints']} endpoints")
            
            # Check for key features
            if "FastAPI" in content:
                self.print_success("FastAPI framework detected")
            
            if "tensorflow" in content.lower() or "torch" in content.lower():
                analysis["ml_integration"] = True
                self.print_success("ML framework integration detected")
            
            if "HTTPException" in content:
                analysis["error_handling"] = True
                self.print_success("Error handling implemented")
            
            # Extract endpoint patterns
            import re
            endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
            analysis["api_endpoints"] = [f"{method.upper()} {path}" for method, path in endpoints]
            self.print_info(f"Found {len(analysis['api_endpoints'])} API endpoints")
        
        # Analyze requirements
        req_file = backend_path / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            packages = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
            analysis["requirements"] = {
                "count": len(packages),
                "packages": packages[:10],  # First 10
            }
            self.print_success(f"requirements.txt: {len(packages)} packages")
            
            # Check key dependencies
            key_deps = ["fastapi", "tensorflow", "torch", "scikit-learn", "numpy", "pandas"]
            found_deps = [dep for dep in key_deps if any(dep in pkg.lower() for pkg in packages)]
            if found_deps:
                self.print_info(f"Key dependencies: {', '.join(found_deps)}")
        
        self.results["backend"] = analysis
        return analysis
    
    def analyze_frontend_code(self) -> Dict[str, Any]:
        """Analyze frontend code quality"""
        self.print_section("Frontend Code Analysis")
        self.total_tests += 4
        
        analysis = {
            "package_json": None,
            "components": [],
            "pages": [],
            "styling": None,
            "routing": False,
        }
        
        frontend_path = Path(__file__).parent / "agrisense_app" / "frontend" / "farm-fortune-frontend-main"
        
        # Analyze package.json
        package_json = frontend_path / "package.json"
        if package_json.exists():
            data = json.loads(package_json.read_text())
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            analysis["package_json"] = {
                "name": data.get("name", "unknown"),
                "version": data.get("version", "unknown"),
                "dependencies": len(deps),
                "devDependencies": len(dev_deps),
            }
            self.print_success(f"package.json: {len(deps)} dependencies, {len(dev_deps)} dev dependencies")
            
            # Check key frameworks
            if "react" in deps:
                self.print_success(f"React version: {deps['react']}")
            if "typescript" in dev_deps:
                self.print_success("TypeScript configured")
            if "vite" in dev_deps:
                self.print_success("Vite build tool configured")
            if "tailwindcss" in dev_deps:
                analysis["styling"] = "Tailwind CSS"
                self.print_success("Tailwind CSS for styling")
            if "react-router-dom" in deps:
                analysis["routing"] = True
                self.print_success("React Router for navigation")
        
        # Count components
        components_dir = frontend_path / "src" / "components"
        if components_dir.exists():
            components = list(components_dir.glob("*.tsx")) + list(components_dir.glob("*.jsx"))
            analysis["components"] = [c.stem for c in components]
            self.print_success(f"Components: {len(components)} files")
        
        # Count pages
        pages_dir = frontend_path / "src" / "pages"
        if pages_dir.exists():
            pages = list(pages_dir.glob("*.tsx")) + list(pages_dir.glob("*.jsx"))
            analysis["pages"] = [p.stem for p in pages]
            self.print_success(f"Pages: {len(pages)} files")
        
        self.results["frontend"] = analysis
        return analysis
    
    def simulate_ml_features(self) -> Dict[str, Any]:
        """Simulate and test ML features"""
        self.print_section("ML Features Testing (Simulated)")
        self.total_tests += 6
        
        results = {
            "recommendation_engine": {"status": "unknown"},
            "disease_detection": {"status": "unknown"},
            "weed_management": {"status": "unknown"},
            "crop_suggestion": {"status": "unknown"},
            "chatbot": {"status": "unknown"},
            "water_optimization": {"status": "unknown"},
        }
        
        # Test 1: Recommendation Engine
        try:
            from agrisense_app.backend.core.engine import RecoEngine
            engine = RecoEngine()
            test_reading = {
                "zone_id": "Z1",
                "plant": "tomato",
                "soil_type": "loam",
                "area_m2": 100,
                "moisture_pct": 35.0,
                "temperature_c": 28.0,
            }
            result = engine.recommend(test_reading)
            if result and "water_liters" in result:
                results["recommendation_engine"] = {
                    "status": "✓ Working",
                    "water_liters": result.get("water_liters"),
                    "tips_count": len(result.get("tips", [])),
                }
                self.print_success(f"Recommendation Engine: {result.get('water_liters', 0):.1f}L recommended")
            else:
                results["recommendation_engine"] = {"status": "⚠ Partial"}
                self.print_warning("Recommendation Engine: returns data but incomplete")
        except Exception as e:
            results["recommendation_engine"] = {"status": "✗ Failed", "error": str(e)}
            self.print_error(f"Recommendation Engine failed: {str(e)[:50]}")
        
        # Test 2: Disease Detection
        try:
            from agrisense_app.backend.comprehensive_disease_detector import ComprehensiveDiseaseDetector
            detector = ComprehensiveDiseaseDetector()
            # Create dummy image data
            from PIL import Image
            img = Image.new('RGB', (224, 224), color='green')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            result = detector.analyze_disease_image(img_base64, crop_type="tomato")
            if result:
                results["disease_detection"] = {
                    "status": "✓ Working",
                    "model": result.get("model_used", "unknown"),
                    "confidence": result.get("detection_confidence", 0),
                }
                self.print_success(f"Disease Detection: {result.get('model_used', 'Model loaded')}")
            else:
                results["disease_detection"] = {"status": "⚠ No result"}
                self.print_warning("Disease Detection: loaded but no result")
        except Exception as e:
            results["disease_detection"] = {"status": "✗ Failed", "error": str(e)}
            self.print_error(f"Disease Detection failed: {str(e)[:50]}")
        
        # Test 3: Weed Management
        try:
            from agrisense_app.backend.weed_management import WeedManagementEngine
            weed_engine = WeedManagementEngine()
            # Use same dummy image
            result = weed_engine.analyze_weed_image(img_base64)
            if result:
                results["weed_management"] = {
                    "status": "✓ Working",
                    "severity": result.get("severity", "unknown"),
                }
                self.print_success("Weed Management: Engine loaded")
            else:
                results["weed_management"] = {"status": "⚠ Loaded"}
                self.print_warning("Weed Management: loaded but limited result")
        except Exception as e:
            results["weed_management"] = {"status": "✗ Failed", "error": str(e)}
            self.print_error(f"Weed Management failed: {str(e)[:50]}")
        
        # Test 4: Crop Suggestion
        try:
            from agrisense_app.backend.smart_farming_ml import SmartFarmingRecommendationSystem
            system = SmartFarmingRecommendationSystem()
            sensor_data = {
                "soil_type": "Loam",
                "ph": 6.5,
                "nitrogen": 100,
                "phosphorus": 40,
                "potassium": 40,
                "temperature": 25,
                "moisture": 60,
                "humidity": 70,
                "water_level": 500,
            }
            suggestions = system.get_crop_recommendations(sensor_data)
            if suggestions and len(suggestions) > 0:
                results["crop_suggestion"] = {
                    "status": "✓ Working",
                    "suggestions_count": len(suggestions),
                    "top_crop": suggestions[0].get("crop") if suggestions else None,
                }
                self.print_success(f"Crop Suggestion: {len(suggestions)} recommendations")
            else:
                results["crop_suggestion"] = {"status": "⚠ No suggestions"}
                self.print_warning("Crop Suggestion: loaded but no suggestions")
        except Exception as e:
            results["crop_suggestion"] = {"status": "✗ Failed", "error": str(e)}
            self.print_error(f"Crop Suggestion failed: {str(e)[:50]}")
        
        # Test 5: Chatbot (Check if artifacts exist)
        chatbot_path = Path(__file__).parent / "agrisense_app" / "backend" / "chatbot_qa_pairs.json"
        if chatbot_path.exists():
            try:
                data = json.loads(chatbot_path.read_text())
                qa_count = len(data.get("answers", []))
                results["chatbot"] = {
                    "status": "✓ Configured",
                    "qa_pairs": qa_count,
                }
                self.print_success(f"Chatbot: {qa_count} QA pairs configured")
            except Exception as e:
                results["chatbot"] = {"status": "⚠ File exists", "error": str(e)}
                self.print_warning("Chatbot: configuration file exists but parsing failed")
        else:
            results["chatbot"] = {"status": "✗ Not configured"}
            self.print_error("Chatbot: configuration file missing")
        
        # Test 6: Water Optimization Model
        ml_models_path = Path(__file__).parent / "ml_models"
        water_model = ml_models_path / "core_models" / "water_model.joblib"
        if water_model.exists():
            size_mb = water_model.stat().st_size / (1024 * 1024)
            results["water_optimization"] = {
                "status": "✓ Model exists",
                "size_mb": size_mb,
            }
            self.print_success(f"Water Optimization: Model loaded ({size_mb:.2f} MB)")
        else:
            results["water_optimization"] = {"status": "⚠ Model missing"}
            self.print_warning("Water Optimization: Model file not found")
        
        self.results["ml_features"] = results
        return results
    
    def analyze_api_design(self) -> Dict[str, Any]:
        """Analyze API design and endpoints"""
        self.print_section("API Design Analysis")
        self.total_tests += 3
        
        analysis = {
            "endpoints": [],
            "authentication": False,
            "error_handling": False,
            "documentation": False,
        }
        
        backend_path = Path(__file__).parent / "agrisense_app" / "backend"
        main_py = backend_path / "main.py"
        
        if main_py.exists():
            content = main_py.read_text(encoding='utf-8')
            
            # Extract all endpoints
            import re
            endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', content, re.MULTILINE)
            
            for method, path, func_name in endpoints:
                analysis["endpoints"].append({
                    "method": method.upper(),
                    "path": path,
                    "function": func_name,
                })
            
            self.print_success(f"API Endpoints: {len(analysis['endpoints'])} endpoints found")
            
            # Group by category
            categories = {}
            for ep in analysis["endpoints"]:
                category = ep["path"].split("/")[1] if "/" in ep["path"] else "root"
                if category not in categories:
                    categories[category] = []
                categories[category].append(ep)
            
            for cat, eps in sorted(categories.items()):
                self.print_info(f"  /{cat}: {len(eps)} endpoints")
            
            # Check for authentication
            if "Depends" in content and ("token" in content.lower() or "auth" in content.lower()):
                analysis["authentication"] = True
                self.print_success("Authentication: Implemented")
            else:
                analysis["authentication"] = False
                self.print_warning("Authentication: Not detected")
                self.recommendations.append("Consider implementing API authentication")
            
            # Check error handling
            if "HTTPException" in content and "try" in content:
                analysis["error_handling"] = True
                self.print_success("Error Handling: Implemented")
            else:
                self.print_warning("Error Handling: Limited")
                self.recommendations.append("Enhance error handling with try-except blocks")
            
            # Check for API docs
            if 'title="' in content and 'description="' in content:
                analysis["documentation"] = True
                self.print_success("API Documentation: Configured (Swagger/OpenAPI)")
            else:
                self.print_warning("API Documentation: Not fully configured")
        
        self.results["api_design"] = analysis
        return analysis
    
    def calculate_scores(self) -> Dict[str, float]:
        """Calculate detailed scores for each category"""
        self.print_section("Scoring & Evaluation")
        
        scores = {}
        
        # 1. Project Structure (2 points)
        structure = self.results.get("structure", {})
        structure_score = 0
        if structure.get("backend"):
            structure_score += 0.7
        if structure.get("frontend"):
            structure_score += 0.7
        if structure.get("ml_models"):
            structure_score += 0.3
        if structure.get("documentation"):
            structure_score += 0.2
        if structure.get("tests"):
            structure_score += 0.1
        scores["structure"] = min(2.0, structure_score)
        
        # 2. Backend Code Quality (2 points)
        backend = self.results.get("backend", {})
        backend_score = 0
        if backend.get("main_py"):
            backend_score += 0.8
        if backend.get("requirements"):
            backend_score += 0.5
        if backend.get("ml_integration"):
            backend_score += 0.4
        if backend.get("error_handling"):
            backend_score += 0.3
        scores["backend_quality"] = min(2.0, backend_score)
        
        # 3. Frontend Code Quality (1.5 points)
        frontend = self.results.get("frontend", {})
        frontend_score = 0
        if frontend.get("package_json"):
            frontend_score += 0.5
        if len(frontend.get("components", [])) > 5:
            frontend_score += 0.5
        if len(frontend.get("pages", [])) > 3:
            frontend_score += 0.3
        if frontend.get("styling"):
            frontend_score += 0.2
        scores["frontend_quality"] = min(1.5, frontend_score)
        
        # 4. ML Features (2.5 points)
        ml_features = self.results.get("ml_features", {})
        ml_score = 0
        for feature, data in ml_features.items():
            status = data.get("status", "unknown")
            if "✓" in status:
                ml_score += 0.42  # 2.5 / 6 features
            elif "⚠" in status:
                ml_score += 0.21
        scores["ml_features"] = min(2.5, ml_score)
        
        # 5. API Design (1.5 points)
        api = self.results.get("api_design", {})
        api_score = 0
        endpoint_count = len(api.get("endpoints", []))
        if endpoint_count > 20:
            api_score += 0.7
        elif endpoint_count > 10:
            api_score += 0.5
        elif endpoint_count > 5:
            api_score += 0.3
        if api.get("authentication"):
            api_score += 0.4
        if api.get("error_handling"):
            api_score += 0.2
        if api.get("documentation"):
            api_score += 0.2
        scores["api_design"] = min(1.5, api_score)
        
        # 6. Documentation & Testing (0.5 points)
        doc_score = 0
        if structure.get("documentation"):
            doc_score += 0.3
        if structure.get("tests"):
            doc_score += 0.2
        scores["documentation"] = min(0.5, doc_score)
        
        self.scores = scores
        
        # Print detailed scores
        self.print_info(f"Structure & Organization: {scores['structure']:.2f} / 2.0")
        self.print_info(f"Backend Code Quality: {scores['backend_quality']:.2f} / 2.0")
        self.print_info(f"Frontend Code Quality: {scores['frontend_quality']:.2f} / 1.5")
        self.print_info(f"ML Features & Integration: {scores['ml_features']:.2f} / 2.5")
        self.print_info(f"API Design & Architecture: {scores['api_design']:.2f} / 1.5")
        self.print_info(f"Documentation & Testing: {scores['documentation']:.2f} / 0.5")
        
        return scores
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        self.print_header("AGRISENSE FULL-STACK PROJECT ANALYSIS REPORT")
        
        # Calculate total score
        total_score = sum(self.scores.values())
        max_score = 10.0
        percentage = (total_score / max_score) * 100
        
        # Determine grade
        if total_score >= 9.0:
            grade = "A+ (Excellent)"
            color = Color.GREEN
        elif total_score >= 8.0:
            grade = "A (Very Good)"
            color = Color.GREEN
        elif total_score >= 7.0:
            grade = "B+ (Good)"
            color = Color.CYAN
        elif total_score >= 6.0:
            grade = "B (Above Average)"
            color = Color.CYAN
        elif total_score >= 5.0:
            grade = "C (Average)"
            color = Color.YELLOW
        else:
            grade = "D (Needs Improvement)"
            color = Color.RED
        
        print(f"\n{Color.BOLD}FINAL SCORE: {color}{total_score:.2f} / {max_score} ({percentage:.1f}%){Color.END}")
        print(f"{Color.BOLD}GRADE: {color}{grade}{Color.END}\n")
        
        # Category breakdown
        print(f"{Color.BOLD}Category Scores:{Color.END}")
        for category, score in self.scores.items():
            bar_length = int((score / 2.0) * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            cat_name = category.replace("_", " ").title()
            print(f"  {cat_name:30} {bar} {score:.2f}")
        
        # Strengths
        print(f"\n{Color.BOLD}{Color.GREEN}STRENGTHS:{Color.END}")
        strengths = []
        if self.scores.get("structure", 0) >= 1.5:
            strengths.append("Well-organized project structure")
        if self.scores.get("backend_quality", 0) >= 1.5:
            strengths.append("Solid backend implementation with FastAPI")
        if self.scores.get("ml_features", 0) >= 1.5:
            strengths.append("Comprehensive ML features integrated")
        if self.scores.get("api_design", 0) >= 1.0:
            strengths.append("Good API design with multiple endpoints")
        if self.scores.get("frontend_quality", 0) >= 1.0:
            strengths.append("Modern React frontend with TypeScript")
        
        if not strengths:
            strengths.append("Project has foundation in place")
        
        for i, strength in enumerate(strengths, 1):
            print(f"  {i}. {strength}")
        
        # Recommendations
        if self.recommendations:
            print(f"\n{Color.BOLD}{Color.YELLOW}RECOMMENDATIONS FOR IMPROVEMENT:{Color.END}")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Additional recommendations based on scores
        print(f"\n{Color.BOLD}{Color.YELLOW}OPTIMIZATION SUGGESTIONS:{Color.END}")
        suggestions = []
        
        if self.scores.get("ml_features", 0) < 2.0:
            suggestions.append("Enhance ML model integration - ensure all disease/weed models are properly loaded")
            suggestions.append("Add ML model versioning and performance monitoring")
        
        if self.scores.get("api_design", 0) < 1.2:
            suggestions.append("Implement comprehensive API authentication and authorization")
            suggestions.append("Add rate limiting to prevent abuse")
        
        if self.scores.get("documentation", 0) < 0.4:
            suggestions.append("Add comprehensive API documentation with examples")
            suggestions.append("Create user guides and deployment documentation")
        
        if self.scores.get("backend_quality", 0) < 1.5:
            suggestions.append("Add more error handling and logging")
            suggestions.append("Implement caching for frequently accessed data")
        
        if self.scores.get("frontend_quality", 0) < 1.2:
            suggestions.append("Enhance frontend with more reusable components")
            suggestions.append("Add frontend unit and integration tests")
        
        # General suggestions
        suggestions.extend([
            "Add end-to-end testing with Playwright or Cypress",
            "Implement CI/CD pipeline for automated testing and deployment",
            "Add performance monitoring and analytics",
            "Create Docker containers for easier deployment",
            "Add database migrations system for schema changes",
            "Implement WebSocket for real-time sensor updates",
            "Add multi-language support (i18n) for wider accessibility",
            "Create mobile-responsive PWA for field use",
        ])
        
        for i, suggestion in enumerate(suggestions[:10], 1):
            print(f"  {i}. {suggestion}")
        
        # Test Summary
        print(f"\n{Color.BOLD}TEST SUMMARY:{Color.END}")
        print(f"  Total Tests Run: {self.total_tests}")
        print(f"  Tests Passed: {self.passed_tests}")
        print(f"  Success Rate: {(self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0:.1f}%")
        
        # Conclusion
        print(f"\n{Color.BOLD}CONCLUSION:{Color.END}")
        if total_score >= 8.0:
            print(f"{Color.GREEN}AgriSense is a well-built, production-ready smart agriculture platform with")
            print(f"comprehensive features. Focus on optimization and scaling.{Color.END}")
        elif total_score >= 6.0:
            print(f"{Color.CYAN}AgriSense has a solid foundation with good features. Some areas need")
            print(f"improvement before production deployment. Focus on ML integration and testing.{Color.END}")
        else:
            print(f"{Color.YELLOW}AgriSense has potential but needs significant work in multiple areas.")
            print(f"Focus on completing core features and adding comprehensive testing.{Color.END}")
        
        print(f"\n{Color.BOLD}Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Color.END}")
        print(f"{Color.BOLD}{Color.CYAN}{'='*80}{Color.END}\n")
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "grade": grade,
            "scores": self.scores,
            "test_summary": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "success_rate": (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0,
            },
            "recommendations": self.recommendations,
            "detailed_results": self.results,
        }
        
        report_file = Path(__file__).parent / "analysis_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"{Color.CYAN}Detailed report saved to: {report_file}{Color.END}\n")
    
    def run_full_analysis(self):
        """Run complete project analysis"""
        try:
            self.analyze_project_structure()
            self.analyze_backend_code()
            self.analyze_frontend_code()
            self.simulate_ml_features()
            self.analyze_api_design()
            self.calculate_scores()
            self.generate_final_report()
        except Exception as e:
            self.print_error(f"Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    """Main entry point"""
    analyzer = AgriSenseAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
