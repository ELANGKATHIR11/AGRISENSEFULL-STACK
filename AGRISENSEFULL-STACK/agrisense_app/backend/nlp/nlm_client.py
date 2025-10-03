import os
from typing import List, Dict, Any, Optional

from .nlu_service import NLUService
from .response_generator import ResponseGenerator

class NLMClient:
    """
    Client to interact with the Natural Language Model (NLM) services.
    Combines NLU for intent recognition and response generation.
    """
    
    def __init__(self):
        self.nlu_service = NLUService()
        self.response_generator = ResponseGenerator()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the NLM pipeline.
        
        Args:
            query: User's natural language query
            
        Returns:
            A dictionary containing the intent, entities, and generated response.
        """
        # Recognize intent and extract entities
        intent, confidence = self.nlu_service.recognize_intent(query)
        entities = self.nlu_service.extract_entities(query)
        
        # Generate response based on intent and entities
        response = self.response_generator.generate_response(query, intent, entities)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "response": response
        }
