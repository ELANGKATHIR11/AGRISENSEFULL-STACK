"""
Test Hybrid LLM+VLM Agricultural AI System

This script tests the offline-capable hybrid AI combining:
- Phi LLM for language understanding
- SCOLD VLM for visual analysis
- Multimodal agricultural intelligence
"""

import base64
import json
import time
from pathlib import Path
from typing import Dict, Any

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Fallback color stubs
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = BLUE = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

import requests


# ============================================================================
# Configuration
# ============================================================================

API_BASE = "http://localhost:8004"
HYBRID_BASE = f"{API_BASE}/api/hybrid"

# Test image (simple 1x1 pixel PNG for demo - replace with real images)
SAMPLE_IMAGE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


# ============================================================================
# Helper Functions
# ============================================================================

def print_header(text: str):
    """Print section header"""
    if COLORS_AVAILABLE:
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    else:
        print(f"\n{'=' * 70}")
        print(text)
        print('=' * 70)


def print_success(text: str):
    """Print success message"""
    if COLORS_AVAILABLE:
        print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")
    else:
        print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    if COLORS_AVAILABLE:
        print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")
    else:
        print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    if COLORS_AVAILABLE:
        print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")
    else:
        print(f"ℹ️  {text}")


def print_result(label: str, value: Any):
    """Print result key-value pair"""
    if COLORS_AVAILABLE:
        print(f"{Fore.YELLOW}{label}:{Style.RESET_ALL} {value}")
    else:
        print(f"{label}: {value}")


# ============================================================================
# Test Functions
# ============================================================================

