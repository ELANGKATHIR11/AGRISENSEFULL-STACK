import os
from typing import Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class NLUService:
    """
    Natural Language Understanding service for intent recognition and entity extraction
    """
    
    def __init__(self):
        # Use a lightweight model for production
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.intents = self._load_intents()
        
    def _load_intents(self) -> Dict[str, np.ndarray]:
        """Load predefined intents and their embeddings"""
        intents = {
            "weather_inquiry": ["weather", "forecast", "rain", "temperature"],
            "crop_advice": ["crop", "plant", "harvest", "grow"],
            "disease_help": ["disease", "sick", "infected", "treatment"],
            "irrigation_help": ["water", "irrigate", "moisture", "hydrate"],
            "general_help": ["help", "assist", "support", "question"]
        }
        return {intent: self.model.encode(phrases) for intent, phrases in intents.items()}
    
    def recognize_intent(self, text: str) -> Tuple[str, float]:
        """
        Recognize user intent with similarity scoring
        Args:
            text: User input text
        Returns:
            tuple: (intent, confidence_score)
        """
        query_embedding = self.model.encode([text])
        best_intent = "general_help"
        best_score = 0.0
        
        for intent, embeddings in self.intents.items():
            scores = cosine_similarity(query_embedding, embeddings)
            max_score = np.max(scores)
            if max_score > best_score:
                best_score = max_score
                best_intent = intent
                
        return best_intent, float(best_score)
    
    def extract_entities(self, text: str) -> Dict[str, str]:
        """
        Extract key entities from user input
        Args:
            text: User input text
        Returns:
            dict: Extracted entities
        """
        # Simple rule-based entity extraction (can be enhanced with NER later)
        entities = {}
        words = text.lower().split()
        
        # Extract crop names
        crop_keywords = {"rice", "wheat", "corn", "maize", "soybean", "cotton"}
        crops = [word for word in words if word in crop_keywords]
        if crops:
            entities["crop"] = crops[0]
            
        # Extract locations
        location_keywords = {"field", "farm", "garden", "plot"}
        locations = [word for word in words if word in location_keywords]
        if locations:
            entities["location"] = locations[0]
            
        # Extract problems
        problem_keywords = {"yellow", "wilting", "spots", "drying", "pests"}
        problems = [word for word in words if word in problem_keywords]
        if problems:
            entities["problem"] = problems[0]
            
        return entities
