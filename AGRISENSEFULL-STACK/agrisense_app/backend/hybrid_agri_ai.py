"""
Hybrid LLM+VLM Edge AI for Agriculture
========================================

A unified edge AI system combining:
- Phi LLM (Ollama) for natural language understanding and advice
- SCOLD VLM for visual analysis (disease, weed, crop health)
- Offline-first architecture for farm deployments
- Agriculture-specific multimodal intelligence

Features:
---------
1. Multimodal Analysis: Combine image + text queries
2. Contextual Recommendations: Use visual + textual context
3. Offline Operation: Runs locally without internet
4. Domain Expertise: Agricultural knowledge base integration
5. Real-time Processing: Fast inference for field use

Environment Variables:
----------------------
    HYBRID_AI_MODE: 'offline' or 'online' (default: offline)
    HYBRID_AI_TIMEOUT: Request timeout in seconds (default: 45)
    HYBRID_AI_MAX_HISTORY: Conversation history length (default: 5)
    HYBRID_AI_ENABLE_CACHE: Enable response caching (default: true)
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration & Types
# ============================================================================

class AIMode(str, Enum):
    """AI operation mode"""
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"


class AnalysisType(str, Enum):
    """Type of analysis requested"""
    DISEASE_DETECTION = "disease_detection"
    WEED_IDENTIFICATION = "weed_identification"
    CROP_HEALTH = "crop_health"
    PEST_DETECTION = "pest_detection"
    SOIL_ANALYSIS = "soil_analysis"
    GENERAL_ADVICE = "general_advice"
    MULTIMODAL = "multimodal"


@dataclass
class HybridAIConfig:
    """Configuration for Hybrid AI system"""
    mode: AIMode = AIMode.OFFLINE
    timeout: int = 45
    max_history: int = 5
    enable_cache: bool = True
    phi_endpoint: str = "http://localhost:11434"
    phi_model: str = "phi:latest"
    scold_endpoint: str = "http://localhost:8001"
    confidence_threshold: float = 0.6
    temperature: float = 0.75
    

@dataclass
class VisualAnalysis:
    """Visual analysis results from SCOLD VLM"""
    detections: List[Dict[str, Any]]
    confidence: float
    locations: List[Tuple[int, int, int, int]]  # Bounding boxes
    severity: Optional[str] = None
    affected_area_percent: Optional[float] = None
    raw_response: Optional[Dict] = None


@dataclass
class TextualAnalysis:
    """Textual analysis results from Phi LLM"""
    response: str
    confidence: float
    context_used: bool
    reasoning: Optional[str] = None
    recommendations: List[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class HybridAnalysis:
    """Combined hybrid analysis result"""
    analysis_type: AnalysisType
    visual: Optional[VisualAnalysis] = None
    textual: Optional[TextualAnalysis] = None
    synthesis: Optional[str] = None  # Combined interpretation
    actionable_steps: List[str] = None
    confidence_score: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: str = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'analysis_type': self.analysis_type.value,
            'visual': asdict(self.visual) if self.visual else None,
            'textual': asdict(self.textual) if self.textual else None,
            'synthesis': self.synthesis,
            'actionable_steps': self.actionable_steps or [],
            'confidence_score': self.confidence_score,
            'processing_time_ms': self.processing_time_ms,
            'timestamp': self.timestamp,
            'metadata': self.metadata or {}
        }


# ============================================================================
# Hybrid AI Core Engine
# ============================================================================

class HybridAgriAI:
    """
    Hybrid LLM+VLM Edge AI System for Agriculture
    
    Combines Phi LLM and SCOLD VLM for comprehensive agricultural analysis.
    Designed for offline operation on edge devices (Raspberry Pi, farm servers).
    """
    
    def __init__(self, config: Optional[HybridAIConfig] = None):
        """Initialize hybrid AI system"""
        self.config = config or self._load_config()
        self.conversation_history: List[Dict] = []
        self.cache: Dict[str, Any] = {}
        self._phi_available = False
        self._scold_available = False
        self._check_availability()
        
        logger.info(
            f"🤖 Hybrid AgriAI initialized: "
            f"Phi={'✅' if self._phi_available else '❌'} "
            f"SCOLD={'✅' if self._scold_available else '❌'} "
            f"Mode={self.config.mode.value}"
        )
    
    def _load_config(self) -> HybridAIConfig:
        """Load configuration from environment"""
        return HybridAIConfig(
            mode=AIMode(os.getenv("HYBRID_AI_MODE", "offline")),
            timeout=int(os.getenv("HYBRID_AI_TIMEOUT", "45")),
            max_history=int(os.getenv("HYBRID_AI_MAX_HISTORY", "5")),
            enable_cache=os.getenv("HYBRID_AI_ENABLE_CACHE", "true").lower() == "true",
            phi_endpoint=os.getenv("PHI_LLM_ENDPOINT", "http://localhost:11434"),
            phi_model=os.getenv("PHI_MODEL_NAME", "phi:latest"),
            scold_endpoint=os.getenv("SCOLD_BASE_URL", "http://localhost:8001"),
            confidence_threshold=float(os.getenv("SCOLD_CONFIDENCE_THRESHOLD", "0.6")),
            temperature=float(os.getenv("PHI_CHAT_TEMPERATURE", "0.75"))
        )
    
    def _check_availability(self):
        """Check if LLM and VLM are available"""
        # Check Phi LLM
        try:
            import requests
            resp = requests.get(
                f"{self.config.phi_endpoint}/api/tags",
                timeout=5
            )
            self._phi_available = resp.status_code == 200
        except Exception as e:
            logger.warning(f"Phi LLM not available: {e}")
            self._phi_available = False
        
        # Check SCOLD VLM
        try:
            import requests
            resp = requests.get(
                f"{self.config.scold_endpoint}/health",
                timeout=5
            )
            self._scold_available = resp.status_code == 200
        except Exception as e:
            logger.warning(f"SCOLD VLM not available: {e}")
            self._scold_available = False
    
    # ========================================================================
    # Visual Analysis (SCOLD VLM)
    # ========================================================================
    
    def analyze_image(
        self,
        image_data: Union[str, bytes, Image.Image],
        analysis_type: AnalysisType = AnalysisType.MULTIMODAL,
        prompt: Optional[str] = None
    ) -> VisualAnalysis:
        """
        Analyze agricultural image using SCOLD VLM
        
        Args:
            image_data: Image file path, bytes, or PIL Image
            analysis_type: Type of analysis to perform
            prompt: Optional specific prompt for VLM
            
        Returns:
            VisualAnalysis with detections and insights
        """
        if not self._scold_available:
            logger.warning("SCOLD VLM not available, using fallback")
            return self._fallback_visual_analysis(image_data, analysis_type)
        
        try:
            import requests
            
            # Convert image to base64
            image_b64 = self._image_to_base64(image_data)
            
            # Build prompt based on analysis type
            if not prompt:
                prompt = self._build_visual_prompt(analysis_type)
            
            # Call SCOLD VLM
            payload = {
                "image": image_b64,
                "prompt": prompt,
                "confidence_threshold": self.config.confidence_threshold
            }
            
            response = requests.post(
                f"{self.config.scold_endpoint}/api/analyze",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            # Parse SCOLD response
            return VisualAnalysis(
                detections=result.get("detections", []),
                confidence=result.get("confidence", 0.0),
                locations=result.get("bounding_boxes", []),
                severity=result.get("severity"),
                affected_area_percent=result.get("affected_area_percent"),
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"SCOLD VLM analysis failed: {e}")
            return self._fallback_visual_analysis(image_data, analysis_type)
    
    def _build_visual_prompt(self, analysis_type: AnalysisType) -> str:
        """Build VLM prompt based on analysis type"""
        prompts = {
            AnalysisType.DISEASE_DETECTION: (
                "Analyze this plant image and identify any diseases. "
                "Provide: disease name, affected parts, severity (mild/moderate/severe), "
                "and estimated affected area percentage."
            ),
            AnalysisType.WEED_IDENTIFICATION: (
                "Identify weeds in this agricultural field image. "
                "For each weed: provide common name, scientific name if possible, "
                "location in image, and coverage percentage."
            ),
            AnalysisType.CROP_HEALTH: (
                "Assess the overall health of crops in this image. "
                "Consider: leaf color, growth stage, signs of stress, nutrient deficiency, "
                "and provide a health score (0-100)."
            ),
            AnalysisType.PEST_DETECTION: (
                "Detect and identify any pests or insect damage in this image. "
                "For each pest: name, location, damage severity, and life stage if visible."
            ),
            AnalysisType.SOIL_ANALYSIS: (
                "Analyze visible soil conditions in this image. "
                "Assess: soil texture, moisture level, color, visible organic matter, "
                "and erosion signs."
            )
        }
        return prompts.get(
            analysis_type,
            "Analyze this agricultural image and provide detailed observations."
        )
    
    def _fallback_visual_analysis(
        self, 
        image_data: Any, 
        analysis_type: AnalysisType
    ) -> VisualAnalysis:
        """Fallback visual analysis when SCOLD unavailable"""
        return VisualAnalysis(
            detections=[{
                "type": "fallback",
                "message": "Visual analysis unavailable - SCOLD VLM offline",
                "analysis_type": analysis_type.value
            }],
            confidence=0.0,
            locations=[],
            severity="unknown"
        )
    
    # ========================================================================
    # Textual Analysis (Phi LLM)
    # ========================================================================
    
    def analyze_text(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_history: bool = True
    ) -> TextualAnalysis:
        """
        Analyze text query using Phi LLM with agricultural expertise
        
        Args:
            query: User question or statement
            context: Additional context (crop type, location, season, etc.)
            use_history: Include conversation history
            
        Returns:
            TextualAnalysis with response and recommendations
        """
        if not self._phi_available:
            logger.warning("Phi LLM not available, using fallback")
            return self._fallback_text_analysis(query)
        
        try:
            import requests
            
            # Build agricultural expert prompt
            system_prompt = self._build_text_prompt(context)
            
            # Add conversation history
            messages = []
            if use_history and self.conversation_history:
                messages.extend(self.conversation_history[-self.config.max_history:])
            
            messages.append({"role": "user", "content": query})
            
            # Call Phi LLM via Ollama
            payload = {
                "model": self.config.phi_model,
                "messages": messages,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "top_p": 0.95,
                    "top_k": 50,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                f"{self.config.phi_endpoint}/api/chat",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            assistant_message = result.get("message", {}).get("content", "")
            
            # Extract recommendations from response
            recommendations = self._extract_recommendations(assistant_message)
            
            # Update conversation history
            if use_history:
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
            
            return TextualAnalysis(
                response=assistant_message,
                confidence=0.85,  # Phi is generally reliable
                context_used=context is not None,
                recommendations=recommendations,
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"Phi LLM analysis failed: {e}")
            return self._fallback_text_analysis(query)
    
    def _build_text_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt for Phi LLM"""
        base_prompt = (
            "You are an expert agricultural AI assistant with deep knowledge of:\n"
            "- Crop cultivation and management\n"
            "- Disease and pest identification\n"
            "- Soil health and fertilization\n"
            "- Irrigation and water management\n"
            "- Sustainable farming practices\n"
            "- Organic and traditional methods\n\n"
            "Provide practical, actionable advice that farmers can implement. "
            "Be specific with measurements, timing, and techniques. "
            "Consider local conditions and traditional knowledge. "
            "Always prioritize farmer safety and environmental sustainability.\n"
        )
        
        if context:
            context_str = "\nCurrent context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            base_prompt += context_str
        
        return base_prompt
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from LLM response"""
        recommendations = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered items, bullet points, or "should/must/need to"
            if (line and (
                line[0].isdigit() or
                line.startswith(('- ', '• ', '* ')) or
                any(word in line.lower() for word in ['should', 'must', 'need to', 'recommend'])
            )):
                # Clean up formatting
                rec = line.lstrip('0123456789.-•* ').strip()
                if len(rec) > 10:  # Avoid very short fragments
                    recommendations.append(rec)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _fallback_text_analysis(self, query: str) -> TextualAnalysis:
        """Fallback text analysis when Phi unavailable"""
        return TextualAnalysis(
            response=(
                "I'm currently operating in offline mode without the language model. "
                "Please check that Ollama is running and the Phi model is available. "
                f"Your query was: '{query}'"
            ),
            confidence=0.0,
            context_used=False,
            recommendations=[]
        )
    
    # ========================================================================
    # Hybrid Multimodal Analysis
    # ========================================================================
    
    def analyze_multimodal(
        self,
        image_data: Union[str, bytes, Image.Image],
        text_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> HybridAnalysis:
        """
        Perform hybrid analysis combining visual and textual AI
        
        This is the core capability: analyze an image while understanding
        natural language queries about it.
        
        Example:
            image = "diseased_tomato_leaf.jpg"
            query = "What's wrong with my tomato plant and how do I treat it?"
            result = ai.analyze_multimodal(image, query)
        
        Args:
            image_data: Agricultural image
            text_query: Question or request about the image
            context: Additional context (crop type, location, etc.)
            
        Returns:
            HybridAnalysis combining visual + textual insights
        """
        start_time = time.time()
        
        # Determine analysis type from query
        analysis_type = self._infer_analysis_type(text_query)
        
        # Step 1: Visual analysis with SCOLD
        logger.info(f"🔍 Visual analysis: {analysis_type.value}")
        visual_result = self.analyze_image(image_data, analysis_type)
        
        # Step 2: Build enhanced context with visual findings
        enhanced_context = context or {}
        enhanced_context['visual_findings'] = {
            'detections': visual_result.detections,
            'confidence': visual_result.confidence,
            'severity': visual_result.severity,
            'affected_area': visual_result.affected_area_percent
        }
        
        # Step 3: Textual analysis with Phi using visual context
        enhanced_query = self._build_enhanced_query(text_query, visual_result)
        logger.info(f"💬 Textual analysis with visual context")
        textual_result = self.analyze_text(enhanced_query, enhanced_context)
        
        # Step 4: Synthesize results
        synthesis = self._synthesize_results(
            visual_result,
            textual_result,
            text_query
        )
        
        # Step 5: Extract actionable steps
        actionable_steps = self._extract_actionable_steps(
            visual_result,
            textual_result
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(visual_result, textual_result)
        
        processing_time = (time.time() - start_time) * 1000
        
        result = HybridAnalysis(
            analysis_type=analysis_type,
            visual=visual_result,
            textual=textual_result,
            synthesis=synthesis,
            actionable_steps=actionable_steps,
            confidence_score=confidence,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat(),
            metadata={
                'query': text_query,
                'context': context,
                'phi_available': self._phi_available,
                'scold_available': self._scold_available
            }
        )
        
        logger.info(
            f"✅ Hybrid analysis complete: "
            f"{processing_time:.0f}ms, confidence={confidence:.2f}"
        )
        
        return result
    
    def _infer_analysis_type(self, query: str) -> AnalysisType:
        """Infer analysis type from user query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['disease', 'sick', 'infection', 'fungus', 'blight']):
            return AnalysisType.DISEASE_DETECTION
        elif any(word in query_lower for word in ['weed', 'unwanted plant', 'invasive']):
            return AnalysisType.WEED_IDENTIFICATION
        elif any(word in query_lower for word in ['pest', 'insect', 'bug', 'damage']):
            return AnalysisType.PEST_DETECTION
        elif any(word in query_lower for word in ['soil', 'ground', 'earth']):
            return AnalysisType.SOIL_ANALYSIS
        elif any(word in query_lower for word in ['health', 'growth', 'condition']):
            return AnalysisType.CROP_HEALTH
        else:
            return AnalysisType.MULTIMODAL
    
    def _build_enhanced_query(
        self,
        original_query: str,
        visual_result: VisualAnalysis
    ) -> str:
        """Enhance text query with visual analysis results"""
        if not visual_result.detections:
            return original_query
        
        visual_summary = "Visual analysis detected: "
        detection_summaries = []
        
        for detection in visual_result.detections[:3]:  # Top 3 detections
            if isinstance(detection, dict):
                det_type = detection.get('type', 'unknown')
                det_conf = detection.get('confidence', 0.0)
                detection_summaries.append(f"{det_type} (confidence: {det_conf:.2f})")
        
        if detection_summaries:
            visual_summary += ", ".join(detection_summaries)
            if visual_result.severity:
                visual_summary += f". Severity: {visual_result.severity}"
            
            enhanced = f"{visual_summary}\n\nUser question: {original_query}"
            return enhanced
        
        return original_query
    
    def _synthesize_results(
        self,
        visual: VisualAnalysis,
        textual: TextualAnalysis,
        original_query: str
    ) -> str:
        """Synthesize visual and textual results into coherent response"""
        if not self._phi_available or not self._scold_available:
            # If either is unavailable, use available one
            if textual.response:
                return textual.response
            elif visual.detections:
                return f"Visual analysis detected: {json.dumps(visual.detections, indent=2)}"
            else:
                return "Analysis unavailable - both AI systems offline"
        
        # Both available - Phi already synthesized with visual context
        return textual.response
    
    def _extract_actionable_steps(
        self,
        visual: VisualAnalysis,
        textual: TextualAnalysis
    ) -> List[str]:
        """Extract clear actionable steps from analysis"""
        steps = []
        
        # Get recommendations from textual analysis
        if textual.recommendations:
            steps.extend(textual.recommendations)
        
        # Add visual-based actions
        if visual.severity in ['moderate', 'severe']:
            steps.insert(0, f"⚠️ Immediate action required - {visual.severity} severity detected")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_steps = []
        for step in steps:
            if step not in seen:
                seen.add(step)
                unique_steps.append(step)
        
        return unique_steps[:7]  # Top 7 actionable steps
    
    def _calculate_confidence(
        self,
        visual: VisualAnalysis,
        textual: TextualAnalysis
    ) -> float:
        """Calculate overall confidence score"""
        visual_conf = visual.confidence if self._scold_available else 0.0
        textual_conf = textual.confidence if self._phi_available else 0.0
        
        if self._phi_available and self._scold_available:
            # Both available - weighted average (visual 60%, textual 40%)
            return (visual_conf * 0.6) + (textual_conf * 0.4)
        elif self._phi_available:
            return textual_conf
        elif self._scold_available:
            return visual_conf
        else:
            return 0.0
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _image_to_base64(self, image_data: Union[str, bytes, Image.Image]) -> str:
        """Convert various image formats to base64"""
        if isinstance(image_data, str):
            # File path
            with open(image_data, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        elif isinstance(image_data, bytes):
            return base64.b64encode(image_data).decode('utf-8')
        elif isinstance(image_data, Image.Image):
            buffer = io.BytesIO()
            image_data.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        else:
            raise ValueError(f"Unsupported image type: {type(image_data)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "hybrid_ai_available": self._phi_available and self._scold_available,
            "phi_llm_available": self._phi_available,
            "scold_vlm_available": self._scold_available,
            "mode": self.config.mode.value,
            "conversation_history_length": len(self.conversation_history),
            "cache_size": len(self.cache),
            "config": {
                "phi_endpoint": self.config.phi_endpoint,
                "phi_model": self.config.phi_model,
                "scold_endpoint": self.config.scold_endpoint,
                "timeout": self.config.timeout,
                "temperature": self.config.temperature
            }
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def clear_cache(self):
        """Clear response cache"""
        self.cache.clear()
        logger.info("Response cache cleared")


# ============================================================================
# Convenience Functions
# ============================================================================

# Global instance
_hybrid_ai_instance: Optional[HybridAgriAI] = None


def get_hybrid_ai() -> HybridAgriAI:
    """Get or create global Hybrid AI instance"""
    global _hybrid_ai_instance
    if _hybrid_ai_instance is None:
        _hybrid_ai_instance = HybridAgriAI()
    return _hybrid_ai_instance


def analyze_farm_image(
    image_path: str,
    question: str,
    context: Optional[Dict] = None
) -> HybridAnalysis:
    """
    Quick function to analyze a farm image with a question
    
    Example:
        result = analyze_farm_image(
            "tomato_leaf.jpg",
            "What disease does this plant have?",
            context={"crop": "tomato", "location": "greenhouse"}
        )
    """
    ai = get_hybrid_ai()
    return ai.analyze_multimodal(image_path, question, context)


def ask_agricultural_question(
    question: str,
    context: Optional[Dict] = None
) -> str:
    """
    Quick function to ask agricultural question (text only)
    
    Example:
        answer = ask_agricultural_question(
            "When should I plant wheat in North India?"
        )
    """
    ai = get_hybrid_ai()
    result = ai.analyze_text(question, context)
    return result.response
