"""
Vision Language Model Engine for Crop Disease Detection
Uses Google Gemini 1.5 Flash for multimodal analysis
"""

import os
import json
import logging
from typing import Dict, Optional
from io import BytesIO
import google.generativeai as genai
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CropDiseaseDetector:
    """
    Vision Language Model for detecting crop diseases, pests, and weeds.
    Acts as an Expert Plant Pathologist using Google Gemini.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the VLM with Google Gemini API.
        
        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set or api_key not provided")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 1.5 Flash for faster inference
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # System prompt for strict JSON output
        self.system_prompt = """You are an Expert Plant Pathologist with 20+ years of experience in crop disease diagnosis.

YOUR TASK:
Analyze the provided crop/plant image and detect:
1. Crop Type (e.g., Tomato, Rice, Wheat, Maize, Potato, etc.)
2. Condition: Healthy, Diseased, Weed, or Unknown
3. Specific Disease Name (if diseased) or null (if healthy)
4. Confidence Score (0-100 as a float)
5. Severity Level: Low, Medium, or High

If the condition is Diseased or there's a pest/weed issue, provide:
- 2 Organic Cure methods
- 2 Chemical Cure methods
- 2 Prevention methods

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON. NO markdown, NO code blocks, NO explanations.
- If the image is NOT a plant/crop, return status as "Unknown" with confidence 0.
- Be specific with disease names (e.g., "Early Blight" not just "Blight")
- Confidence must reflect certainty (clear images = 85-95, unclear = 50-70)

EXACT JSON SCHEMA (DO NOT DEVIATE):
{
  "crop_detected": "string",
  "status": "Healthy" | "Diseased" | "Weed" | "Unknown",
  "disease_name": "string or null",
  "confidence": 0.0-100.0,
  "severity": "Low" | "Medium" | "High" | "None",
  "recommendations": {
    "organic_cure": ["method1", "method2"],
    "chemical_cure": ["method1", "method2"],
    "prevention": ["method1", "method2"]
  }
}

EXAMPLES:
Healthy Tomato:
{
  "crop_detected": "Tomato",
  "status": "Healthy",
  "disease_name": null,
  "confidence": 92.5,
  "severity": "None",
  "recommendations": {
    "organic_cure": [],
    "chemical_cure": [],
    "prevention": ["Maintain proper spacing for air circulation", "Use disease-free certified seeds"]
  }
}

Diseased Tomato:
{
  "crop_detected": "Tomato",
  "status": "Diseased",
  "disease_name": "Early Blight (Alternaria solani)",
  "confidence": 88.3,
  "severity": "Medium",
  "recommendations": {
    "organic_cure": ["Apply baking soda solution (1 tbsp per gallon)", "Use copper-based organic fungicide"],
    "chemical_cure": ["Chlorothalonil fungicide every 7-10 days", "Mancozeb spray at first sign of symptoms"],
    "prevention": ["Remove lower leaves touching soil", "Practice crop rotation with 3-year cycle"]
  }
}

Now analyze the image and return ONLY the JSON."""

        logger.info("CropDiseaseDetector initialized with Gemini 1.5 Flash")

    def analyze_image(self, image_bytes: bytes) -> Dict:
        """
        Analyze crop image for diseases, pests, or weeds.
        
        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)
            
        Returns:
            dict: Structured diagnosis with crop type, disease, and recommendations
            
        Raises:
            ValueError: If image is invalid
            RuntimeError: If API call fails
        """
        try:
            # Load image
            image = Image.open(BytesIO(image_bytes))
            logger.info(f"Image loaded: {image.size}, {image.format}")
            
            # Generate content with the system prompt and image
            response = self.model.generate_content(
                [self.system_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low temperature for consistent JSON
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            # Extract text response
            raw_response = response.text.strip()
            logger.info(f"Raw VLM Response: {raw_response[:200]}...")
            
            # Parse JSON (handle potential markdown wrapping)
            json_text = self._extract_json(raw_response)
            result = json.loads(json_text)
            
            # Validate schema
            self._validate_response(result)
            
            logger.info(f"Successfully analyzed image: {result.get('crop_detected')} - {result.get('status')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}\nRaw response: {raw_response}")
            return self._error_response("Invalid JSON response from AI model")
        
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return self._error_response(f"Analysis error: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from response, handling markdown code blocks.
        
        Args:
            text: Raw response text
            
        Returns:
            str: Clean JSON string
        """
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        return text.strip()

    def _validate_response(self, data: Dict) -> None:
        """
        Validate that the response matches the expected schema.
        
        Args:
            data: Parsed JSON response
            
        Raises:
            ValueError: If schema validation fails
        """
        required_fields = ["crop_detected", "status", "disease_name", "confidence", "severity", "recommendations"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate status enum
        valid_statuses = ["Healthy", "Diseased", "Weed", "Unknown"]
        if data["status"] not in valid_statuses:
            raise ValueError(f"Invalid status: {data['status']}")
        
        # Validate recommendations structure
        rec = data["recommendations"]
        if not all(key in rec for key in ["organic_cure", "chemical_cure", "prevention"]):
            raise ValueError("Invalid recommendations structure")
        
        # Validate confidence range
        if not (0 <= data["confidence"] <= 100):
            raise ValueError(f"Confidence must be 0-100, got {data['confidence']}")

    def _error_response(self, message: str) -> Dict:
        """
        Generate a structured error response.
        
        Args:
            message: Error description
            
        Returns:
            dict: Error response matching schema
        """
        return {
            "crop_detected": "Unknown",
            "status": "Unknown",
            "disease_name": None,
            "confidence": 0.0,
            "severity": "None",
            "recommendations": {
                "organic_cure": [],
                "chemical_cure": [],
                "prevention": []
            },
            "error": message
        }


# Singleton instance for dependency injection
_detector_instance: Optional[CropDiseaseDetector] = None


def get_vlm_engine() -> CropDiseaseDetector:
    """
    Get or create singleton VLM engine instance.
    
    Returns:
        CropDiseaseDetector: Initialized detector
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CropDiseaseDetector()
    return _detector_instance
