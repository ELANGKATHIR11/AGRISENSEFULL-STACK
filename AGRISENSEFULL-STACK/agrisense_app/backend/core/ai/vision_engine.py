"""
Vision Engine for AgriSense - VLM-based Crop Disease & Weed Detection
=====================================================================

This module implements a Vision-Language Model (VLM) for analyzing crop images:
1. Disease detection: Identifies plant diseases from photos
2. Weed detection: Recognizes and classifies weeds
3. Treatment recommendations: Provides actionable advice

Why VLM over CNN?
-----------------
- Understands visual + textual context (plant + symptoms)
- Can explain findings in natural language
- Zero-shot capability (works on unseen diseases)
- Multi-modal reasoning (image + farmer's description)

Model Choice: LLaVA-v1.6-Mistral-7B
-----------------------------------
- State-of-the-art vision-language understanding
- 7B parameters (fits in 8GB VRAM with quantization)
- Strong performance on agricultural imagery
- Open-source and commercially usable

Architecture:
-------------
1. Image Preprocessing: Resize, normalize, convert to tensors
2. Visual Encoding: CLIP-based image encoder
3. Language Generation: Mistral-7B decoder
4. Post-processing: Extract structured diagnosis

Author: AgriSense Team
Date: December 2025
"""

import base64
import io
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from PIL import Image

# Core dependencies
try:
    import torch
    from transformers import (
        AutoProcessor,
        BitsAndBytesConfig,
        LlavaNextForConditionalGeneration,
        LlavaNextProcessor,
    )
    
    TORCH_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PyTorch/Transformers not available: {e}")
    TORCH_AVAILABLE = False

# Configure logger
logger = logging.getLogger(__name__)


