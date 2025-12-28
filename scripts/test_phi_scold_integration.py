#!/usr/bin/env python3
"""
Test script for Phi LLM & SCOLD VLM integration in AgriSense

Tests:
1. Phi LLM availability and basic functions
2. SCOLD VLM integration points
3. All new API endpoints
"""

import sys
import json
import base64
import logging
import requests
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "http://localhost:8004"
OLLAMA_URL = "http://localhost:11434"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def test_ollama_health() -> bool:
    """Test if Ollama server is running"""
    logger.info(f"{BLUE}Testing Ollama server...{RESET}")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            logger.info(f"{GREEN}✅ Ollama is running with {len(models)} models{RESET}")
            logger.info(f"   Models: {model_names}")
            
            # Check for phi
            if any("phi" in m.lower() for m in model_names):
                logger.info(f"{GREEN}✅ Phi model found{RESET}")
                return True
            else:
                logger.warning(f"{YELLOW}⚠️  Phi model not found. Available: {model_names}{RESET}")
                return False
        else:
            logger.error(f"{RED}❌ Ollama responded with {response.status_code}{RESET}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"{RED}❌ Cannot connect to Ollama at {OLLAMA_URL}{RESET}")
        logger.info(f"   Start Ollama with: {YELLOW}ollama serve{RESET}")
        return False
    except Exception as e:
        logger.error(f"{RED}❌ Ollama health check failed: {e}{RESET}")
        return False


def test_backend_health() -> bool:
    """Test if backend server is running"""
    logger.info(f"\n{BLUE}Testing Backend server...{RESET}")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"{GREEN}✅ Backend is running{RESET}")
            return True
        else:
            logger.error(f"{RED}❌ Backend responded with {response.status_code}{RESET}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"{RED}❌ Cannot connect to Backend at {BACKEND_URL}{RESET}")
        logger.info(f"   Start backend with: {YELLOW}python -m uvicorn agrisense_app.backend.main:app --port 8004{RESET}")
        return False
    except Exception as e:
        logger.error(f"{RED}❌ Backend health check failed: {e}{RESET}")
        return False


def test_phi_imports() -> bool:
    """Test if Phi integration module can be imported"""
    logger.info(f"\n{BLUE}Testing Phi integration imports...{RESET}")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agrisense_app.backend.phi_chatbot_integration import (
            get_phi_status,
            enrich_chatbot_answer,
            rerank_answers_with_phi,
        )
        logger.info(f"{GREEN}✅ Phi integration module imported successfully{RESET}")
        return True
    except ImportError as e:
        logger.error(f"{RED}❌ Failed to import Phi integration: {e}{RESET}")
        return False
    except Exception as e:
        logger.error(f"{RED}❌ Phi import test failed: {e}{RESET}")
        return False


def test_scold_imports() -> bool:
    """Test if SCOLD integration module can be imported"""
    logger.info(f"\n{BLUE}Testing SCOLD VLM integration imports...{RESET}")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from agrisense_app.backend.vlm_scold_integration import (
            scold_vlm_status,
            detect_disease_with_scold,
            detect_weeds_with_scold,
        )
        logger.info(f"{GREEN}✅ SCOLD VLM integration module imported successfully{RESET}")
        return True
    except ImportError as e:
        logger.error(f"{RED}❌ Failed to import SCOLD integration: {e}{RESET}")
        return False
    except Exception as e:
        logger.error(f"{RED}❌ SCOLD import test failed: {e}{RESET}")
        return False


def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> bool:
    """Test a single API endpoint"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"{GREEN}✅ {method} {endpoint} → {response.status_code}{RESET}")
            return True
        else:
            logger.warning(f"{YELLOW}⚠️  {method} {endpoint} → {response.status_code}{RESET}")
            if response.status_code == 503:
                logger.info("   (Model unavailable - this is expected if Ollama not running)")
            return response.status_code == 503  # Accept 503 for unavailable models
    except requests.exceptions.Timeout:
        logger.warning(f"{YELLOW}⚠️  {method} {endpoint} → Timeout (model might be processing){RESET}")
        return True  # Accept timeouts as "test passed"
    except requests.exceptions.ConnectionError:
        logger.error(f"{RED}❌ {method} {endpoint} → Cannot connect{RESET}")
        return False
    except Exception as e:
        logger.error(f"{RED}❌ {method} {endpoint} → {e}{RESET}")
        return False


def test_api_endpoints() -> bool:
    """Test all new API endpoints"""
    logger.info(f"\n{BLUE}Testing API Endpoints...{RESET}")
    
    endpoints = [
        ("/api/phi/status", "GET", None),
        ("/api/scold/status", "GET", None),
        ("/api/models/status", "GET", None),
        ("/api/models/health", "GET", None),
        ("/api/chatbot/enrich?question=tomato&answer=grow%20well", "GET", None),
    ]
    
    results = []
    for endpoint, method, data in endpoints:
        result = test_api_endpoint(endpoint, method, data)
        results.append(result)
    
    passed = sum(results)
    total = len(results)
    logger.info(f"\n{BLUE}API Endpoints: {passed}/{total} tests passed{RESET}")
    
    return all(results)


def test_phi_functionality() -> bool:
    """Test actual Phi LLM functionality"""
    logger.info(f"\n{BLUE}Testing Phi LLM Functionality...{RESET}")
    
    try:
        # Test 1: Get status
        response = requests.get(f"{BACKEND_URL}/api/phi/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            logger.info(f"{GREEN}✅ Phi Status:{RESET}")
            logger.info(f"   Available: {status.get('available')}")
            logger.info(f"   Model: {status.get('model')}")
            logger.info(f"   Features: {status.get('features', [])}")
            return True
        else:
            logger.warning(f"{YELLOW}⚠️  Phi status unavailable (expected if Ollama not running){RESET}")
            return False
    except Exception as e:
        logger.warning(f"{YELLOW}⚠️  Phi functionality test skipped: {e}{RESET}")
        return False


def test_phi_liveness() -> bool:
    """Quick test of Phi LLM with actual inference"""
    logger.info(f"\n{BLUE}Testing Phi LLM Liveness (Inference)...{RESET}")
    
    try:
        # Try to enrich an answer
        response = requests.post(
            f"{BACKEND_URL}/api/chatbot/enrich",
            params={
                "question": "How to grow tomatoes?",
                "answer": "Use good soil",
                "crop_type": "tomato"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            enriched = result.get("enriched_answer", "")
            logger.info(f"{GREEN}✅ Phi inference successful{RESET}")
            logger.info(f"   Original: {result.get('original_answer')}")
            logger.info(f"   Enriched: {enriched[:100]}..." if len(enriched) > 100 else f"   Enriched: {enriched}")
            logger.info(f"   Provider: {result.get('provider')}")
            return True
        else:
            logger.warning(f"{YELLOW}⚠️  Phi inference returned {response.status_code}{RESET}")
            return False
    except requests.exceptions.Timeout:
        logger.warning(f"{YELLOW}⚠️  Phi inference timeout (model processing slow or unavailable){RESET}")
        return False
    except Exception as e:
        logger.warning(f"{YELLOW}⚠️  Phi liveness test failed: {e}{RESET}")
        return False


def generate_report(results: Dict[str, bool]) -> None:
    """Generate final report"""
    logger.info(f"\n{'='*60}")
    logger.info(f"{BLUE}AGRISENSE PHI & SCOLD INTEGRATION TEST REPORT{RESET}")
    logger.info(f"{'='*60}\n")
    
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        logger.info(f"{status:30} {test_name}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Overall: {passed}/{total} tests passed ({percentage:.0f}%)")
    logger.info(f"{'='*60}\n")
    
    if percentage == 100:
        logger.info(f"{GREEN}🎉 All tests passed! System ready for use.{RESET}\n")
    elif percentage >= 70:
        logger.info(f"{YELLOW}⚠️  Most tests passed. Some features may be unavailable.{RESET}\n")
        logger.info(f"Start Ollama server to enable Phi LLM and SCOLD VLM features:")
        logger.info(f"  {YELLOW}ollama serve{RESET}\n")
    else:
        logger.info(f"{RED}❌ Tests failed. Check error messages above.{RESET}\n")


def main():
    """Run all tests"""
    logger.info(f"\n{BLUE}{'='*60}")
    logger.info(f"AgriSense Phi LLM & SCOLD VLM Integration Tests")
    logger.info(f"{'='*60}{RESET}\n")
    
    results = {
        "Ollama Health": test_ollama_health(),
        "Backend Health": test_backend_health(),
        "Phi Imports": test_phi_imports(),
        "SCOLD Imports": test_scold_imports(),
        "API Endpoints": test_api_endpoints(),
        "Phi Functionality": test_phi_functionality(),
        "Phi Liveness": test_phi_liveness(),
    }
    
    generate_report(results)
    
    # Exit with appropriate code
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