def test_health_check():
    """Test 1: Health check"""
    print_header("Test 1: Health Check")
    
    try:
        response = requests.get(f"{HYBRID_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Hybrid AI service is running")
            print_result("Status", data.get("status"))
            print_result("Hybrid Available", data.get("hybrid_available"))
            
            components = data.get("components", {})
            print_info(f"Phi LLM: {components.get('phi_llm', 'unknown')}")
            print_info(f"SCOLD VLM: {components.get('scold_vlm', 'unknown')}")
            return True
        else:
            print_error(f"Health check failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend. Is it running on port 8004?")
        return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_system_status():
    """Test 2: System status"""
    print_header("Test 2: System Status")
    
    try:
        response = requests.get(f"{HYBRID_BASE}/status", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Status retrieved")
            
            print_result("Hybrid AI Available", data.get("hybrid_ai_available"))
            print_result("Phi LLM Available", data.get("phi_llm_available"))
            print_result("SCOLD VLM Available", data.get("scold_vlm_available"))
            print_result("Mode", data.get("mode"))
            print_result("History Length", data.get("conversation_history_length"))
            
            config = data.get("config", {})
            print_info(f"Phi Model: {config.get('phi_model')}")
            print_info(f"Temperature: {config.get('temperature')}")
            print_info(f"Timeout: {config.get('timeout')}s")
            
            return True
        else:
            print_error(f"Status check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Status check failed: {e}")
        return False


def test_text_analysis():
    """Test 3: Text-only analysis"""
    print_header("Test 3: Text-Only Agricultural Advice")
    
    questions = [
        "When is the best time to plant tomatoes?",
        "What are the signs of nitrogen deficiency in plants?",
        "How do I prepare soil for organic farming?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{Fore.MAGENTA if COLORS_AVAILABLE else ''}Question {i}: {question}{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{HYBRID_BASE}/text",
                json={
                    "query": question,
                    "context": {"test_mode": True},
                    "use_history": True
                },
                timeout=30
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print_success(f"Analysis completed in {elapsed:.0f}ms")
                    
                    answer = data.get("response", "")
                    if len(answer) > 200:
                        answer = answer[:200] + "..."
                    print_result("Response", answer)
                    
                    print_result("Confidence", f"{data.get('confidence', 0):.2f}")
                    
                    recs = data.get("recommendations", [])
                    if recs:
                        print_info(f"Recommendations: {len(recs)}")
                        for j, rec in enumerate(recs[:3], 1):
                            print(f"   {j}. {rec[:80]}...")
                else:
                    print_error("Analysis failed")
            else:
                print_error(f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print_error(f"Request failed: {e}")
    
    return True


def test_image_analysis():
    """Test 4: Image-only analysis"""
    print_header("Test 4: Image-Only Visual Analysis")
    
    analysis_types = [
        "disease_detection",
        "crop_health",
        "weed_identification"
    ]
    
    for analysis_type in analysis_types:
        print(f"\n{Fore.MAGENTA if COLORS_AVAILABLE else ''}Analysis Type: {analysis_type}{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{HYBRID_BASE}/image",
                json={
                    "image_base64": SAMPLE_IMAGE_B64,
                    "analysis_type": analysis_type,
                    "custom_prompt": None
                },
                timeout=30
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print_success(f"Analysis completed in {elapsed:.0f}ms")
                    
                    detections = data.get("detections", [])
                    print_result("Detections", len(detections))
                    
                    if detections:
                        print_info(f"First detection: {detections[0]}")
                    
                    print_result("Confidence", f"{data.get('confidence', 0):.2f}")
                    print_result("Severity", data.get("severity", "N/A"))
                else:
                    print_error("Analysis failed")
            else:
                print_error(f"HTTP {response.status_code}")
                
        except Exception as e:
            print_error(f"Request failed: {e}")
    
    return True


def test_multimodal_analysis():
    """Test 5: Multimodal analysis (image + text)"""
    print_header("Test 5: Multimodal Analysis (Image + Text)")
    
    test_cases = [
        {
            "query": "What disease is affecting this plant?",
            "context": {"crop": "tomato", "location": "greenhouse"}
        },
        {
            "query": "Is this weed harmful to my crops?",
            "context": {"crop": "wheat", "region": "North India"}
        },
        {
            "query": "How severe is the pest damage?",
            "context": {"crop": "rice", "season": "monsoon"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Fore.MAGENTA if COLORS_AVAILABLE else ''}Test Case {i}: {test_case['query']}{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{HYBRID_BASE}/analyze",
                json={
                    "image_base64": SAMPLE_IMAGE_B64,
                    "query": test_case["query"],
                    "context": test_case["context"]
                },
                timeout=45
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print_success(f"Multimodal analysis completed in {elapsed:.0f}ms")
                    
                    print_result("Analysis Type", data.get("analysis_type"))
                    print_result("Confidence Score", f"{data.get('confidence_score', 0):.2f}")
                    
                    synthesis = data.get("synthesis", "")
                    if synthesis and len(synthesis) > 150:
                        synthesis = synthesis[:150] + "..."
                    print_result("Synthesis", synthesis)
                    
                    steps = data.get("actionable_steps", [])
                    if steps:
                        print_info(f"Actionable Steps: {len(steps)}")
                        for j, step in enumerate(steps[:3], 1):
                            print(f"   {j}. {step[:70]}...")
                    
                    # Visual analysis
                    visual = data.get("visual_analysis")
                    if visual:
                        print_info(f"Visual detections: {len(visual.get('detections', []))}")
                        print_info(f"Visual confidence: {visual.get('confidence', 0):.2f}")
                    
                    # Textual analysis
                    textual = data.get("textual_analysis")
                    if textual:
                        print_info(f"Textual confidence: {textual.get('confidence', 0):.2f}")
                        recs = textual.get("recommendations", [])
                        print_info(f"Text recommendations: {len(recs)}")
                else:
                    print_error("Analysis failed")
            else:
                print_error(f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print_error(f"Request failed: {e}")
    
    return True


def test_conversation_history():
    """Test 6: Conversation history"""
    print_header("Test 6: Conversation History Management")
    
    # Ask related questions to test history
    questions = [
        "Tell me about tomato cultivation",
        "What fertilizer should I use?",  # Should understand "for tomatoes"
        "When should I harvest?"  # Should understand "tomatoes"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{Fore.MAGENTA if COLORS_AVAILABLE else ''}Question {i}: {question}{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
        
        try:
            response = requests.post(
                f"{HYBRID_BASE}/text",
                json={
                    "query": question,
                    "use_history": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    answer = data.get("response", "")[:150]
                    print_success(f"Response: {answer}...")
            
        except Exception as e:
            print_error(f"Request failed: {e}")
    
    # Clear history
    print(f"\n{Fore.YELLOW if COLORS_AVAILABLE else ''}Clearing conversation history...{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
    try:
        response = requests.post(f"{HYBRID_BASE}/history/clear", timeout=5)
        if response.status_code == 200:
            print_success("History cleared")
        else:
            print_error("Failed to clear history")
    except Exception as e:
        print_error(f"Clear history failed: {e}")
    
    return True


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print_header("🤖 Hybrid Agricultural AI - Test Suite")
    print_info(f"Testing endpoint: {HYBRID_BASE}")
    print_info("Note: Using sample image - replace with real agricultural images for full testing")
    
    tests = [
        ("Health Check", test_health_check),
        ("System Status", test_system_status),
        ("Text Analysis", test_text_analysis),
        ("Image Analysis", test_image_analysis),
        ("Multimodal Analysis", test_multimodal_analysis),
        ("Conversation History", test_conversation_history)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print_error("\nTests interrupted by user")
            break
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("📊 Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Fore.GREEN if result else Fore.RED
        if COLORS_AVAILABLE:
            print(f"{color}{status:<6} {Style.RESET_ALL}{test_name}")
        else:
            print(f"{status:<6} {test_name}")
    
    print(f"\n{Fore.CYAN if COLORS_AVAILABLE else ''}{'─' * 70}{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
    
    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
    else:
        print_error(f"Some tests failed: {passed}/{total} passed")
    
    print(f"\n{Fore.YELLOW if COLORS_AVAILABLE else ''}💡 Next Steps:{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
    print("1. Test with real agricultural images")
    print("2. Verify Ollama is running: ollama serve")
    print("3. Verify Phi model is available: ollama list")
    print("4. Check SCOLD VLM if visual analysis fails")
    print("5. Review API docs: http://localhost:8004/docs")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW if COLORS_AVAILABLE else ''}Tests interrupted{Style.RESET_ALL if COLORS_AVAILABLE else ''}")
        exit(130)
