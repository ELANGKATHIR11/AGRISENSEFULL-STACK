from .nlu_service import NLUService
from .response_generator import ResponseGenerator
import llm_clients

class UnifiedNLP:
    """Combines existing LLM with new NLM for enhanced capabilities"""
    
    def __init__(self):
        self.nlu = NLUService()
        self.response_gen = ResponseGenerator()
        
    def process_query(self, query: str) -> str:
        """
        Process query through both systems:
        1. NLM for intent recognition
        2. LLM for deep semantic understanding
        3. Generate enhanced response
        """
        # NLM: Intent recognition
        intent, _ = self.nlu.recognize_intent(query)
        entities = self.nlu.extract_entities(query)
        
        # LLM: Deep semantic understanding
        llm_insights = self._get_llm_insights(query, intent)
        
        # Generate enhanced response
        return self.response_gen.generate_response(
            context=llm_insights,
            intent=intent,
            entities=entities
        )
        
    def _get_llm_insights(self, query: str, intent: str) -> str:
        """Get insights from existing LLM"""
        # Use existing LLM capabilities
        if hasattr(llm_clients, 'llm_rerank'):
            # Example: Get top 3 related concepts
            candidates = ["crop management", "disease prevention", "irrigation techniques"]
            scores = llm_clients.llm_rerank(query, candidates) or []
            return ", ".join([c for _, c in sorted(zip(scores, candidates), reverse=True)[:3]])
        return ""
