"""
Enhanced Conversational Chatbot Service for AgriSense
Makes the chatbot more human-like and farmer-friendly with:
- Conversational greetings and context
- Empathetic language
- Follow-up suggestions
- Multi-turn conversation memory
- Regional farming context awareness
"""

import logging
import os
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Conversation memory (session-based)
_conversation_memory: Dict[str, List[Dict[str, Any]]] = OrderedDict()
_MAX_MEMORY_SIZE = 100  # Max sessions to remember
_MAX_HISTORY_PER_SESSION = 10  # Max messages per session


class ConversationalEnhancer:
    """Enhances chatbot responses to be more conversational and farmer-friendly"""
    
    def __init__(self, language: str = "en"):
        self.language = language
        self.conversation_starters = self._load_conversation_starters()
        self.empathy_phrases = self._load_empathy_phrases()
        self.follow_up_templates = self._load_follow_up_templates()
        self.regional_context = self._load_regional_context()
    
    def _load_conversation_starters(self) -> Dict[str, List[str]]:
        """Load greeting and conversation starter phrases"""
        return {
            "en": [
                "Hello! I'm here to help with your farming questions. 😊",
                "Namaste! Happy to assist you with agriculture advice today!",
                "Hi there, farmer friend! What can I help you with?",
                "Greetings! I'm your agriculture assistant. How may I help?",
                "Good day! Ready to answer your farming questions!",
            ],
            "hi": [
                "नमस्ते! मैं आपके खेती के सवालों में मदद करने के लिए यहाँ हूँ। 😊",
                "नमस्कार! आज मैं आपकी कृषि सलाह में सहायता करने को तैयार हूँ!",
                "हैलो किसान भाई! मैं आपकी क्या मदद कर सकता हूँ?",
            ],
            "ta": [
                "வணக்கம்! உங்கள் விவசாய கேள்விகளுக்கு உதவ நான் இங்கே இருக்கிறேன். 😊",
                "வணக்கம் விவசாயி நண்பரே! நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
            ],
            "te": [
                "నమస్కారం! మీ వ్యవసాయ ప్రశ్నలకు సహాయం చేయడానికి నేను ఇక్కడ ఉన్నాను। 😊",
                "హలో రైతు మిత్రమా! నేను మీకు ఎలా సహాయం చేయగలను?",
            ],
            "kn": [
                "ನಮಸ್ಕಾರ! ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳಿಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ। 😊",
                "ಹಲೋ ರೈತ ಸ್ನೇಹಿತ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
            ],
        }
    
    def _load_empathy_phrases(self) -> Dict[str, Dict[str, List[str]]]:
        """Load empathetic phrases for different question types"""
        return {
            "en": {
                "problem": [
                    "I understand that can be concerning.",
                    "I can see why you're worried about that.",
                    "That's a common challenge many farmers face.",
                    "Don't worry, let me help you with this.",
                ],
                "success": [
                    "That's great to hear!",
                    "Wonderful! Keep up the good work!",
                    "Excellent question!",
                ],
                "question": [
                    "That's a very good question!",
                    "I'm glad you asked that!",
                    "Let me help you with that.",
                    "Here's what I know about this:",
                ],
            },
            "hi": {
                "problem": [
                    "मैं समझता हूँ कि यह चिंता का विषय हो सकता है।",
                    "यह कई किसानों के सामने आने वाली आम समस्या है।",
                    "चिंता न करें, मैं इसमें आपकी मदद करूंगा।",
                ],
                "question": [
                    "यह बहुत अच्छा सवाल है!",
                    "मुझे खुशी है कि आपने यह पूछा!",
                    "आइए मैं इसमें आपकी मदद करता हूँ।",
                ],
            },
            "ta": {
                "problem": [
                    "இது பலர் எதிர்கொள்ளும் பொதுவான சவால்.",
                    "கவலைப்பட வேண்டாம், இதில் நான் உங்களுக்கு உதவுகிறேன்.",
                ],
                "question": [
                    "இது மிகவும் நல்ல கேள்வி!",
                    "இதில் நான் உங்களுக்கு உதவுகிறேன்.",
                ],
            },
            "te": {
                "problem": [
                    "ఇది చాలా మంది రైతులు ఎదుర్కొనే సాధారణ సవాలు.",
                    "చింతించకండి, దీనిలో నేను మీకు సహాయం చేస్తాను.",
                ],
                "question": [
                    "ఇది చాలా మంచి ప్రశ్న!",
                    "ఇందులో నేను మీకు సహాయం చేస్తాను.",
                ],
            },
            "kn": {
                "problem": [
                    "ಇದು ಅನೇಕ ರೈತರು ಎದುರಿಸುವ ಸಾಮಾನ್ಯ ಸವಾಲು.",
                    "ಚಿಂತಿಸಬೇಡಿ, ಇದರಲ್ಲಿ ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
                ],
                "question": [
                    "ಇದು ಉತ್ತಮ ಪ್ರಶ್ನೆ!",
                    "ಇದರಲ್ಲಿ ನಾನು ನಿಮಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
                ],
            },
        }
    
    def _load_follow_up_templates(self) -> Dict[str, List[str]]:
        """Load follow-up question templates"""
        return {
            "en": [
                "\n\n💡 You might also want to know:",
                "\n\n🌱 Related tips:",
                "\n\n📌 Keep in mind:",
                "\n\n✨ Pro tip:",
                "\n\n🤔 Need to know more? Feel free to ask about:",
            ],
            "hi": [
                "\n\n💡 आप यह भी जानना चाह सकते हैं:",
                "\n\n🌱 संबंधित सुझाव:",
                "\n\n📌 ध्यान रखें:",
                "\n\n✨ विशेष सुझाव:",
            ],
            "ta": [
                "\n\n💡 நீங்கள் இதையும் அறிய விரும்பலாம்:",
                "\n\n🌱 தொடர்புடைய குறிப்புகள்:",
                "\n\n📌 நினைவில் கொள்ளுங்கள்:",
            ],
            "te": [
                "\n\n💡 మీరు దీన్ని కూడా తెలుసుకోవాలనుకోవచ్చు:",
                "\n\n🌱 సంబంధిత చిట్కాలు:",
                "\n\n📌 గుర్తుంచుకోండి:",
            ],
            "kn": [
                "\n\n💡 ನೀವು ಇದನ್ನು ಸಹ ತಿಳಿಯಲು ಬಯಸಬಹುದು:",
                "\n\n🌱 ಸಂಬಂಧಿತ ಸುಳಿವುಗಳು:",
                "\n\n📌 ನೆನಪಿಡಿ:",
            ],
        }
    
    def _load_regional_context(self) -> Dict[str, str]:
        """Load regional farming context"""
        return {
            "monsoon": "Remember to adjust practices based on monsoon patterns in your region.",
            "season": "Farming practices vary by season and region.",
            "local": "Always consult with local agricultural extension services for region-specific advice.",
        }
    
    def detect_question_intent(self, question: str) -> str:
        """Detect the intent of the question"""
        question_lower = question.lower()
        
        # Problem/concern keywords
        problem_keywords = ["disease", "pest", "problem", "issue", "dying", "yellow", "wilting", 
                           "not growing", "damage", "infected", "sick", "failing"]
        if any(keyword in question_lower for keyword in problem_keywords):
            return "problem"
        
        # Success/positive keywords
        success_keywords = ["good", "great", "thank", "success", "working", "growing well"]
        if any(keyword in question_lower for keyword in success_keywords):
            return "success"
        
        return "question"
    
    def enhance_response(
        self, 
        question: str, 
        base_answer: str, 
        session_id: Optional[str] = None,
        is_greeting: bool = False
    ) -> str:
        """
        Enhance a base answer to be more conversational and farmer-friendly
        
        Args:
            question: The user's question
            base_answer: The retrieved answer from the knowledge base
            session_id: Optional session ID for conversation tracking
            is_greeting: Whether this is a greeting message
            
        Returns:
            Enhanced, conversational response
        """
        lang = self.language
        
        # Handle greetings
        if is_greeting or self._is_greeting(question):
            greeting = random.choice(self.conversation_starters.get(lang, self.conversation_starters["en"]))
            if base_answer:
                return f"{greeting}\n\n{base_answer}"
            return greeting
        
        # Detect question intent
        intent = self.detect_question_intent(question)
        
        # Add empathetic opening
        opening = ""
        if lang in self.empathy_phrases and intent in self.empathy_phrases[lang]:
            opening = random.choice(self.empathy_phrases[lang][intent]) + "\n\n"
        
        # Clean and enhance the base answer
        enhanced_answer = self._humanize_answer(base_answer, lang)
        
        # Add regional context if relevant
        contextual_note = self._add_context(question, lang)
        
        # Add follow-up suggestions
        follow_up = self._generate_follow_up(question, lang)
        
        # Assemble the complete response
        parts = [opening, enhanced_answer]
        
        if contextual_note:
            parts.append(f"\n\n{contextual_note}")
        
        if follow_up:
            parts.append(follow_up)
        
        # Add encouraging closing
        closing = self._get_closing_phrase(lang)
        if closing:
            parts.append(f"\n\n{closing}")
        
        response = "".join(parts)
        
        # Store in conversation memory
        if session_id:
            self._add_to_memory(session_id, question, response)
        
        return response
    
    def _is_greeting(self, text: str) -> bool:
        """Check if text is a greeting"""
        greetings = [
            "hello", "hi", "hey", "namaste", "namaskar", "vanakkam", "నమస్కారం", "ನಮಸ್ಕಾರ",
            "good morning", "good afternoon", "good evening", "greetings"
        ]
        text_lower = text.lower().strip()
        return any(greeting in text_lower for greeting in greetings) or len(text.split()) <= 2
    
    def _humanize_answer(self, answer: str, lang: str) -> str:
        """Make the answer sound more human and conversational"""
        if not answer:
            return answer
        
        # Remove excessive technical jargon explanations (keep it simple)
        answer = re.sub(r'\s+', ' ', answer).strip()
        
        # Add conversational markers
        conversational_starters = {
            "en": ["Well, ", "You see, ", "Here's the thing: ", "Actually, ", "Let me explain: "],
            "hi": ["देखिए, ", "वास्तव में, ", "बात यह है: "],
            "ta": ["பார்க்கலாம், ", "உண்மையில், "],
            "te": ["చూడండి, ", "వాస్తవానికి, "],
            "kn": ["ನೋಡಿ, ", "ವಾಸ್ತವವಾಗಿ, "],
        }
        
        # Sometimes add a conversational starter (30% of the time)
        if random.random() < 0.3 and lang in conversational_starters:
            starter = random.choice(conversational_starters[lang])
            if not answer.startswith(tuple(conversational_starters[lang])):
                answer = starter + answer[0].lower() + answer[1:] if len(answer) > 1 else answer
        
        return answer
    
    def _add_context(self, question: str, lang: str) -> str:
        """Add relevant contextual notes"""
        question_lower = question.lower()
        
        context_phrases = {
            "en": {
                "season": "🌦️ Note: The timing may vary based on your local climate and season.",
                "region": "🗺️ Remember: This advice is general. Check with local experts for your specific region.",
                "weather": "☀️ Always consider current weather patterns in your area.",
            },
            "hi": {
                "season": "🌦️ नोट: समय आपकी स्थानीय जलवायु और मौसम के आधार पर भिन्न हो सकता है।",
                "region": "🗺️ याद रखें: यह सामान्य सलाह है। अपने क्षेत्र के लिए स्थानीय विशेषज्ञों से परामर्श लें।",
            },
            "ta": {
                "season": "🌦️ குறிப்பு: நேரம் உங்கள் உள்ளூர் காலநிலை மற்றும் பருவத்தைப் பொறுத்து மாறுபடும்.",
                "region": "🗺️ நினைவில் கொள்ளுங்கள்: இது பொதுவான ஆலோசனை. உங்கள் பகுதிக்கு உள்ளூர் நிபுணர்களை சந்திக்கவும்.",
            },
            "te": {
                "season": "🌦️ గమనిక: సమయం మీ స్థానిక వాతావరణం మరియు సీజన్ ఆధారంగా మారుతుంది.",
                "region": "🗺️ గుర్తుంచుకోండి: ఇది సాధారణ సలహా. మీ ప్రాంతానికి స్థానిక నిపుణులను సంప్రదించండి.",
            },
            "kn": {
                "season": "🌦️ ಸೂಚನೆ: ಸಮಯವು ನಿಮ್ಮ ಸ್ಥಳೀಯ ಹವಾಮಾನ ಮತ್ತು ಋತುವನ್ನು ಆಧರಿಸಿ ಬದಲಾಗಬಹುದು.",
                "region": "🗺️ ನೆನಪಿಡಿ: ಇದು ಸಾಮಾನ್ಯ ಸಲಹೆ. ನಿಮ್ಮ ಪ್ರದೇಶಕ್ಕೆ ಸ್ಥಳೀಯ ತಜ್ಞರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
            },
        }
        
        # Check for season/time-related questions
        if any(word in question_lower for word in ["when", "time", "season", "month", "कब", "எப்போது", "ఎప్పుడు", "ಯಾವಾಗ"]):
            return context_phrases.get(lang, context_phrases["en"]).get("season", "")
        
        # Check for location/region-related questions
        if any(word in question_lower for word in ["where", "region", "area", "कहाँ", "எங்கே", "ఎక్కడ", "ಎಲ್ಲಿ"]):
            return context_phrases.get(lang, context_phrases["en"]).get("region", "")
        
        return ""
    
    def _generate_follow_up(self, question: str, lang: str) -> str:
        """Generate follow-up suggestions based on the question"""
        question_lower = question.lower()
        
        follow_ups = {
            "en": {
                "water": ["optimal watering schedule", "signs of overwatering", "irrigation methods"],
                "fertilizer": ["organic vs chemical fertilizers", "when to apply fertilizer", "soil testing"],
                "pest": ["natural pest control methods", "identifying pest damage", "preventive measures"],
                "disease": ["disease prevention tips", "organic fungicides", "crop rotation benefits"],
                "crop": ["best crops for your soil", "crop rotation planning", "harvest timing"],
            },
            "hi": {
                "water": ["सिंचाई का सही समय", "अधिक पानी के लक्षण"],
                "fertilizer": ["जैविक बनाम रासायनिक उर्वरक", "उर्वरक कब डालें"],
                "pest": ["प्राकृतिक कीट नियंत्रण", "रोकथाम के उपाय"],
            },
            "ta": {
                "water": ["நீர்ப்பாசன அட்டவணை", "அதிக தண்ணீரின் அறிகுறிகள்"],
                "fertilizer": ["இயற்கை உரங்கள்", "உரம் இடும் நேரம்"],
            },
            "te": {
                "water": ["నీటి పారుదల షెడ్యూల్", "ఎక్కువ నీరు యొక్క సంకేతాలు"],
                "fertilizer": ["సేంద్రీయ ఎరువులు", "ఎరువులు వేసే సమయం"],
            },
            "kn": {
                "water": ["ನೀರಾವರಿ ವೇಳಾಪಟ್ಟಿ", "ಹೆಚ್ಚು ನೀರಿನ ಲಕ್ಷಣಗಳು"],
                "fertilizer": ["ಸಾವಯವ ಗೊಬ್ಬರಗಳು", "ಗೊಬ್ಬರ ಹಾಕುವ ಸಮಯ"],
            },
        }
        
        # Detect topic
        topic = None
        for key in ["water", "fertilizer", "pest", "disease", "crop"]:
            if key in question_lower or key in question_lower.replace("ing", ""):
                topic = key
                break
        
        if not topic or lang not in follow_ups or topic not in follow_ups[lang]:
            return ""
        
        suggestions = follow_ups[lang][topic]
        if not suggestions:
            return ""
        
        intro = random.choice(self.follow_up_templates.get(lang, self.follow_up_templates["en"]))
        follow_up_list = "\n• " + "\n• ".join(suggestions[:2])  # Limit to 2 suggestions
        
        return f"{intro}{follow_up_list}"
    
    def _get_closing_phrase(self, lang: str) -> str:
        """Get a friendly closing phrase"""
        closings = {
            "en": [
                "Feel free to ask if you need more help! 🌾",
                "Happy farming! 🌱",
                "Hope this helps! Let me know if you have more questions.",
                "Good luck with your crops! 🌻",
                "May your harvest be bountiful! 🌾",
            ],
            "hi": [
                "और मदद चाहिए तो बेझिझक पूछें! 🌾",
                "शुभ खेती! 🌱",
                "आशा है यह मदद करेगा!",
            ],
            "ta": [
                "மேலும் உதவி தேவைப்பட்டால் கேளுங்கள்! 🌾",
                "இனிய விவசாயம்! 🌱",
            ],
            "te": [
                "మరింత సహాయం కావాలంటే అడగండి! 🌾",
                "శుభ వ్యవసాయం! 🌱",
            ],
            "kn": [
                "ಹೆಚ್ಚಿನ ಸಹಾಯ ಬೇಕಾದರೆ ಕೇಳಿ! 🌾",
                "ಶುಭ ಕೃಷಿ! 🌱",
            ],
        }
        
        # Return closing 70% of the time
        if random.random() < 0.7:
            return random.choice(closings.get(lang, closings["en"]))
        return ""
    
    def _add_to_memory(self, session_id: str, question: str, response: str):
        """Add conversation to memory"""
        global _conversation_memory
        
        if session_id not in _conversation_memory:
            _conversation_memory[session_id] = []
        
        _conversation_memory[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
        })
        
        # Keep only last N messages per session
        if len(_conversation_memory[session_id]) > _MAX_HISTORY_PER_SESSION:
            _conversation_memory[session_id] = _conversation_memory[session_id][-_MAX_HISTORY_PER_SESSION:]
        
        # Limit total number of sessions
        if len(_conversation_memory) > _MAX_MEMORY_SIZE:
            _conversation_memory.popitem(last=False)
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return _conversation_memory.get(session_id, [])
    
    def clear_session(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in _conversation_memory:
            del _conversation_memory[session_id]


def enhance_chatbot_response(
    question: str,
    base_answer: str,
    session_id: Optional[str] = None,
    language: str = "en",
) -> str:
    """
    Main function to enhance chatbot responses
    
    Args:
        question: User's question
        base_answer: Retrieved answer from knowledge base
        session_id: Optional session ID for tracking
        language: Language code (en, hi, ta, te, kn)
    
    Returns:
        Enhanced conversational response
    """
    try:
        enhancer = ConversationalEnhancer(language=language)
        return enhancer.enhance_response(question, base_answer, session_id)
    except Exception as e:
        logger.error(f"Error enhancing response: {e}", exc_info=True)
        # Fallback to base answer
        return base_answer


def get_greeting_message(language: str = "en") -> str:
    """Get a greeting message in the specified language"""
    enhancer = ConversationalEnhancer(language=language)
    return random.choice(enhancer.conversation_starters.get(language, enhancer.conversation_starters["en"]))
