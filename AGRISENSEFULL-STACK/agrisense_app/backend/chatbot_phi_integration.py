"""
Phi LLM Integration for Agricultural Chatbot
=============================================

Integrates Ollama Phi LLM to enhance the chatbot with:
- Natural conversational responses
- Agriculture-specific fine-tuning through prompt engineering
- Context-aware answers based on farming knowledge
- Multi-turn conversation support
- Fallback to knowledge base when LLM unavailable

Usage:
------
    from chatbot_phi_integration import PhiAgriChatbot
    
    chatbot = PhiAgriChatbot()
    response = chatbot.ask(
        question="How do I treat tomato blight?",
        context={"crop": "tomato", "season": "monsoon"}
    )
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class PhiConfig:
    """Configuration for Phi LLM"""
    endpoint: str = "http://localhost:11434"
    model: str = "phi:latest"
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9


class PhiAgriChatbot:
    """
    Agricultural Chatbot powered by Ollama Phi LLM
    
    Features:
    - Agriculture-specific prompt engineering
    - Context-aware responses
    - Multi-turn conversations
    - Fallback mechanisms
    - Knowledge base integration
    """
    
    # Agriculture-specific system prompt
    AGRI_SYSTEM_PROMPT = """You are an expert agricultural advisor with deep knowledge of farming, crop management, pest control, soil health, irrigation, and sustainable agriculture practices.

Your role is to:
1. Provide practical, actionable farming advice
2. Use simple language that farmers can understand
3. Consider regional and seasonal factors
4. Prioritize sustainable and cost-effective solutions
5. Include specific measurements, timings, and dosages when relevant
6. Warn about safety concerns when handling chemicals or equipment

Guidelines:
- Keep responses concise (2-4 sentences for simple queries, longer for complex ones)
- Use metric units (liters, grams, hectares)
- Include approximate costs when relevant
- Suggest alternatives when possible
- Acknowledge uncertainty instead of guessing
- Focus on Indian agriculture context unless specified otherwise

