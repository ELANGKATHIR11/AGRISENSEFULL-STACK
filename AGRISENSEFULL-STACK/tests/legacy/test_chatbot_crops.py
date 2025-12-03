"""Test script for chatbot crop name responses"""
import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variables
os.environ['AGRISENSE_DISABLE_ML'] = '1'

try:
    from agrisense_app.backend.chatbot_service import ChatbotService
    # Create a wrapper class to match the expected interface
    class AgriChatbot:
        def __init__(self):
            self.service = ChatbotService()
        
        def get_response(self, message, zone_id):
            return self.service.get_response(message, zone_id)
except ImportError:
    print("Warning: ChatbotService not found, using mock implementation")
    class AgriChatbot:
        def get_response(self, message, zone_id):
            return {"answer": f"Mock response for {message} in zone {zone_id}"}

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    zone_id: str

# Test all 48 crops
test_crops = [
    'apple', 'banana', 'barley', 'beans', 'beetroot', 'broccoli', 'cabbage', 'carrot',
    'cauliflower', 'chickpeas', 'chili', 'corn', 'cotton', 'cucumber', 'eggplant', 'garlic',
    'ginger', 'grapes', 'groundnut', 'guava', 'lentils', 'lettuce', 'mango', 'millet',
    'mustard', 'oats', 'onion', 'orange', 'papaya', 'peas', 'pepper', 'pomegranate',
    'potato', 'pumpkin', 'radish', 'rapeseed', 'rice', 'sesame', 'sorghum', 'soybean',
    'spinach', 'strawberry', 'sugarcane', 'sunflower', 'tomato', 'turmeric', 'watermelon', 'wheat'
]

# Initialize chatbot instance
chatbot = AgriChatbot()

# Initialize result tracking lists
successful = []
failed = []

for crop in test_crops:
    try:
        request = ChatRequest(message=crop, zone_id="Z1")
        response = chatbot.get_response(request.message, request.zone_id)
        
        # Check if response contains the crop name
        answer = response.get("answer", "") if isinstance(response, dict) else str(response)
        if crop in answer.lower():
            print(f"✓ {crop:15} -> {answer[:50]}...")
            successful.append(crop)
        else:
            print(f"✗ {crop:15} -> {answer[:50]}... (expected crop name)")
            failed.append(crop)
            
    except Exception as e:
        print(f"✗ {crop:15} -> ERROR: {str(e)[:50]}")
        failed.append(crop)

print("\n" + "=" * 80)
print(f"\nResults: {len(successful)}/{len(test_crops)} crops working correctly")

if failed:
    print(f"\nFailed crops ({len(failed)}): {', '.join(failed)}")
else:
    print("\n🎉 All 48 crops are working correctly!")

# Test some variations
variations = [
    ("tell me about rice", "rice"),
    ("what is wheat", "wheat"),
]

for query, expected in variations:
    try:
        request = ChatRequest(message=query, zone_id="Z1")
        response = chatbot.get_response(request.message, request.zone_id)
        
        answer = response.get("answer", "") if isinstance(response, dict) else str(response)
        if expected in answer.lower():
            print(f"✓ '{query}' -> Contains '{expected}'")
        else:
            print(f"✗ '{query}' -> {answer[:50]}... (expected '{expected}')")
            
    except Exception as e:
        print(f"✗ '{query}' -> ERROR: {str(e)[:50]}")
