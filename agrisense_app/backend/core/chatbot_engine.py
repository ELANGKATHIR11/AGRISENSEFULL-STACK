"""
Context-Aware Agricultural Chatbot
Acts as a Senior Agronomist providing empathetic, professional advice
"""

import os
import json
import logging
from typing import Dict, Optional
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgriAdvisorBot:
    """
    Context-aware chatbot that acts as a Senior Agronomist.
    Provides empathetic, professional advice based on VLM diagnosis.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chatbot with Google Gemini API.
        
        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set or api_key not provided")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 1.5 Flash for conversational responses
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Base system prompt for persona
        self.base_persona = """You are Dr. Priya Kumar, a Senior Agronomist with 25 years of field experience in sustainable farming practices across Asia and Africa.

YOUR PERSONALITY:
- Empathetic: You understand farmers' concerns and financial constraints
- Encouraging: You offer hope while being realistic
- Scientific: Your advice is evidence-based but explained in simple terms
- Patient: You never dismiss questions as trivial
- Practical: You focus on actionable, affordable solutions

YOUR EXPERTISE:
- Integrated Pest Management (IPM)
- Organic and conventional farming methods
- Crop disease diagnosis and treatment
- Soil health and nutrition
- Water management and irrigation

COMMUNICATION STYLE:
- Use first-person perspective ("I recommend...", "In my experience...")
- Reference specific details from the diagnosis context
- Acknowledge the farmer's emotional state (worry, confusion, urgency)
- Provide cost estimates when discussing treatments
- Offer both immediate actions and long-term prevention
- Use analogies to explain complex concepts
- End with encouragement and next steps

CRITICAL RULES:
1. ALWAYS reference specific details from the diagnosis context (crop type, disease name, severity)
2. If confidence is <70%, advise caution and suggest getting a second opinion or physical inspection
3. If severity is High, emphasize urgency but avoid panic
4. Never give generic advice - tailor everything to the specific situation
5. If asked about costs, provide realistic price ranges in USD
6. If no diagnosis context is provided, ask clarifying questions

EXAMPLE INTERACTIONS:

Context: {"crop_detected": "Tomato", "status": "Diseased", "disease_name": "Early Blight", "confidence": 88.3, "severity": "Medium"}
User: "Is this bad? Will I lose my crop?"
Response: "I understand your concern - seeing those brown spots on your tomato plants can be worrying. The good news is we've identified this as Early Blight with about 88% certainty, and you've caught it at a Medium severity level. That means we can definitely manage this!

Early Blight is very common and treatable. You won't lose your entire crop if we act now. I recommend starting with an organic approach first - a simple baking soda solution (1 tablespoon per gallon of water) sprayed every 5-7 days can work wonders and costs less than $5. 

Remove the affected lower leaves to improve air circulation. If the organic method doesn't show improvement in 2 weeks, we can escalate to a copper fungicide (around $15-20).

Most importantly, don't panic. I've seen hundreds of tomato farmers successfully manage Early Blight. You've got this!"

Context: {"crop_detected": "Rice", "status": "Diseased", "disease_name": "Bacterial Leaf Blight", "confidence": 65.2, "severity": "High"}
User: "What should I do?"
Response: "I can see you're dealing with what appears to be Bacterial Leaf Blight in your rice field, and the severity looks High. However, I want to be transparent - my confidence in this diagnosis is about 65%, which is moderate.

Given the High severity AND the uncertainty, I strongly recommend:

1. IMMEDIATE: Get a physical inspection by a local agricultural extension officer or plant pathologist. Bacterial diseases in rice can spread rapidly, and we need to be absolutely certain before treatment.

2. MEANWHILE: Isolate the affected area if possible to prevent spread. Avoid overhead irrigation which can spread bacteria.

3. IF CONFIRMED: Bacterial Leaf Blight requires aggressive management - you'll need a copper-based bactericide (around $30-40 per acre) and may need to remove severely infected plants.

I don't want to alarm you, but bacterial diseases require quick, accurate action. The good news is that if we act in the next 2-3 days, you can still save a significant portion of your crop. Please reach out to local experts and keep me updated!"