Tone: Friendly, professional, and empathetic to farmers' challenges."""

    CROP_SPECIFIC_PROMPTS = {
        "rice": "Rice cultivation context: Consider water management, proper puddling, spacing (15x15 cm), fertilizer split application (NPK 120:60:40), and common pests like stem borer and leaf folder.",
        "wheat": "Wheat cultivation context: Consider sowing time (November), seed rate (100 kg/ha), irrigation at critical stages, and diseases like rust and bunt.",
        "tomato": "Tomato cultivation context: Consider transplanting, staking, regular pesticide sprays, drip irrigation, and diseases like early blight and late blight.",
        "potato": "Potato cultivation context: Consider seed treatment, earthing up, blight management, and proper storage.",
        "cotton": "Cotton cultivation context: Consider bollworm management, pink bollworm, proper spacing, and integrated pest management.",
    }
    
    def __init__(self, config: Optional[PhiConfig] = None, knowledge_base: Optional[Dict] = None):
        """
        Initialize Phi agricultural chatbot
        
        Args:
            config: Phi LLM configuration
            knowledge_base: Optional knowledge base for fallback
        """
        self.config = config or PhiConfig()
        self.knowledge_base = knowledge_base or {}
        self.conversation_history: List[Dict] = []
        self.max_history = 5  # Keep last 5 exchanges
        
        # Check Phi availability
        self._phi_available = self._check_phi_available()
        if self._phi_available:
            logger.info(f"✅ Phi LLM available at {self.config.endpoint}")
        else:
            logger.warning(f"⚠️ Phi LLM not available at {self.config.endpoint} - using fallback mode")
    
    def _check_phi_available(self) -> bool:
        """Check if Phi LLM is available"""
        try:
            response = requests.get(
                f"{self.config.endpoint}/api/tags",
                timeout=5
            )
            if response.ok:
                data = response.json()
                models = data.get("models", [])
                # Check if phi model exists
                for model in models:
                    if "phi" in model.get("name", "").lower():
                        return True
            return False
        except Exception as e:
            logger.debug(f"Phi availability check failed: {e}")
            return False
    
    def _build_agricultural_prompt(self, question: str, context: Optional[Dict] = None) -> str:
        """
        Build agriculture-specific prompt for Phi LLM
        
        Args:
            question: User's question
            context: Optional context (crop type, location, season, etc.)
            
        Returns:
            Formatted prompt string
        """
        # Start with system prompt
        prompt_parts = [self.AGRI_SYSTEM_PROMPT]
        
        # Add context if available
        if context:
            context_str = "Current context:\n"
            if "crop" in context:
                crop = context["crop"].lower()
                context_str += f"- Crop: {context['crop']}\n"
                # Add crop-specific guidance
                if crop in self.CROP_SPECIFIC_PROMPTS:
                    prompt_parts.append(self.CROP_SPECIFIC_PROMPTS[crop])
            
            if "season" in context:
                context_str += f"- Season: {context['season']}\n"
            
            if "location" in context:
                context_str += f"- Location: {context['location']}\n"
            
            if "soil_type" in context:
                context_str += f"- Soil type: {context['soil_type']}\n"
            
            prompt_parts.append(context_str)
        
        # Add conversation history
        if self.conversation_history:
            history_str = "\nRecent conversation:\n"
            for exchange in self.conversation_history[-3:]:  # Last 3 exchanges
                history_str += f"Farmer: {exchange['question']}\n"
                history_str += f"You: {exchange['answer'][:100]}...\n"  # Truncate long answers
            prompt_parts.append(history_str)
        
        # Add the current question
        prompt_parts.append(f"\nFarmer's question: {question}\n\nYour helpful response:")
        
        return "\n\n".join(prompt_parts)
    
    def _call_phi_llm(self, prompt: str) -> Optional[str]:
        """
        Call Phi LLM via Ollama API
        
        Args:
            prompt: The prompt to send to Phi
            
        Returns:
            Generated response or None if failed
        """
        if not self._phi_available:
            return None
        
        try:
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "num_predict": self.config.max_tokens,
                }
            }
            
            response = requests.post(
                f"{self.config.endpoint}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.ok:
                data = response.json()
                generated_text = data.get("response", "").strip()
                
                # Log token usage
                total_duration = data.get("total_duration", 0) / 1e9  # Convert to seconds
                logger.info(f"Phi response generated in {total_duration:.2f}s")
                
                return generated_text
            else:
                logger.error(f"Phi API error: {response.status_code} - {response.text}")
                return None
                
        except requests.Timeout:
            logger.error(f"Phi request timed out after {self.config.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Error calling Phi LLM: {e}", exc_info=True)
            return None
    
    def _extract_crop_from_question(self, question: str) -> Optional[str]:
        """Extract crop name from question if present"""
        question_lower = question.lower()
        
        # Common crops in Indian agriculture
        crops = [
            "rice", "wheat", "maize", "corn", "paddy",
            "tomato", "potato", "onion", "garlic", "ginger",
            "cotton", "sugarcane", "soybean", "groundnut", "peanut",
            "chickpea", "lentil", "peas", "beans",
            "mango", "banana", "guava", "papaya", "orange",
            "chili", "pepper", "brinjal", "eggplant", "cauliflower",
            "cabbage", "carrot", "radish", "beetroot", "spinach"
        ]
        
        for crop in crops:
            if crop in question_lower:
                return crop
        
        return None
    
    def _get_kb_fallback(self, question: str) -> str:
        """Get fallback response from knowledge base"""
        if not self.knowledge_base:
            return "I'm currently unable to provide a detailed answer. Please try again or rephrase your question."
        
        # Simple keyword matching in knowledge base
        question_lower = question.lower()
        best_match = None
        best_score = 0
        
        for kb_question, kb_answer in self.knowledge_base.items():
            # Simple word overlap scoring
            kb_words = set(kb_question.lower().split())
            q_words = set(question_lower.split())
            overlap = len(kb_words & q_words)
            
            if overlap > best_score:
                best_score = overlap
                best_match = kb_answer
        
        if best_match and best_score >= 2:  # At least 2 word overlap
            return best_match
        
        return "I don't have specific information about that. Could you rephrase or ask about common topics like irrigation, fertilizers, pest control, or specific crops?"
    
    def ask(
        self,
        question: str,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Ask a question to the agricultural chatbot
        
        Args:
            question: The farmer's question
            context: Optional context (crop, location, season, etc.)
            session_id: Optional session ID for conversation tracking
            language: Language code (currently supports 'en', future: hi, ta, te, kn)
            
        Returns:
            Dictionary with answer, confidence, enhanced flag, and metadata
        """
        start_time = time.time()
        
        # Auto-extract crop if not in context
        if not context:
            context = {}
        if "crop" not in context:
            detected_crop = self._extract_crop_from_question(question)
            if detected_crop:
                context["crop"] = detected_crop
        
        # Try Phi LLM first
        phi_response = None
        if self._phi_available:
            prompt = self._build_agricultural_prompt(question, context)
            phi_response = self._call_phi_llm(prompt)
        
        # Prepare response
        if phi_response:
            # Phi successfully generated response
            answer = phi_response
            confidence = 0.85  # High confidence for LLM responses
            enhanced = True
            source = "phi_llm"
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "context": context,
                "timestamp": time.time()
            })
            
            # Trim history
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
        else:
            # Fallback to knowledge base
            answer = self._get_kb_fallback(question)
            confidence = 0.6  # Lower confidence for fallback
            enhanced = False
            source = "knowledge_base_fallback"
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "answer": answer,
            "confidence": confidence,
            "enhanced": enhanced,
            "source": source,
            "context": context,
            "processing_time_ms": processing_time,
            "phi_available": self._phi_available,
            "language": language,
            "timestamp": time.time()
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get chatbot status"""
        return {
            "phi_available": self._phi_available,
            "phi_endpoint": self.config.endpoint,
            "phi_model": self.config.model,
            "conversation_length": len(self.conversation_history),
            "kb_entries": len(self.knowledge_base),
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "timeout": self.config.timeout
            }
        }


# ============================================================================
# Convenience Functions
# ============================================================================

# Global instance (singleton pattern)
_phi_chatbot_instance: Optional[PhiAgriChatbot] = None


def get_phi_chatbot(knowledge_base: Optional[Dict] = None) -> PhiAgriChatbot:
    """Get or create global Phi chatbot instance"""
    global _phi_chatbot_instance
    
    if _phi_chatbot_instance is None:
        _phi_chatbot_instance = PhiAgriChatbot(knowledge_base=knowledge_base)
    
    return _phi_chatbot_instance


def enhance_with_phi(
    question: str,
    base_answer: str,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Enhance a base answer with Phi LLM
    
    Args:
        question: Original question
        base_answer: Base answer from knowledge base
        context: Optional context
        
    Returns:
        Enhanced response with metadata
    """
    chatbot = get_phi_chatbot()
    
    # If Phi available, use it to enhance the base answer
    if chatbot._phi_available:
        # Create a prompt that asks Phi to improve the base answer
        enhancement_prompt = f"""Given this farming question and a basic answer, enhance it to be more helpful, conversational, and practical.

Question: {question}

Basic answer: {base_answer}

Provide an enhanced version that:
1. Keeps the core information from the basic answer
2. Adds practical tips or warnings if relevant
3. Uses friendly, farmer-appropriate language
4. Includes specific measurements or timings when helpful

Enhanced answer:"""
        
        enhanced = chatbot._call_phi_llm(enhancement_prompt)
        
        if enhanced:
            return {
                "answer": enhanced,
                "original_answer": base_answer,
                "enhanced": True,
                "source": "phi_enhanced"
            }
    
    # Fallback: return original
    return {
        "answer": base_answer,
        "original_answer": None,
        "enhanced": False,
        "source": "knowledge_base"
    }
