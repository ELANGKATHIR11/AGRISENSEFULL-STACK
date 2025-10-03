#!/usr/bin/env python3
"""
Vision Language Model (VLM) Engine for AgriSense
Combines computer vision with agricultural knowledge base for enhanced analysis
"""

import json
import logging
import os
import re
import base64
import io
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from PIL import Image
import cv2
from datetime import datetime
import random

# Optional ML imports with fallbacks
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import transforms, models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgriVLMEngine:
    """
    Vision Language Model Engine for Agricultural Analysis
    Combines image analysis with agricultural knowledge base
    """
    
    def __init__(self):
        self.knowledge_base = {}
        self.image_processor = None
        self.text_encoder = None
        self.vision_model = None
        self.load_knowledge_base()
        self.initialize_models()
    
    def load_knowledge_base(self):
        """Load agricultural knowledge base from JSON files"""
        try:
            # Load agriculture books data
            books_path = Path(__file__).parent.parent.parent / "archive (7)" / "Agriculture_Books_Data.json"
            if books_path.exists():
                with open(books_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base['books'] = json.load(f)
                logger.info(f"Loaded {len(self.knowledge_base['books'])} agricultural books")
            
            # Load disease and weed classes
            config_dir = Path(__file__).parent / "config"
            
            disease_classes_path = config_dir / "disease_classes.json"
            if disease_classes_path.exists():
                with open(disease_classes_path, 'r') as f:
                    self.knowledge_base['diseases'] = json.load(f)
            
            weed_classes_path = config_dir / "weed_classes.json"
            if weed_classes_path.exists():
                with open(weed_classes_path, 'r') as f:
                    self.knowledge_base['weeds'] = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load full knowledge base: {e}")
            self.knowledge_base = self._create_fallback_knowledge_base()
    
    def _create_fallback_knowledge_base(self) -> Dict[str, Any]:
        """Create fallback knowledge base with essential agricultural information"""
        return {
            'diseases': {
                'common_diseases': [
                    'leaf_spot', 'powdery_mildew', 'rust', 'blight', 'mosaic_virus',
                    'bacterial_wilt', 'root_rot', 'anthracnose', 'downy_mildew'
                ],
                'symptoms': {
                    'leaf_spot': 'Circular or irregular spots on leaves, often with yellow halos',
                    'powdery_mildew': 'White powdery coating on leaves and stems',
                    'rust': 'Orange or reddish pustules on leaf surfaces',
                    'blight': 'Rapid browning and death of plant tissues',
                    'mosaic_virus': 'Mottled yellow and green patterns on leaves'
                }
            },
            'weeds': {
                'common_weeds': [
                    'dandelion', 'crabgrass', 'clover', 'plantain', 'chickweed',
                    'pigweed', 'lambsquarters', 'foxtail', 'bindweed'
                ],
                'characteristics': {
                    'broadleaf': ['dandelion', 'clover', 'plantain', 'chickweed'],
                    'grassy': ['crabgrass', 'foxtail'],
                    'annual': ['crabgrass', 'pigweed', 'lambsquarters'],
                    'perennial': ['dandelion', 'clover', 'bindweed']
                }
            },
            'crops': {
                'major_crops': [
                    'corn', 'wheat', 'rice', 'soybean', 'cotton', 'tomato',
                    'potato', 'apple', 'grape', 'citrus'
                ]
            }
        }
    
    def initialize_models(self):
        """Initialize vision and language models"""
        try:
            if TRANSFORMERS_AVAILABLE:
                # Initialize BLIP for image captioning and VQA
                self.image_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.vision_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                logger.info("Initialized BLIP model for image analysis")
            
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Initialize sentence transformer for text similarity
                self.text_encoder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Initialized sentence transformer for text encoding")
                
        except Exception as e:
            logger.warning(f"Could not initialize advanced models: {e}")
            self._initialize_fallback_models()
    
    def _initialize_fallback_models(self):
        """Initialize basic computer vision models as fallback"""
        try:
            if TORCH_AVAILABLE:
                # Use basic ResNet for image feature extraction
                self.vision_model = models.resnet50(pretrained=True)
                self.vision_model.eval()
                
                self.transform = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                       std=[0.229, 0.224, 0.225])
                ])
                logger.info("Initialized ResNet50 for basic image analysis")
        except Exception as e:
            logger.warning(f"Fallback model initialization failed: {e}")
    
    def preprocess_image(self, image_input: Union[str, bytes, Image.Image]) -> Image.Image:
        """Preprocess image input to PIL Image"""
        if isinstance(image_input, str):
            if image_input.startswith('data:image'):
                # Base64 encoded image
                image_data = image_input.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                return Image.open(io.BytesIO(image_bytes)).convert('RGB')
            else:
                # File path
                return Image.open(image_input).convert('RGB')
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, Image.Image):
            return image_input.convert('RGB')
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    def analyze_image_content(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image content using vision models"""
        try:
            if self.image_processor and self.vision_model and TRANSFORMERS_AVAILABLE:
                # Use BLIP for detailed image analysis
                inputs = self.image_processor(image, return_tensors="pt")
                
                # Generate image caption
                out = self.vision_model.generate(**inputs, max_length=50)
                caption = self.image_processor.decode(out[0], skip_special_tokens=True)
                
                # Extract visual features
                visual_features = self._extract_visual_features(image)
                
                return {
                    'caption': caption,
                    'visual_features': visual_features,
                    'analysis_method': 'BLIP'
                }
            else:
                # Fallback to basic analysis
                return self._basic_image_analysis(image)
                
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._basic_image_analysis(image)
    
    def _extract_visual_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extract detailed visual features from image"""
        # Convert to OpenCV format for analysis
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        features = {
            'dominant_colors': self._get_dominant_colors(cv_image),
            'texture_analysis': self._analyze_texture(cv_image),
            'shape_analysis': self._analyze_shapes(cv_image),
            'size': image.size
        }
        
        return features
    
    def _get_dominant_colors(self, cv_image: np.ndarray) -> List[List[int]]:
        """Extract dominant colors from image"""
        try:
            # Reshape image to be a list of pixels
            pixels = cv_image.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # Use k-means to find dominant colors
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            k = 5
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert to RGB and return as list
            centers = np.uint8(centers)
            dominant_colors = [color.tolist() for color in centers]
            
            return dominant_colors
        except Exception:
            return [[0, 128, 0], [139, 69, 19], [255, 255, 0]]  # Default: green, brown, yellow
    
    def _analyze_texture(self, cv_image: np.ndarray) -> Dict[str, float]:
        """Analyze image texture characteristics"""
        try:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate texture features
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate local binary pattern approximation
            mean_intensity = np.mean(gray)
            std_intensity = np.std(gray)
            
            return {
                'sharpness': float(laplacian_var),
                'mean_intensity': float(mean_intensity),
                'intensity_variation': float(std_intensity)
            }
        except Exception:
            return {'sharpness': 100.0, 'mean_intensity': 128.0, 'intensity_variation': 50.0}
    
    def _analyze_shapes(self, cv_image: np.ndarray) -> Dict[str, Any]:
        """Analyze shapes and contours in image"""
        try:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            return {
                'contour_count': len(contours),
                'edge_density': float(np.sum(edges > 0) / edges.size)
            }
        except Exception:
            return {'contour_count': 10, 'edge_density': 0.1}
    
    def _basic_image_analysis(self, image: Image.Image) -> Dict[str, Any]:
        """Basic image analysis without advanced models"""
        # Convert to numpy array for basic analysis
        img_array = np.array(image)
        
        # Basic color analysis
        mean_color = np.mean(img_array, axis=(0, 1))
        
        # Determine likely content based on color analysis
        green_dominant = mean_color[1] > mean_color[0] and mean_color[1] > mean_color[2]
        brown_present = np.mean(img_array[:, :, 0]) > 100 and np.mean(img_array[:, :, 1]) > 50
        
        caption = "Agricultural field image"
        if green_dominant:
            caption = "Green vegetation or crop field"
        elif brown_present:
            caption = "Soil or dried vegetation"
        
        return {
            'caption': caption,
            'visual_features': {
                'dominant_colors': mean_color.tolist(),
                'size': image.size,
                'green_dominant': green_dominant,
                'brown_present': brown_present
            },
            'analysis_method': 'basic'
        }
    
    def search_knowledge_base(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search agricultural knowledge base for relevant information"""
        results = []
        query_lower = query.lower()
        
        try:
            # Search in books data if available
            if 'books' in self.knowledge_base:
                for book_name, content in self.knowledge_base['books'].items():
                    if isinstance(content, str) and query_lower in content.lower():
                        # Extract relevant excerpt
                        content_lower = content.lower()
                        start_idx = max(0, content_lower.find(query_lower) - 200)
                        end_idx = min(len(content), content_lower.find(query_lower) + 400)
                        excerpt = content[start_idx:end_idx].strip()
                        
                        results.append({
                            'source': book_name,
                            'type': 'book',
                            'excerpt': excerpt,
                            'relevance_score': self._calculate_relevance(query, excerpt)
                        })
            
            # Search in disease/weed databases
            if category == 'disease' and 'diseases' in self.knowledge_base:
                disease_info = self.knowledge_base['diseases']
                for disease, symptoms in disease_info.get('symptoms', {}).items():
                    if query_lower in disease.lower() or query_lower in symptoms.lower():
                        results.append({
                            'source': 'disease_database',
                            'type': 'disease',
                            'disease': disease,
                            'symptoms': symptoms,
                            'relevance_score': self._calculate_relevance(query, f"{disease} {symptoms}")
                        })
            
            elif category == 'weed' and 'weeds' in self.knowledge_base:
                weed_info = self.knowledge_base['weeds']
                for weed in weed_info.get('common_weeds', []):
                    if query_lower in weed.lower():
                        results.append({
                            'source': 'weed_database',
                            'type': 'weed',
                            'weed': weed,
                            'relevance_score': self._calculate_relevance(query, weed)
                        })
        
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results[:10]  # Return top 10 results
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate relevance score between query and text"""
        if self.text_encoder and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                query_embedding = self.text_encoder.encode([query])
                text_embedding = self.text_encoder.encode([text])
                similarity = np.dot(query_embedding[0], text_embedding[0]) / (
                    np.linalg.norm(query_embedding[0]) * np.linalg.norm(text_embedding[0])
                )
                return float(similarity)
            except Exception:
                pass
        
        # Fallback to simple word matching
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def generate_enhanced_analysis(self, image_input: Union[str, bytes, Image.Image], 
                                 analysis_type: str = 'general',
                                 crop_type: str = 'unknown') -> Dict[str, Any]:
        """
        Generate enhanced analysis combining vision and knowledge base
        
        Args:
            image_input: Image data (base64, bytes, or PIL Image)
            analysis_type: Type of analysis ('disease', 'weed', 'general')
            crop_type: Type of crop being analyzed
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # Preprocess image
            image = self.preprocess_image(image_input)
            
            # Analyze image content
            vision_analysis = self.analyze_image_content(image)
            
            # Search knowledge base based on vision analysis
            search_query = f"{analysis_type} {crop_type} {vision_analysis.get('caption', '')}"
            knowledge_results = self.search_knowledge_base(search_query, analysis_type)
            
            # Generate comprehensive recommendations
            recommendations = self._generate_recommendations(
                vision_analysis, knowledge_results, analysis_type, crop_type
            )
            
            # Calculate confidence scores
            confidence_score = self._calculate_confidence(vision_analysis, knowledge_results)
            
            return {
                'analysis_type': analysis_type,
                'crop_type': crop_type,
                'timestamp': datetime.now().isoformat(),
                'vision_analysis': vision_analysis,
                'knowledge_matches': knowledge_results,
                'recommendations': recommendations,
                'confidence_score': confidence_score,
                'vlm_version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {e}")
            return self._generate_fallback_analysis(analysis_type, crop_type)
    
    def _generate_recommendations(self, vision_analysis: Dict[str, Any], 
                                knowledge_results: List[Dict[str, Any]],
                                analysis_type: str, crop_type: str) -> Dict[str, Any]:
        """Generate actionable recommendations based on analysis"""
        recommendations = {
            'immediate_actions': [],
            'preventive_measures': [],
            'monitoring_suggestions': [],
            'treatment_options': []
        }
        
        try:
            # Extract insights from vision analysis
            caption = vision_analysis.get('caption', '').lower()
            visual_features = vision_analysis.get('visual_features', {})
            
            # Generate recommendations based on analysis type
            if analysis_type == 'disease':
                recommendations.update(self._generate_disease_recommendations(
                    caption, visual_features, knowledge_results, crop_type
                ))
            elif analysis_type == 'weed':
                recommendations.update(self._generate_weed_recommendations(
                    caption, visual_features, knowledge_results, crop_type
                ))
            else:
                recommendations.update(self._generate_general_recommendations(
                    caption, visual_features, knowledge_results, crop_type
                ))
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            recommendations['immediate_actions'] = ["Consult with agricultural expert for detailed analysis"]
        
        return recommendations
    
    def _generate_disease_recommendations(self, caption: str, visual_features: Dict[str, Any],
                                        knowledge_results: List[Dict[str, Any]], 
                                        crop_type: str) -> Dict[str, Any]:
        """Generate disease-specific recommendations"""
        recommendations = {
            'immediate_actions': [],
            'preventive_measures': [],
            'monitoring_suggestions': [],
            'treatment_options': []
        }
        
        # Analyze visual indicators
        if 'spot' in caption or 'brown' in caption:
            recommendations['immediate_actions'].append("Isolate affected plants to prevent spread")
            recommendations['treatment_options'].append("Apply fungicide treatment for leaf spot diseases")
        
        if 'yellow' in caption or visual_features.get('dominant_colors'):
            recommendations['monitoring_suggestions'].append("Monitor for nutrient deficiency or viral infections")
        
        # Add knowledge-based recommendations
        for result in knowledge_results[:3]:
            if result.get('type') == 'disease':
                disease = result.get('disease', '')
                if 'fungal' in result.get('symptoms', '').lower():
                    recommendations['treatment_options'].append(f"Consider copper-based fungicide for {disease}")
                elif 'bacterial' in result.get('symptoms', '').lower():
                    recommendations['treatment_options'].append(f"Apply bactericide for {disease}")
        
        # Add general preventive measures
        recommendations['preventive_measures'].extend([
            "Ensure proper plant spacing for air circulation",
            "Avoid overhead watering to reduce moisture on leaves",
            "Remove and destroy infected plant debris"
        ])
        
        return recommendations
    
    def _generate_weed_recommendations(self, caption: str, visual_features: Dict[str, Any],
                                     knowledge_results: List[Dict[str, Any]], 
                                     crop_type: str) -> Dict[str, Any]:
        """Generate weed-specific recommendations"""
        recommendations = {
            'immediate_actions': [],
            'preventive_measures': [],
            'monitoring_suggestions': [],
            'treatment_options': []
        }
        
        # Analyze weed density and type
        contour_count = visual_features.get('contour_count', 0)
        if contour_count > 20:
            recommendations['immediate_actions'].append("High weed density detected - immediate action required")
            recommendations['treatment_options'].append("Consider post-emergent herbicide application")
        else:
            recommendations['immediate_actions'].append("Moderate weed pressure - monitor closely")
            recommendations['treatment_options'].append("Spot treatment or mechanical removal may be sufficient")
        
        # Add knowledge-based recommendations
        for result in knowledge_results[:3]:
            if result.get('type') == 'weed':
                weed = result.get('weed', '')
                if weed in self.knowledge_base.get('weeds', {}).get('characteristics', {}).get('broadleaf', []):
                    recommendations['treatment_options'].append(f"Use broadleaf herbicide for {weed}")
                elif weed in self.knowledge_base.get('weeds', {}).get('characteristics', {}).get('grassy', []):
                    recommendations['treatment_options'].append(f"Use grass-selective herbicide for {weed}")
        
        # Add preventive measures
        recommendations['preventive_measures'].extend([
            "Maintain healthy crop canopy to suppress weed growth",
            "Use pre-emergent herbicides in early season",
            "Implement crop rotation to break weed cycles"
        ])
        
        return recommendations
    
    def _generate_general_recommendations(self, caption: str, visual_features: Dict[str, Any],
                                        knowledge_results: List[Dict[str, Any]], 
                                        crop_type: str) -> Dict[str, Any]:
        """Generate general agricultural recommendations"""
        recommendations = {
            'immediate_actions': [],
            'preventive_measures': [],
            'monitoring_suggestions': [],
            'treatment_options': []
        }
        
        # General crop health assessment
        green_dominant = visual_features.get('green_dominant', False)
        if green_dominant:
            recommendations['monitoring_suggestions'].append("Crop appears healthy - continue regular monitoring")
        else:
            recommendations['immediate_actions'].append("Investigate potential stress factors")
        
        # Add crop-specific recommendations from knowledge base
        for result in knowledge_results[:2]:
            if 'management' in result.get('excerpt', '').lower():
                excerpt = result.get('excerpt', '')[:200] + "..."
                recommendations['preventive_measures'].append(f"Knowledge base suggests: {excerpt}")
        
        return recommendations
    
    def _calculate_confidence(self, vision_analysis: Dict[str, Any], 
                            knowledge_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on vision analysis quality
        if vision_analysis.get('analysis_method') == 'BLIP':
            confidence += 0.2
        
        # Increase confidence based on knowledge base matches
        if knowledge_results:
            avg_relevance = np.mean([r.get('relevance_score', 0) for r in knowledge_results])
            confidence += min(0.3, avg_relevance)
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def _generate_fallback_analysis(self, analysis_type: str, crop_type: str) -> Dict[str, Any]:
        """Generate fallback analysis when main analysis fails"""
        return {
            'analysis_type': analysis_type,
            'crop_type': crop_type,
            'timestamp': datetime.now().isoformat(),
            'vision_analysis': {
                'caption': f"Analysis of {crop_type} for {analysis_type} detection",
                'analysis_method': 'fallback'
            },
            'knowledge_matches': [],
            'recommendations': {
                'immediate_actions': ["Consult with agricultural expert"],
                'preventive_measures': ["Follow standard agricultural practices"],
                'monitoring_suggestions': ["Regular field monitoring recommended"],
                'treatment_options': ["Seek professional advice for treatment options"]
            },
            'confidence_score': 0.3,
            'vlm_version': '1.0.0',
            'note': 'Fallback analysis - limited functionality'
        }

# Global VLM engine instance
vlm_engine = None

def get_vlm_engine() -> AgriVLMEngine:
    """Get or create global VLM engine instance"""
    global vlm_engine
    if vlm_engine is None:
        vlm_engine = AgriVLMEngine()
    return vlm_engine

def analyze_with_vlm(image_input: Union[str, bytes, Image.Image], 
                    analysis_type: str = 'general',
                    crop_type: str = 'unknown') -> Dict[str, Any]:
    """
    Main function to analyze images with VLM
    
    Args:
        image_input: Image data (base64, bytes, or PIL Image)
        analysis_type: Type of analysis ('disease', 'weed', 'general')
        crop_type: Type of crop being analyzed
        
    Returns:
        Comprehensive analysis results
    """
    engine = get_vlm_engine()
    return engine.generate_enhanced_analysis(image_input, analysis_type, crop_type)
