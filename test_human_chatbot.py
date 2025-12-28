"""
Test script for human-like chatbot with Phi LLM integration
"""
import requests
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)

BACKEND_URL = "http://localhost:8004"

def test_chatbot(question, language="en"):
    """Test chatbot with a question"""
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"{Fore.CYAN}🧪 Testing Human-Like Chatbot")
    print(f"{Fore.CYAN}{'═' * 60}\n")
    
    print(f"{Fore.WHITE}👤 Question: {Fore.YELLOW}{question}")
    print(f"{Fore.WHITE}Language: {language}\n")
    
    payload = {
        "question": question,
        "language": language,
        "top_k": 3
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/chatbot/ask",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                top_answer = data["results"][0]
                answer_text = top_answer.get("answer", "No answer")
                
                print(f"{Fore.GREEN}{'━' * 60}")
                print(f"{Fore.GREEN}🤖 AgriSense Assistant:")
                print(f"{Fore.GREEN}{'━' * 60}\n")
                
                # Print answer with word wrap
                import textwrap
                wrapped = textwrap.fill(answer_text, width=58)
                print(f"{Fore.WHITE}{wrapped}\n")
                
                print(f"{Fore.GREEN}{'━' * 60}\n")
                
                # Show metadata
                phi_enhanced = top_answer.get("phi_enhanced", False)
                score = top_answer.get("score", 0)
                
                if phi_enhanced:
                    print(f"{Fore.MAGENTA}✨ Enhanced with Phi LLM - Human-like Response!")
                    print(f"{Fore.MAGENTA}   (Response has personality, empathy, and warmth)")
                else:
                    print(f"{Fore.YELLOW}⚡ Standard Response")
                    print(f"{Fore.YELLOW}   (Phi LLM not available or enhancement skipped)")
                
                print(f"\n{Fore.CYAN}ℹ️  Details:")
                print(f"{Fore.WHITE}  • Confidence: {score:.3f}")
                print(f"{Fore.WHITE}  • Response Time: {elapsed:.2f}s")
                print(f"{Fore.WHITE}  • Enhanced: {phi_enhanced}")
                print(f"{Fore.WHITE}  • Language: {language}")
                
                # Show comparison if available
                if top_answer.get("original_answer") and phi_enhanced:
                    print(f"\n{Fore.CYAN}📊 Transformation:")
                    orig = top_answer["original_answer"]
                    print(f"{Fore.WHITE}  • Original: {len(orig)} chars")
                    print(f"{Fore.WHITE}  • Enhanced: {len(answer_text)} chars")
                    print(f"{Fore.WHITE}  • Improvement: +{len(answer_text) - len(orig)} chars")
            else:
                print(f"{Fore.RED}❌ No results returned")
        else:
            print(f"{Fore.RED}❌ Error: HTTP {response.status_code}")
            print(f"{Fore.RED}   {response.text}")
    
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}❌ Request timed out after 30s")
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Could not connect to backend at {BACKEND_URL}")
        print(f"{Fore.YELLOW}   Make sure the backend is running on port 8004")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}")


def main():
    """Run chatbot tests"""
    print(f"\n{Fore.MAGENTA}{'═' * 60}")
    print(f"{Fore.MAGENTA}🌾 AgriSense Human-Like Chatbot Test Suite")
    print(f"{Fore.MAGENTA}{'═' * 60}")
    
    # Test questions
    questions = [
        ("How do I grow tomatoes?", "en"),
        ("What's the best fertilizer for rice?", "en"),
        ("My wheat plants have yellow leaves, what should I do?", "en"),
        ("When is the best time to plant corn?", "en"),
    ]
    
    for i, (question, lang) in enumerate(questions, 1):
        print(f"\n{Fore.CYAN}[Test {i}/{len(questions)}]")
        test_chatbot(question, lang)
        
        if i < len(questions):
            print(f"\n{Fore.WHITE}{'─' * 60}")
            time.sleep(2)  # Brief pause between tests
    
    print(f"\n{Fore.MAGENTA}{'═' * 60}")
    print(f"{Fore.GREEN}✅ All tests completed!")
    print(f"{Fore.MAGENTA}{'═' * 60}\n")
    
    print(f"{Fore.CYAN}💡 Tips:")
    print(f"{Fore.WHITE}  • Look for the ✨ Enhanced badge for Phi-powered responses")
    print(f"{Fore.WHITE}  • Human-like responses have personality and empathy")
    print(f"{Fore.WHITE}  • Test in the web UI at: http://127.0.0.1:8081")
    print()


if __name__ == "__main__":
    main()