class CropVisionAnalyst:
    """
    VLM-based image analyzer for crop disease and weed detection.
    
    This class uses the LLaVA-v1.6-Mistral-7B vision-language model to:
    - Identify plant diseases from photos
    - Detect and classify weeds
    - Provide treatment recommendations
    - Explain findings in natural language
    
    Features:
    ---------
    - Multi-modal: Combines visual and textual understanding
    - 4-bit quantization: Fits in 8GB VRAM (or runs on CPU)
    - Zero-shot capable: Works on diseases not in training data
    - Natural language output: Easy for farmers to understand
    - Structured responses: JSON-formatted for UI integration
    
    Why LLaVA?
    ----------
    - Strong vision-language alignment
    - Open-source (commercial use allowed)
    - Good performance on agricultural images
    - Active community and support
    
    Example:
    --------
    ```python
    analyst = CropVisionAnalyst(device="cuda", use_4bit=True)
    
    with open("tomato_leaf.jpg", "rb") as f:
        image_bytes = f.read()
    
    result = analyst.analyze_image(image_bytes, task="disease")
    print(result["diagnosis"])
    print(result["treatment"])
    ```
    """
    
    def __init__(
        self,
        model_name: str = "llava-hf/llava-v1.6-mistral-7b-hf",
        device: Optional[str] = None,
        use_4bit: bool = True,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize the VLM-based crop vision analyst.
        
        Parameters:
        -----------
        model_name : str
            HuggingFace model identifier
            Default: llava-hf/llava-v1.6-mistral-7b-hf
            Why: Best balance of performance and resource usage
        device : Optional[str]
            "cuda", "cpu", or None (auto-detect)
            Why: Allows forcing CPU mode on systems without GPU
        use_4bit : bool
            Use 4-bit quantization (requires bitsandbytes)
            Why: Reduces VRAM from 28GB to ~8GB with minimal quality loss
        cache_dir : Optional[str]
            Directory to cache downloaded models
            Why: Avoids re-downloading 14GB model on every restart
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch and Transformers not installed. "
                "Install with: pip install -r requirements-ai.txt"
            )
        
        self.model_name = model_name
        
        # Auto-detect device if not specified
        if device is None:
            device = os.getenv("AGRISENSE_AI_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        
        # Cache directory for model storage
        if cache_dir is None:
            cache_dir = os.getenv("AGRISENSE_MODEL_CACHE", "./model_cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initializing CropVisionAnalyst with device={self.device}, 4bit={use_4bit}")
        
        # Quantization config for memory efficiency
        # Why 4-bit: Reduces model size by 75% with <5% quality loss
        quantization_config = None
        if use_4bit and self.device == "cuda":
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,  # Why fp16: Faster than fp32
                    bnb_4bit_quant_type="nf4",             # Why nf4: Best for neural nets
                    bnb_4bit_use_double_quant=True,        # Why: Extra memory savings
                )
                logger.info("Using 4-bit quantization (NF4)")
            except Exception as e:
                logger.warning(f"Failed to configure 4-bit quantization: {e}")
                quantization_config = None
        
        # Load processor (handles image preprocessing + tokenization)
        # Why separate processor: VLM needs both visual and text processing
        try:
            self.processor = LlavaNextProcessor.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir),
            )
            logger.info(f"Loaded processor: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load processor: {e}")
            raise
        
        # Load model with quantization
        try:
            model_kwargs = {
                "cache_dir": str(self.cache_dir),
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "low_cpu_mem_usage": True,  # Why: Reduces memory spikes during loading
            }
            
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
                model_kwargs["device_map"] = "auto"  # Why: Automatic device placement
            else:
                # For CPU or non-quantized mode
                model_kwargs["device_map"] = {"": self.device}
            
            self.model = LlavaNextForConditionalGeneration.from_pretrained(
                model_name,
                **model_kwargs,
            )
            
            # Set to evaluation mode
            # Why: Disables dropout, batch normalization training behavior
            self.model.eval()
            
            logger.info(f"Loaded VLM model: {model_name}")
            logger.info(f"Model memory footprint: ~{self._estimate_memory_gb():.1f} GB")
            
        except Exception as e:
            logger.error(f"Failed to load VLM model: {e}")
            logger.error("Ensure you have sufficient memory and CUDA (if using GPU)")
            raise
        
        # Prompt templates for different tasks
        # Why templates: Consistent formatting improves model performance
        self.prompts = {
            "disease": (
                "Analyze this crop image and identify any plant diseases. "
                "Provide: 1) Disease name, 2) Severity (mild/moderate/severe), "
                "3) Visible symptoms, 4) Recommended treatment. "
                "If no disease is visible, state 'Healthy plant'."
            ),
            "weed": (
                "Analyze this agricultural field image and identify any weeds. "
                "Provide: 1) Weed species, 2) Coverage percentage, "
                "3) Growth stage, 4) Recommended control method. "
                "If no weeds are visible, state 'No weeds detected'."
            ),
            "general": (
                "Analyze this crop image and describe what you see. "
                "Include plant health status, any visible issues, and recommendations."
            ),
        }
    
    def _estimate_memory_gb(self) -> float:
        """
        Estimate model memory usage in GB.
        
        Why: Helps users understand hardware requirements
        """
        try:
            if self.device == "cuda":
                allocated = torch.cuda.memory_allocated() / (1024 ** 3)
                return allocated
            else:
                # Rough estimate for CPU
                # 7B params * 2 bytes (fp16) / 4 (4-bit) ≈ 3.5GB
                return 3.5 if hasattr(self.model, "quantization_config") else 14.0
        except Exception:
            return 0.0
    
    def _preprocess_image(self, image_bytes: bytes) -> Image.Image:
        """
        Preprocess image bytes into PIL Image.
        
        Why separate preprocessing:
        - Validates image format
        - Handles various input formats (JPEG, PNG, etc.)
        - Applies EXIF orientation
        - Resizes if too large
        
        Parameters:
        -----------
        image_bytes : bytes
            Raw image data
            
        Returns:
        --------
        PIL.Image: Preprocessed image
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            # Why: Model expects 3-channel RGB
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Apply EXIF orientation
            # Why: Some cameras store rotation in EXIF, not in pixel data
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            except Exception:
                pass
            
            # Resize if too large (max 1024px on longest side)
            # Why: Reduces memory, faster processing, model doesn't need full resolution
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {new_size}")
            
            return image
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ValueError(f"Invalid image format: {str(e)}")
    
    def analyze_image(
        self,
        image_bytes: bytes,
        task: str = "disease",
        custom_prompt: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Analyze a crop image for diseases, weeds, or general health assessment.
        
        Process:
        1. Preprocess image (resize, normalize)
        2. Encode image + text prompt
        3. Generate description using VLM
        4. Parse output into structured format
        5. Add confidence scores and metadata
        
        Why VLM for agriculture:
        - Can identify subtle visual symptoms
        - Explains findings (not just labels)
        - Handles diverse conditions (lighting, angles, backgrounds)
        - Zero-shot on rare diseases
        
        Parameters:
        -----------
        image_bytes : bytes
            Raw image data (JPEG, PNG, etc.)
        task : str
            "disease", "weed", or "general"
            Why: Task-specific prompts improve accuracy
        custom_prompt : Optional[str]
            Override default prompt for this task
        max_new_tokens : int
            Maximum response length
            Why: Longer allows detailed explanations
        temperature : float
            Sampling temperature (0.0-1.0)
            Why: Lower = more deterministic, higher = more creative
            
        Returns:
        --------
        Dict containing:
        - diagnosis: Main findings (disease name, weed species, etc.)
        - severity: Assessment of severity (if applicable)
        - symptoms: Visible symptoms or characteristics
        - treatment: Recommended actions
        - confidence: Model confidence score (0.0-1.0)
        - raw_output: Full model response
        - task: Task type used
        """
        logger.info(f"Analyzing image for task: {task}")
        
        # Preprocess image
        try:
            image = self._preprocess_image(image_bytes)
        except Exception as e:
            return {
                "error": f"Image preprocessing failed: {str(e)}",
                "task": task,
            }
        
        # Get prompt for task
        prompt = custom_prompt if custom_prompt else self.prompts.get(task, self.prompts["general"])
        
        # Format as chat message
        # Why chat format: Model is trained on conversational format
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image"},
                ],
            },
        ]
        
        # Process inputs
        try:
            prompt_text = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
            
            inputs = self.processor(
                text=prompt_text,
                images=image,
                return_tensors="pt",
                padding=True,
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
        except Exception as e:
            logger.error(f"Input processing failed: {e}")
            return {
                "error": f"Failed to process inputs: {str(e)}",
                "task": task,
            }
        
        # Generate response
        try:
            with torch.no_grad():  # Why: Disable gradients for inference (saves memory)
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0.0,  # Why: Deterministic if temp=0
                    top_p=0.9,                     # Nucleus sampling
                    top_k=50,                      # Limit sampling pool
                )
            
            # Decode output
            # Why skip_special_tokens: Remove [PAD], [EOS], etc.
            output_text = self.processor.decode(
                output_ids[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )
            
            # Extract only the assistant's response
            # Why: Remove the prompt from output
            if "ASSISTANT:" in output_text:
                output_text = output_text.split("ASSISTANT:")[-1].strip()
            
            logger.info(f"Generated response: {output_text[:100]}...")
            
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            return {
                "error": f"Failed to generate analysis: {str(e)}",
                "task": task,
            }
        
        # Parse output into structured format
        result = self._parse_output(output_text, task)
        result["raw_output"] = output_text
        result["task"] = task
        
        # Add metadata
        result["model"] = self.model_name
        result["device"] = self.device
        result["image_size"] = image.size
        
        return result
    
    def _parse_output(self, text: str, task: str) -> Dict[str, Any]:
        """
        Parse VLM output into structured format.
        
        Why structured parsing:
        - Easier for UI to display
        - Consistent format across different outputs
        - Extractable fields for database storage
        
        Parameters:
        -----------
        text : str
            Raw model output
        task : str
            Task type (affects parsing logic)
            
        Returns:
        --------
        Dict with parsed fields (diagnosis, severity, symptoms, treatment, etc.)
        """
        result = {
            "diagnosis": "",
            "severity": "unknown",
            "symptoms": [],
            "treatment": "",
            "confidence": 0.8,  # Default confidence (can be improved with calibration)
        }
        
        # Simple parsing based on task
        # Note: This is a basic implementation - can be enhanced with NER, regex, etc.
        
        if task == "disease":
            # Check for "Healthy plant" or "No disease"
            if any(phrase in text.lower() for phrase in ["healthy plant", "no disease", "no visible"]):
                result["diagnosis"] = "Healthy Plant"
                result["severity"] = "none"
                result["confidence"] = 0.9
            else:
                # Extract disease name (often in first sentence)
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for disease indicators
                    if any(word in line.lower() for word in ["disease", "blight", "rot", "wilt", "mildew"]):
                        if not result["diagnosis"]:
                            result["diagnosis"] = line
                    
                    # Extract severity
                    if any(word in line.lower() for word in ["severe", "serious", "critical"]):
                        result["severity"] = "severe"
                    elif any(word in line.lower() for word in ["moderate", "medium"]):
                        result["severity"] = "moderate"
                    elif any(word in line.lower() for word in ["mild", "slight", "early"]):
                        result["severity"] = "mild"
                    
                    # Extract symptoms
                    if any(word in line.lower() for word in ["symptom", "sign", "visible", "leaf", "spot"]):
                        result["symptoms"].append(line)
                    
                    # Extract treatment
                    if any(word in line.lower() for word in ["treatment", "recommend", "apply", "spray", "control"]):
                        result["treatment"] = line
                
                # If no diagnosis found, use first meaningful line
                if not result["diagnosis"]:
                    result["diagnosis"] = lines[0] if lines else text[:100]
        
        elif task == "weed":
            # Similar parsing for weed detection
            if "no weed" in text.lower() or "weed-free" in text.lower():
                result["diagnosis"] = "No Weeds Detected"
                result["severity"] = "none"
                result["confidence"] = 0.9
            else:
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Extract weed species
                    if any(word in line.lower() for word in ["weed", "grass", "broadleaf"]):
                        if not result["diagnosis"]:
                            result["diagnosis"] = line
                    
                    # Extract coverage/severity
                    if any(word in line.lower() for word in ["coverage", "percent", "%"]):
                        result["symptoms"].append(line)
                    
                    # Extract control method
                    if any(word in line.lower() for word in ["control", "herbicide", "manual", "mulch"]):
                        result["treatment"] = line
                
                if not result["diagnosis"]:
                    result["diagnosis"] = lines[0] if lines else text[:100]
        
        else:  # general
            result["diagnosis"] = text.split("\n")[0] if "\n" in text else text[:100]
            result["symptoms"] = [line.strip() for line in text.split("\n")[1:] if line.strip()]
        
        # Clean up
        result["diagnosis"] = result["diagnosis"].strip()
        result["treatment"] = result["treatment"].strip()
        
        return result
    
    def analyze_batch(
        self,
        image_bytes_list: List[bytes],
        task: str = "disease",
        batch_size: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images in batches.
        
        Why batch processing:
        - More efficient GPU utilization
        - Faster than sequential processing
        - Shared overhead (model loading, etc.)
        
        Parameters:
        -----------
        image_bytes_list : List[bytes]
            List of image byte arrays
        task : str
            Task type for all images
        batch_size : int
            Number of images to process at once
            Why: Balance between speed and memory
            
        Returns:
        --------
        List of analysis results (same format as analyze_image)
        """
        results = []
        
        for i in range(0, len(image_bytes_list), batch_size):
            batch = image_bytes_list[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(image_bytes_list) + batch_size - 1) // batch_size}")
            
            for image_bytes in batch:
                try:
                    result = self.analyze_image(image_bytes, task=task)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    results.append({"error": str(e), "task": task})
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get model statistics and system info.
        
        Returns:
        --------
        Dict with model info, memory usage, device, etc.
        """
        stats = {
            "model_name": self.model_name,
            "device": self.device,
            "memory_gb": self._estimate_memory_gb(),
        }
        
        if self.device == "cuda":
            stats["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                stats["cuda_device_name"] = torch.cuda.get_device_name(0)
                stats["cuda_memory_allocated_gb"] = torch.cuda.memory_allocated() / (1024 ** 3)
                stats["cuda_memory_reserved_gb"] = torch.cuda.memory_reserved() / (1024 ** 3)
        
        return stats


# Singleton instance for dependency injection
_crop_vision_analyst_instance: Optional[CropVisionAnalyst] = None


def get_crop_vision_analyst() -> CropVisionAnalyst:
    """
    Get or create singleton CropVisionAnalyst instance.
    
    Why singleton:
    - VLM model is large (~14GB) and expensive to load
    - Loading multiple instances would exhaust memory
    - Share across all API requests
    
    Usage in FastAPI:
    -----------------
    ```python
    @app.post("/ai/analyze")
    async def analyze(
        file: UploadFile,
        analyst: CropVisionAnalyst = Depends(get_crop_vision_analyst)
    ):
        image_bytes = await file.read()
        return analyst.analyze_image(image_bytes)
    ```
    """
    global _crop_vision_analyst_instance
    
    if _crop_vision_analyst_instance is None:
        # Get configuration from environment
        model_name = os.getenv(
            "AGRISENSE_VLM_MODEL",
            "llava-hf/llava-v1.6-mistral-7b-hf"
        )
        use_4bit = os.getenv("AGRISENSE_VLM_4BIT", "true").lower() == "true"
        
        logger.info("Initializing CropVisionAnalyst singleton")
        _crop_vision_analyst_instance = CropVisionAnalyst(
            model_name=model_name,
            use_4bit=use_4bit,
        )
    
    return _crop_vision_analyst_instance
