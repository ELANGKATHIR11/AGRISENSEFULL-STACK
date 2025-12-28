# Robust mock for missing ML/image libraries
class _Mock:
    def __getattr__(self, name):
        return self
    def __call__(self, *a, **k):
        return self
    def __getitem__(self, key):
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

"""
Enhanced Weed Management System with Deep Learning
Provides weed detection, classification, and management recommendations using computer vision models.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from PIL import Image
import io
import base64

# Optional imports with fallbacks
try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    import torch.nn.functional as F  # type: ignore
    import torchvision.transforms as transforms  # type: ignore
    import torchvision.models as models  # type: ignore
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = nn = F = transforms = models = _Mock()

try:
    import albumentations as A  # type: ignore
    import albumentations.pytorch  # type: ignore
except ImportError:
    A = _Mock()

try:
    import transformers  # type: ignore
except ImportError:
    transformers = _Mock()
    

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import albumentations as A  # type: ignore
    try:
        from albumentations.pytorch import ToTensorV2  # type: ignore
    except ImportError:
        ToTensorV2 = None
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False
    A = None
    ToTensorV2 = None


try:
    from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Provide a mock for segmentation if not defined
if 'segmentation' not in globals():
    segmentation = _Mock()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeedSegmentationModel:
    """Weed segmentation using deep learning models"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/weed_segmentation_model.pth"
        self.model = None
        self.device = None
        self.transform = None
        self.class_names = []
        self.model_loaded = False
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the segmentation model"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - weed segmentation disabled")
            return
        
        try:
            if TORCH_AVAILABLE and torch:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                logger.info(f"Using device: {self.device}")
            
            # Load class names
            class_names_path = os.path.join(os.path.dirname(__file__), "weed_classes.json")
            if os.path.exists(class_names_path):
                with open(class_names_path, 'r') as f:
                    self.class_names = json.load(f)
            else:
                # Default weed classes
                self.class_names = [
                    "background", "dandelion", "clover", "crabgrass", "chickweed",
                    "plantain", "lambsquarters", "pigweed", "foxtail", "bindweed",
                    "thistle", "ragweed", "purslane", "spurge", "goosegrass",
                    "nutsedge", "dock", "sorrel", "henbit", "smartweed",
                    "galinsoga", "mallow", "knotweed"
                ]
            
            # Initialize transforms
            if ALBUMENTATIONS_AVAILABLE and A:
                # ToTensorV2 is available if albumentations.pytorch is present
                transforms_list = [
                    A.Resize(height=512, width=512),
                    A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                    getattr(A, 'ToTensorV2', lambda: _Mock())()
                ]
                self.transform = A.Compose(transforms_list)  # type: ignore
            elif TORCH_AVAILABLE and transforms:
                self.transform = transforms.Compose([
                    transforms.Resize((512, 512)),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
            else:
                self.transform = None
            
            # Try to load custom model
            if os.path.exists(self.model_path):
                self._load_custom_model()
            else:
                self._load_pretrained_model()
                
        except Exception as e:
            logger.error(f"Failed to initialize weed segmentation model: {e}")
    
    def _load_custom_model(self):
        """Load custom trained model"""
        try:
            if TORCH_AVAILABLE and torch and self.model_path:
                checkpoint = torch.load(self.model_path, map_location=self.device)  # type: ignore
                
                # Create model architecture
                self.model = segmentation.deeplabv3_resnet50(  # type: ignore
                    pretrained=False,
                    num_classes=len(self.class_names)
                )
            else:
                logger.warning("Custom model loading skipped - torch not available or model path not provided")
                return
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"Loaded custom weed segmentation model from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load custom model: {e}")
            self._load_pretrained_model()
    
    def _load_pretrained_model(self):
        """Load pretrained model as fallback"""
        try:
            if getattr(transformers, 'AutoImageProcessor', None) and getattr(transformers, 'AutoModelForSemanticSegmentation', None):
                # Use only compatible segmentation models (SegFormer, UPerNet, DPT, etc.)
                # Skip DETR and other incompatible architectures.
                # Try models that are explicitly supported by AutoModelForSemanticSegmentation
                possible_models = [
                    "nvidia/segformer-b0-ade20k",    # SegFormer - lightweight and robust
                    "openmmlab/upernet-convnext-tiny",  # UPerNet with ConvNeXt - accurate
                    "Intel/dpt-tiny-ade20k",  # DPT - good for edge detection
                ]
                selected = None
                selected_error = None
                
                for model_name in possible_models:
                    try:
                        config = transformers.AutoConfig.from_pretrained(model_name)
                        cfg_class = config.__class__.__name__.lower()
                        
                        # Skip DETR and incompatible configs
                        if 'detr' in cfg_class or 'detrconfig' in cfg_class:
                            logger.warning(f"Skipping DETR-incompatible model: {model_name} (config: {cfg_class})")
                            continue
                        
                        # Try to load and validate
                        logger.info(f"Attempting to load segmentation model: {model_name}")
                        processor = transformers.AutoImageProcessor.from_pretrained(model_name)
                        model = transformers.AutoModelForSemanticSegmentation.from_pretrained(model_name)
                        
                        # If we get here, model loaded successfully
                        self.processor = processor
                        self.model = model
                        self.model.to(self.device)
                        self.model.eval()
                        selected = model_name
                        logger.info(f"Successfully loaded Hugging Face segmentation model: {selected}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load {model_name}: {e}")
                        selected_error = str(e)
                        continue

                if selected is None:
                    # No compatible segmentation HF model found, fall back to torchvision DeepLabV3
                    logger.warning(f"No compatible HF semantic segmentation model loaded (last error: {selected_error}); falling back to PyTorch DeepLabV3")
                    raise RuntimeError("No compatible HF semantic segmentation model found")

            else:
                # Use PyTorch pretrained model (fallback when transformers not available)
                logger.info("Using PyTorch pretrained DeepLabV3-ResNet50 for segmentation")
                self.model = segmentation.deeplabv3_resnet50(  # type: ignore
                    pretrained=True,
                    num_classes=21  # COCO classes
                )
                self.model.to(self.device)
                self.model.eval()
                logger.info("Loaded PyTorch pretrained segmentation model")
            
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load pretrained model: {e}")
            # Ensure we don't leave model_loaded in a partial state
            self.model = None
            self.model_loaded = False
            # As a last-resort fallback we keep the classification model available and allow segmentation to be skipped
    
    def segment_weeds(self, image: np.ndarray) -> Dict[str, Any]:
        """Segment weeds in the image"""
        if not self.model_loaded:
            return {
                "success": False,
                "error": "Model not loaded",
                "segments": [],
                "weed_coverage": 0.0
            }
        
        try:
            # Check if models are available
            if not TORCH_AVAILABLE or not torch or self.model is None:
                logger.warning("Segmentation skipped - torch or model not available")
                return {
                    "segments": [],
                    "confidence": 0.0,
                    "weed_coverage": 0.0
                }
            
            # Preprocess image
            if ALBUMENTATIONS_AVAILABLE and self.transform and hasattr(self.transform, '__call__'):
                try:
                    # Try albumentations call format
                    if hasattr(self.transform, '__call__'):
                        # Try with image parameter first
                        try:
                            augmented = self.transform(img=image)
                        except TypeError:
                            # Fallback to positional argument
                            augmented = self.transform(img=image)
                        
                        if isinstance(augmented, dict) and 'image' in augmented:
                            input_tensor = augmented['image']
                            if hasattr(input_tensor, 'unsqueeze'):
                                input_tensor = input_tensor.unsqueeze(0).to(self.device)
                            else:
                                logger.warning("Albumentations transform did not return tensor")
                                return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
                        else:
                            logger.warning("Albumentations transform did not return expected format")
                            return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
                    else:
                        logger.warning("Transform is not callable")
                        return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
                except TypeError:
                    # Fallback to torchvision format
                    pil_image = Image.fromarray(image)
                    transformed = self.transform(pil_image)
                    if TORCH_AVAILABLE and torch and hasattr(transformed, 'unsqueeze') and hasattr(transformed, 'to'):
                        input_tensor = transformed.unsqueeze(0).to(self.device)  # type: ignore
                    else:
                        logger.warning("Transform did not return tensor")
                        return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
            elif self.transform and hasattr(self.transform, '__call__'):
                pil_image = Image.fromarray(image)
                transformed = self.transform(pil_image)
                if TORCH_AVAILABLE and torch and hasattr(transformed, 'unsqueeze') and hasattr(transformed, 'to'):
                    input_tensor = transformed.unsqueeze(0).to(self.device)  # type: ignore
                else:
                    logger.warning("Transform did not return tensor")
                    return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
            else:
                logger.warning("No transform available")
                return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
            
            # Run inference
            if hasattr(torch, 'no_grad'):
                with torch.no_grad():
                    if TRANSFORMERS_AVAILABLE and hasattr(self, 'processor'):
                        # Hugging Face model
                        inputs = self.processor(images=image, return_tensors="pt")
                        outputs = self.model(**inputs.to(self.device))  # type: ignore
                        segmentation_map = outputs.logits.argmax(dim=1).cpu().numpy()[0]
                    else:
                        # PyTorch model
                        outputs = self.model(input_tensor)
                        segmentation_map = outputs['out'].argmax(dim=1).cpu().numpy()[0]
            else:
                logger.warning("torch.no_grad not available")
                return {"segments": [], "confidence": 0.0, "weed_coverage": 0.0}
            
            # Analyze segmentation results
            if len(image.shape) >= 2:
                segments = self._analyze_segments(segmentation_map, (image.shape[0], image.shape[1]))  # type: ignore
            else:
                segments = self._analyze_segments(segmentation_map, (512, 512))  # type: ignore
            weed_coverage = self._calculate_weed_coverage(segmentation_map)  # type: ignore
            
            return {
                "success": True,
                "segments": segments,
                "weed_coverage": weed_coverage,
                "segmentation_map": segmentation_map.tolist(),
                "class_names": self.class_names
            }
            
        except Exception as e:
            logger.error(f"Weed segmentation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "segments": [],
                "weed_coverage": 0.0
            }
    
    def _analyze_segments(self, segmentation_map: np.ndarray, original_shape: Tuple[int, int]) -> List[Dict]:
        """Analyze segmentation results to identify weed instances"""
        segments = []
        
        try:
            # Find unique classes (excluding background)
            unique_classes = np.unique(segmentation_map)
            
            for class_id in unique_classes:
                if class_id == 0:  # Skip background
                    continue
                
                # Create mask for this class
                mask = (segmentation_map == class_id).astype(np.uint8)
                
                # Find contours if OpenCV available
                if CV2_AVAILABLE and cv2:
                    try:
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        
                        for contour in contours:
                            area = cv2.contourArea(contour)
                            if area > 100:  # Filter small segments
                                x, y, w, h = cv2.boundingRect(contour)
                                
                                segments.append({
                                    "class_id": int(class_id),
                                    "class_name": self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}",
                                    "bbox": [x, y, w, h],
                                    "area": float(area),
                                    "confidence": 0.8  # Default confidence
                                })
                    except Exception as e:
                        logger.warning(f"Error processing contours: {e}")
                else:
                    # Fallback without OpenCV
                    area = np.sum(mask)
                    if area > 100:
                        segments.append({
                            "class_id": int(class_id),
                            "class_name": self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}",
                            "area": float(area),
                            "confidence": 0.8
                        })
        
        except Exception as e:
            logger.error(f"Segment analysis failed: {e}")
        
        return segments
    
    def _calculate_weed_coverage(self, segmentation_map: np.ndarray) -> float:
        """Calculate percentage of image covered by weeds"""
        try:
            total_pixels = segmentation_map.size
            weed_pixels = np.sum(segmentation_map > 0)  # Non-background pixels
            return float(weed_pixels / total_pixels * 100)
        except:
            return 0.0

