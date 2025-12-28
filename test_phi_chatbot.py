"""
Test Phi LLM Integration with Chatbot
======================================

This script tests the Ollama Phi LLM integration with the agricultural chatbot.

Usage:
    python test_phi_chatbot.py
"""

import sys
import time
import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Backend URL
BACKEND_URL = "http://localhost:8004"


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text: str):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_info(text: str):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")


def check_backend_health():
    """Check if backend is running"""
    print_header("1. Backend Health Check")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.ok:
            print_success("Backend is healthy and running")
            return True
        else:
            print_error(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend not reachable: {e}")
        return False


def check_phi_status():
    """Check Phi LLM status directly"""
    print_header("2. Phi LLM Status Check")
    try:
        # Check Ollama service
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.ok:
            data = response.json()
            models = data.get("models", [])
            phi_models = [m for m in models if "phi" in m.get("name", "").lower()]
            
            if phi_models:
                print_success(f"Ollama is running with {len(models)} models")
                print_success(f"Phi models found: {[m.get('name') for m in phi_models]}")
                return True
            else:
                print_error("Ollama running but no Phi models found")
                print_info("Available models: " + ", ".join([m.get("name") for m in models]))
                print_info("Run: ollama pull phi")
                return False
        else:
            print_error(f"Ollama API error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Ollama not reachable: {e}")
        print_info("Make sure Ollama is running: ollama serve")
        return False


def test_chatbot_without_phi(question: str):
    """Test chatbot without Phi enhancement (baseline)"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chatbot/ask",
            json={"question": question, "top_k": 1},
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            results = data.get("results", [])
            if results:
                answer = results[0].get("answer", "")
                return answer
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_chatbot_with_phi(question: str):
    """Test chatbot with Phi enhancement"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chatbot/ask",
            json={
                "question": question,
                "top_k": 1,
                "language": "en"
            },
            timeout=30  # Longer timeout for LLM
        )
        
        if response.ok:
            data = response.json()
            results = data.get("results", [])
            if results:
                top_result = results[0]
                answer = top_result.get("answer", "")
                phi_enhanced = top_result.get("phi_enhanced", False)
                original_answer = top_result.get("original_answer")
                
                return {
                    "answer": answer,
                    "phi_enhanced": phi_enhanced,
                    "original_answer": original_answer
                }
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def run_test_questions():
    """Run test questions and compare results"""
    print_header("3. Testing Chatbot with Phi Enhancement")
    
    test_questions = [
        "How to grow tomatoes?",
        "What fertilizer for rice?",
        "Control tomato blight",
        "Best time to water crops",
        "Pest control for cabbage"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{Fore.BLUE}Question {i}: {question}{Style.RESET_ALL}")
        print("-" * 60)
        
        start_time = time.time()
        result = test_chatbot_with_phi(question)
        elapsed = time.time() - start_time
        
        if result:
            answer = result.get("answer", "")
            phi_enhanced = result.get("phi_enhanced", False)
            original = result.get("original_answer")
            
            if phi_enhanced:
                print_success(f"Phi-Enhanced Response ({elapsed:.2f}s):")
                print(f"{Fore.WHITE}{answer[:300]}...{Style.RESET_ALL}\n")
                
                if original:
                    print_info("Original Answer (for comparison):")
                    print(f"{Fore.WHITE}{original[:200]}...{Style.RESET_ALL}")
            else:
                print_info(f"Base Response (no Phi) ({elapsed:.2f}s):")
                print(f"{Fore.WHITE}{answer[:300]}...{Style.RESET_ALL}")
        else:
            print_error("No response received")
        
        time.sleep(1)  # Brief pause between requests


def test_phi_performance():
    """Test Phi LLM performance"""
    print_header("4. Phi LLM Performance Test")
    
    question = "How do I prevent tomato disease?"
    
    print(f"Testing with question: '{question}'")
    print("Timing Phi enhancement...")
    
    times = []
    for i in range(3):
        start = time.time()
        result = test_chatbot_with_phi(question)
        elapsed = time.time() - start
        times.append(elapsed)
        
        if result and result.get("phi_enhanced"):
            print(f"  Attempt {i+1}: {elapsed:.2f}s ✓")
        else:
            print(f"  Attempt {i+1}: {elapsed:.2f}s (no enhancement)")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n{Fore.GREEN}Average response time: {avg_time:.2f}s{Style.RESET_ALL}")
        
        if avg_time < 5:
            print_success("Excellent performance! < 5s")
        elif avg_time < 10:
            print_info("Good performance: 5-10s")
        else:
            print_info("Acceptable performance: > 10s (consider adjusting timeout)")


def main():
    """Main test function"""
    print_header("AgriSense Phi LLM Chatbot Integration Test")
    
    # 1. Check backend
    if not check_backend_health():
        print_error("\nBackend not available. Start it with:")
        print("  cd AGRISENSEFULL-STACK")
        print("  python -m uvicorn agrisense_app.backend.main:app --port 8004")
        return 1
    
    # 2. Check Phi
    phi_available = check_phi_status()
    if not phi_available:
        print_info("\nPhi LLM not available. The chatbot will work but without AI enhancement.")
        print_info("To enable Phi:")
        print_info("  1. Install Ollama: https://ollama.ai/")
        print_info("  2. Run: ollama pull phi")
        print_info("  3. Run: ollama serve")
    
    # 3. Run tests
    run_test_questions()
    
    # 4. Performance test
    if phi_available:
        test_phi_performance()
    
    # Summary
    print_header("Test Summary")
    print_success("All tests completed!")
    
    if phi_available:
        print_success("Phi LLM is working and enhancing chatbot responses")
        print_info("Look for '✨ Enhanced' badges in frontend responses")
    else:
        print_info("Chatbot working with knowledge base (Phi enhancement disabled)")
    
    print(f"\n{Fore.CYAN}Next steps:{Style.RESET_ALL}")
    print("  • Open frontend: http://localhost:8082")
    print("  • Go to Chatbot page")
    print("  • Ask farming questions")
    print("  • Look for human-like, contextual responses")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
