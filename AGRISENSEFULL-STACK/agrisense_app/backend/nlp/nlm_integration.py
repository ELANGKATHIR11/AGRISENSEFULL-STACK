import os
from typing import Dict, Any, cast
from .nlu_service import NLUService
from .response_generator import ResponseGenerator
import llm_clients  # Existing LLM

class NLMIntegration:
    """Combines existing LLM with new NLM for enhanced capabilities"""
    
    def __init__(self):
        self.nlu = NLUService()
        self.response_gen = ResponseGenerator()
        
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query through both systems"""
        # NLM: Intent recognition
        intent, confidence = self.nlu.recognize_intent(query)
        entities = self.nlu.extract_entities(query)
        
        # LLM: Deep semantic understanding
        llm_insights = self._get_llm_insights(query, intent)
        
        # Generate enhanced response
        # Cast to Any to satisfy static type checkers in case ResponseGenerator's
        # runtime implementation provides this method but stubs/annotations do not.
        response = cast(Any, self.response_gen).generate_response(
            context=llm_insights,
            intent=intent,
            entities=entities
        )
        
        return {
            "intent": intent,
            "confidence": confidence,
            "llm_insights": llm_insights,
            "response": response
        }
        
    def _get_llm_insights(self, query: str, intent: str) -> str:
        """Get insights from existing LLM"""
        # Use existing LLM capabilities
        if hasattr(llm_clients, 'llm_rerank'):
            # Example: Get top 3 related concepts
            candidates = ["crop management", "disease prevention", "irrigation techniques"]
            scores = llm_clients.llm_rerank(query, candidates) or []
            return ", ".join([c for _, c in sorted(zip(scores, candidates), reverse=True)[:3]])
        return ""