class WeedClassificationModel:
    """Weed classification using CNN models"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "models/weed_classification_model.pth"
        self.model = None
        self.device = None
        self.transform = None
        self.class_names = []
        self.model_loaded = False
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the classification model"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - weed classification disabled")
            return
        
        try:
            if TORCH_AVAILABLE and torch:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.device = "cpu"
            
            # Load class names
            class_names_path = os.path.join(os.path.dirname(__file__), "weed_classes.json")
            if os.path.exists(class_names_path):
                with open(class_names_path, 'r') as f:
                    self.class_names = json.load(f)
            else:
                self.class_names = [
                    "dandelion", "clover", "crabgrass", "chickweed", "plantain",
                    "lambsquarters", "pigweed", "foxtail", "bindweed", "thistle",
                    "ragweed", "purslane", "spurge", "goosegrass", "nutsedge",
                    "dock", "sorrel", "henbit", "smartweed", "galinsoga",
                    "mallow", "knotweed"
                ]
            
            # Initialize transforms
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Try to load model
            if os.path.exists(self.model_path):
                self._load_custom_model()
            else:
                self._load_pretrained_model()
                
        except Exception as e:
            logger.error(f"Failed to initialize weed classification model: {e}")
    
    def _load_custom_model(self):
        """Load custom trained classification model"""
        try:
            if not TORCH_AVAILABLE or not torch or not self.model_path:
                logger.warning("Custom model loading skipped - torch not available or model path not provided")
                return
                
            checkpoint = torch.load(self.model_path, map_location=self.device)  # type: ignore
            
            # Create model architecture (assuming ResNet50)
            self.model = models.resnet50(pretrained=False)
            self.model.fc = nn.Linear(self.model.fc.in_features, len(self.class_names))  # type: ignore
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"Loaded custom weed classification model from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load custom classification model: {e}")
            self._load_pretrained_model()
    
    def _load_pretrained_model(self):
        """Load pretrained model as fallback"""
        try:
            self.model = models.resnet50(pretrained=True)
            self.model.fc = nn.Linear(self.model.fc.in_features, len(self.class_names))  # type: ignore
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
            logger.info("Loaded pretrained ResNet50 for weed classification")
            
        except Exception as e:
            logger.error(f"Failed to load pretrained classification model: {e}")
    
    def classify_weed(self, image: np.ndarray) -> Dict[str, Any]:
        """Classify weed type in the image"""
        if not self.model_loaded:
            return {
                "success": False,
                "error": "Model not loaded",
                "predictions": []
            }
        
        try:
            # Check if torch is available and model is loaded
            if not TORCH_AVAILABLE or not torch or self.model is None or self.transform is None:
                return {
                    "success": False,
                    "error": "Model or transform not available",
                    "predictions": []
                }
            
            # Preprocess image
            pil_image = Image.fromarray(image)
            transformed = self.transform(pil_image)
            if TORCH_AVAILABLE and torch and hasattr(transformed, 'unsqueeze') and hasattr(transformed, 'to'):
                input_tensor = transformed.unsqueeze(0).to(self.device)  # type: ignore
            else:
                return {
                    "success": False,
                    "error": "Transform did not return tensor",
                    "predictions": []
                }
            
            # Run inference
            if hasattr(torch, 'no_grad'):
                with torch.no_grad():
                    outputs = self.model(input_tensor)
                    if hasattr(torch, 'nn') and hasattr(torch.nn, 'functional') and F is not None:
                        # Ensure outputs[0] is a tensor-like object before calling F.softmax
                        try:
                            from typing import cast, Any as _Any
                            out0 = outputs[0]
                            # Cast to Any to appease static typing when tests/mock frameworks produce _Mock types
                            out0_any = cast(_Any, out0)
                            if hasattr(out0, 'dim') or (TORCH_AVAILABLE and torch is not None and hasattr(torch, 'is_tensor') and torch.is_tensor(out0)):
                                probabilities = F.softmax(out0_any, dim=0)
                            else:
                                # Fallback: treat as ndarray-like and compute numpy softmax
                                arr = np.asarray(outputs[0])
                                ex = np.exp(arr - np.max(arr))
                                probabilities = ex / np.sum(ex)
                        except Exception:
                            arr = np.asarray(outputs[0])
                            ex = np.exp(arr - np.max(arr))
                            probabilities = ex / np.sum(ex)
                    else:
                        return {
                            "success": False,
                            "error": "torch.nn.functional not available",
                            "predictions": []
                        }
            else:
                return {
                    "success": False,
                    "error": "torch.no_grad not available",
                    "predictions": []
                }
            
            # Get top predictions
            if hasattr(torch, 'topk'):
                top_prob, top_class = torch.topk(probabilities, min(5, len(self.class_names)))  # type: ignore
            else:
                return {
                    "success": False,
                    "error": "torch.topk not available",
                    "predictions": []
                }
            
            predictions = []
            for i in range(len(top_prob)):  # type: ignore
                class_idx = int(top_class[i].item()) if hasattr(top_class[i], 'item') else int(top_class[i])  # type: ignore
                if class_idx < len(self.class_names):
                    predictions.append({
                        "class_name": self.class_names[class_idx],
                        "confidence": float(top_prob[i].item()) if hasattr(top_prob[i], 'item') else float(top_prob[i]),  # type: ignore
                        "class_id": class_idx
                    })
            
            return {
                "success": True,
                "predictions": predictions,
                "top_prediction": predictions[0] if predictions else None
            }
            
        except Exception as e:
            logger.error(f"Weed classification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }

class WeedManagementEngine:
    """Enhanced weed management with ML-based detection and recommendations"""
    
    def __init__(self):
        self.segmentation_model = WeedSegmentationModel()
        self.classification_model = WeedClassificationModel()
        
        # Load weed management database
        self.weed_database = self._load_weed_database()
        
        # Load herbicide database
        self.herbicide_database = self._load_herbicide_database()
    
    def _load_weed_database(self) -> Dict[str, Dict]:
        """Load comprehensive weed information database"""
        weed_db_path = os.path.join(os.path.dirname(__file__), "weed_management_database.json")
        
        if os.path.exists(weed_db_path):
            with open(weed_db_path, 'r') as f:
                return json.load(f)
        else:
            # Default weed database
            return {
                "dandelion": {
                    "scientific_name": "Taraxacum officinale",
                    "type": "broadleaf_perennial",
                    "growth_habit": "rosette",
                    "season": "cool_season",
                    "reproduction": "seeds_and_roots",
                    "control_difficulty": "moderate",
                    "herbicides": ["2,4-D", "dicamba", "MCPP"],
                    "cultural_controls": ["dense_turf", "proper_fertilization"],
                    "timing": "spring_and_fall"
                },
                "crabgrass": {
                    "scientific_name": "Digitaria sanguinalis",
                    "type": "grass_annual",
                    "growth_habit": "prostrate",
                    "season": "warm_season",
                    "reproduction": "seeds",
                    "control_difficulty": "easy_with_preemergent",
                    "herbicides": ["pre-emergent", "quinclorac", "fenoxaprop"],
                    "cultural_controls": ["thick_turf", "proper_watering"],
                    "timing": "early_spring_preemergent"
                },
                "clover": {
                    "scientific_name": "Trifolium repens",
                    "type": "broadleaf_perennial",
                    "growth_habit": "creeping",
                    "season": "cool_season",
                    "reproduction": "seeds_and_stolons",
                    "control_difficulty": "moderate",
                    "herbicides": ["triclopyr", "MCPP", "dicamba"],
                    "cultural_controls": ["nitrogen_fertilization", "overseeding"],
                    "timing": "spring_and_fall"
                }
            }
    
    def _load_herbicide_database(self) -> Dict[str, Dict]:
        """Load herbicide information database"""
        return {
            "2,4-D": {
                "type": "selective_broadleaf",
                "mode_of_action": "auxin_mimic",
                "target_weeds": ["dandelion", "plantain", "clover"],
                "application_rate": "1-2 lb/acre",
                "timing": "active_growth",
                "precautions": ["temperature_sensitive", "drift_sensitive"]
            },
            "glyphosate": {
                "type": "non_selective",
                "mode_of_action": "EPSP_synthase_inhibitor",
                "target_weeds": ["all_weeds"],
                "application_rate": "1-4 lb/acre",
                "timing": "active_growth",
                "precautions": ["non_selective", "resistance_concerns"]
            },
            "pre-emergent": {
                "type": "preventive",
                "mode_of_action": "cell_division_inhibitor",
                "target_weeds": ["crabgrass", "annual_weeds"],
                "application_rate": "varies",
                "timing": "before_germination",
                "precautions": ["timing_critical", "irrigation_needed"]
            }
        }
    
    def analyze_image(self, image_data: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze uploaded image for weed detection and identification"""
        try:
            # Decode base64 image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image.convert('RGB'))
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": analysis_type,
                "image_info": {
                    "width": image_array.shape[1],
                    "height": image_array.shape[0],
                    "channels": image_array.shape[2]
                }
            }
            
            if analysis_type in ["comprehensive", "segmentation"]:
                # Perform segmentation
                segmentation_result = self.segmentation_model.segment_weeds(image_array)
                result["segmentation"] = segmentation_result
            
            if analysis_type in ["comprehensive", "classification"]:
                # Perform classification
                classification_result = self.classification_model.classify_weed(image_array)
                result["classification"] = classification_result
            
            if analysis_type == "comprehensive":
                # Generate management recommendations
                recommendations = self._generate_management_recommendations(result)
                result["recommendations"] = recommendations
            
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_management_recommendations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate weed management recommendations based on analysis"""
        recommendations = {
            "immediate_actions": [],
            "herbicide_recommendations": [],
            "cultural_controls": [],
            "timing_recommendations": [],
            "monitoring_advice": [],
            "severity_assessment": "low"
        }
        
        try:
            detected_weeds = set()  # Initialize detected_weeds set
            
            # Analyze segmentation results
            if "segmentation" in analysis_result and analysis_result["segmentation"]["success"]:
                weed_coverage = analysis_result["segmentation"]["weed_coverage"]
                segments = analysis_result["segmentation"]["segments"]
                
                # Assess severity
                if weed_coverage > 50:
                    recommendations["severity_assessment"] = "high"
                elif weed_coverage > 20:
                    recommendations["severity_assessment"] = "moderate"
                else:
                    recommendations["severity_assessment"] = "low"
                
                # Generate recommendations based on detected weeds
                for segment in segments:
                    weed_name = segment["class_name"]
                    if weed_name in self.weed_database:
                        detected_weeds.add(weed_name)
            
            # Analyze classification results
            if "classification" in analysis_result and analysis_result["classification"]["success"]:
                top_prediction = analysis_result["classification"]["top_prediction"]
                if top_prediction and top_prediction["confidence"] > 0.5:
                    detected_weeds.add(top_prediction["class_name"])
            
            # Generate specific recommendations for detected weeds
            for weed_name in detected_weeds:
                if weed_name in self.weed_database:
                    weed_info = self.weed_database[weed_name]
                    
                    # Herbicide recommendations
                    for herbicide in weed_info.get("herbicides", []):
                        if herbicide in self.herbicide_database:
                            herb_info = self.herbicide_database[herbicide]
                            recommendations["herbicide_recommendations"].append({
                                "herbicide": herbicide,
                                "target_weed": weed_name,
                                "application_rate": herb_info["application_rate"],
                                "timing": herb_info["timing"],
                                "precautions": herb_info["precautions"]
                            })
                    
                    # Cultural controls
                    recommendations["cultural_controls"].extend(
                        weed_info.get("cultural_controls", [])
                    )
                    
                    # Timing recommendations
                    recommendations["timing_recommendations"].append({
                        "weed": weed_name,
                        "optimal_timing": weed_info.get("timing", "consult_expert")
                    })
            
            # General recommendations based on severity
            if recommendations["severity_assessment"] == "high":
                recommendations["immediate_actions"] = [
                    "Consider professional consultation",
                    "Implement integrated approach",
                    "Monitor closely after treatment"
                ]
            elif recommendations["severity_assessment"] == "moderate":
                recommendations["immediate_actions"] = [
                    "Apply targeted herbicide treatment",
                    "Improve cultural practices",
                    "Schedule follow-up treatment"
                ]
            else:
                recommendations["immediate_actions"] = [
                    "Continue monitoring",
                    "Maintain good cultural practices",
                    "Spot treat if necessary"
                ]
            
            # Monitoring advice
            recommendations["monitoring_advice"] = [
                "Check treated areas in 2-3 weeks",
                "Document treatment effectiveness",
                "Watch for resistance development",
                "Monitor for new weed emergence"
            ]
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations["error"] = str(e)
        
        return recommendations
    
    def get_weed_info(self, weed_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific weed"""
        weed_name = weed_name.lower()
        
        if weed_name in self.weed_database:
            return {
                "success": True,
                "weed_info": self.weed_database[weed_name],
                "herbicide_details": {
                    herb: self.herbicide_database.get(herb, {})
                    for herb in self.weed_database[weed_name].get("herbicides", [])
                }
            }
        else:
            return {
                "success": False,
                "error": f"Weed '{weed_name}' not found in database",
                "available_weeds": list(self.weed_database.keys())
            }
    
    def get_treatment_plan(self, field_conditions: Dict[str, Any], detected_weeds: List[str]) -> Dict[str, Any]:
        """Generate comprehensive treatment plan"""
        try:
            treatment_plan = {
                "field_assessment": field_conditions,
                "detected_weeds": detected_weeds,
                "treatment_phases": [],
                "estimated_cost": 0.0,
                "expected_efficacy": 0.0,
                "environmental_considerations": []
            }
            
            # Phase 1: Pre-emergent treatment (if applicable)
            pre_emergent_weeds = [
                weed for weed in detected_weeds
                if weed in self.weed_database and 
                "pre-emergent" in self.weed_database[weed].get("herbicides", [])
            ]
            
            if pre_emergent_weeds:
                treatment_plan["treatment_phases"].append({
                    "phase": 1,
                    "timing": "early_spring",
                    "treatment_type": "pre_emergent",
                    "target_weeds": pre_emergent_weeds,
                    "herbicides": ["pre-emergent"],
                    "application_method": "broadcast",
                    "estimated_cost": 150.0
                })
            
            # Phase 2: Post-emergent treatment
            post_emergent_weeds = [
                weed for weed in detected_weeds
                if weed in self.weed_database
            ]
            
            if post_emergent_weeds:
                herbicides = set()
                for weed in post_emergent_weeds:
                    herbicides.update(self.weed_database[weed].get("herbicides", []))
                
                treatment_plan["treatment_phases"].append({
                    "phase": 2,
                    "timing": "active_growth",
                    "treatment_type": "post_emergent",
                    "target_weeds": post_emergent_weeds,
                    "herbicides": list(herbicides),
                    "application_method": "selective_spray",
                    "estimated_cost": 200.0
                })
            
            # Calculate totals
            treatment_plan["estimated_cost"] = sum(
                phase["estimated_cost"] for phase in treatment_plan["treatment_phases"]
            )
            
            # Environmental considerations
            treatment_plan["environmental_considerations"] = [
                "Avoid application before rain",
                "Consider pollinator activity",
                "Follow label instructions",
                "Use IPM principles",
                "Monitor water sources"
            ]
            
            return treatment_plan
            
        except Exception as e:
            logger.error(f"Failed to generate treatment plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Initialize global engine instance
weed_engine = WeedManagementEngine()

def analyze_weed_image(image_data: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
    """Main function for weed image analysis"""
    return weed_engine.analyze_image(image_data, analysis_type)

def get_weed_recommendations(weed_list: List[str], field_conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get management recommendations for detected weeds"""
    if field_conditions is None:
        field_conditions = {}
    
    return weed_engine.get_treatment_plan(field_conditions, weed_list)

def get_weed_database_info(weed_name: Optional[str] = None) -> Dict[str, Any]:
    """Get weed database information"""
    if weed_name:
        return weed_engine.get_weed_info(weed_name)
    else:
        return {
            "available_weeds": list(weed_engine.weed_database.keys()),
            "total_weeds": len(weed_engine.weed_database),
            "herbicides": list(weed_engine.herbicide_database.keys())
        }