Now, respond to the farmer's question using the diagnosis context provided."""

        logger.info("AgriAdvisorBot initialized with empathetic agronomist persona")

    def get_advice(self, user_query: str, diagnosis_context: Optional[Dict] = None) -> str:
        """
        Provide context-aware agricultural advice.
        
        Args:
            user_query: The farmer's question or concern
            diagnosis_context: The JSON output from CropDiseaseDetector.analyze_image()
            
        Returns:
            str: Empathetic, professional advice tailored to the specific situation
        """
        try:
            # Build the context-aware prompt
            if diagnosis_context:
                context_str = json.dumps(diagnosis_context, indent=2)
                full_prompt = f"""{self.base_persona}

CURRENT DIAGNOSIS CONTEXT:
{context_str}

FARMER'S QUESTION:
"{user_query}"

Your response (remember to reference specific details from the diagnosis):"""
            else:
                full_prompt = f"""{self.base_persona}

NO DIAGNOSIS CONTEXT PROVIDED - Ask clarifying questions about their crop issue.

FARMER'S QUESTION:
"{user_query}"

Your response:"""

            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # Higher temperature for natural conversation
                    top_p=0.9,
                    top_k=50,
                    max_output_tokens=800,
                )
            )
            
            advice = response.text.strip()
            
            # Log interaction
            logger.info(f"Chatbot response generated for query: '{user_query[:50]}...'")
            logger.debug(f"Full response: {advice}")
            
            return advice
            
        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}")
            return self._fallback_response(user_query, diagnosis_context)

    def _fallback_response(self, user_query: str, diagnosis_context: Optional[Dict]) -> str:
        """
        Generate a fallback response if API fails.
        
        Args:
            user_query: User's question
            diagnosis_context: Diagnosis data
            
        Returns:
            str: Basic response based on context
        """
        if not diagnosis_context:
            return ("I apologize, but I'm having technical difficulties accessing my knowledge base right now. "
                    "Could you please describe your crop issue in detail? Include the crop type, symptoms you're seeing, "
                    "and how long this has been happening.")
        
        crop = diagnosis_context.get("crop_detected", "your crop")
        status = diagnosis_context.get("status", "Unknown")
        disease = diagnosis_context.get("disease_name")
        severity = diagnosis_context.get("severity", "Unknown")
        confidence = diagnosis_context.get("confidence", 0)
        
        if status == "Healthy":
            return f"Good news! Your {crop} appears to be healthy. Continue your current care routine and monitor regularly."
        
        elif status == "Diseased" and disease:
            response = f"I can see your {crop} is showing signs of {disease} with {severity} severity (confidence: {confidence:.1f}%).\n\n"
            
            if confidence < 70:
                response += "However, my confidence is moderate, so I recommend getting a physical inspection by a local expert.\n\n"
            
            # Add basic recommendations from context
            recs = diagnosis_context.get("recommendations", {})
            if recs.get("organic_cure"):
                response += f"Organic treatments to try: {', '.join(recs['organic_cure'][:2])}\n\n"
            
            if severity == "High":
                response += "⚠️ Given the high severity, please act quickly. Consider consulting a local agricultural extension officer."
            else:
                response += "With prompt action, you can manage this effectively. Don't worry!"
            
            return response
        
        else:
            return f"I detected your crop as {crop} with status: {status}. Could you provide more details about what you're observing?"

    def get_multi_turn_advice(self, conversation_history: list, diagnosis_context: Optional[Dict] = None) -> str:
        """
        Handle multi-turn conversations with context retention.
        
        Args:
            conversation_history: List of {"role": "user/bot", "message": str} dicts
            diagnosis_context: The diagnosis data to maintain context
            
        Returns:
            str: Contextual response considering conversation history
        """
        try:
            # Build conversation context
            conversation_str = "\n".join([
                f"{'FARMER' if msg['role'] == 'user' else 'YOU'}: {msg['message']}"
                for msg in conversation_history
            ])
            
            context_str = json.dumps(diagnosis_context, indent=2) if diagnosis_context else "No diagnosis available"
            
            prompt = f"""{self.base_persona}

DIAGNOSIS CONTEXT:
{context_str}

CONVERSATION HISTORY:
{conversation_str}

Continue the conversation naturally, referencing previous exchanges and the diagnosis context:"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    max_output_tokens=800,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Multi-turn conversation error: {str(e)}")
            return "I apologize, but I'm having trouble maintaining our conversation context. Could you restate your question?"


# Singleton instance for dependency injection
_chatbot_instance: Optional[AgriAdvisorBot] = None


def get_chatbot_engine() -> AgriAdvisorBot:
    """
    Get or create singleton chatbot engine instance.
    
    Returns:
        AgriAdvisorBot: Initialized chatbot
    """
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = AgriAdvisorBot()
    return _chatbot_instance
