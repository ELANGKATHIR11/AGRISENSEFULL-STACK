"""
ML Model Inference Optimization
Optimized for Intel Core Ultra 9 275HX + RTX 5060

Features:
1. ONNX Runtime with GPU acceleration
2. Batch inference for multiple predictions
3. Model caching and lazy loading
4. Thread pool for CPU-bound inference
5. TensorFlow/PyTorch optimization
"""

import os
import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

# Thread pool for CPU inference (use E-cores)
_inference_thread_pool = None
_inference_thread_pool_lock = threading.Lock()


def get_inference_thread_pool() -> ThreadPoolExecutor:
    """Get or create inference thread pool"""
    global _inference_thread_pool
    
    if _inference_thread_pool is None:
        with _inference_thread_pool_lock:
            if _inference_thread_pool is None:
                # Use 16 threads (E-cores for inference)
                num_workers = int(os.getenv("ML_NUM_WORKERS", "16"))
                _inference_thread_pool = ThreadPoolExecutor(
                    max_workers=num_workers,
                    thread_name_prefix="ml_inference"
                )
                logger.info(f"✅ Created inference thread pool with {num_workers} workers")
    
    return _inference_thread_pool


# ============================================================================
# ONNX Runtime Optimization (Recommended for production)
# ============================================================================

class ONNXModelOptimized:
    """
    Optimized ONNX model wrapper with GPU acceleration.
    Supports DirectML (Windows) and CUDA.
    """
    
    def __init__(
        self,
        model_path: Union[str, Path],
        use_gpu: bool = True,
        intra_op_threads: int = 8,  # P-cores
        inter_op_threads: int = 16,  # E-cores
    ):
        try:
            import onnxruntime as ort
        except ImportError:
            raise ImportError(
                "onnxruntime not installed. Install with: "
                "pip install onnxruntime-gpu  # or onnxruntime for CPU-only"
            )
        
        self.model_path = Path(model_path)
        
        # Session options
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session_options.intra_op_num_threads = intra_op_threads
        session_options.inter_op_num_threads = inter_op_threads
        session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        
        # Enable optimizations
        session_options.enable_cpu_mem_arena = True
        session_options.enable_mem_pattern = True
        session_options.enable_mem_reuse = True
        
        # Provider configuration
        providers = []
        
        if use_gpu:
            # DirectML (Windows GPU acceleration - works with RTX 5060!)
            if 'DmlExecutionProvider' in ort.get_available_providers():
                providers.append(('DmlExecutionProvider', {
                    'device_id': 0,
                    'enable_dynamic_graph_fusion': True,
                }))
                logger.info("✅ Using DirectML GPU acceleration")
            
            # CUDA (if available)
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.append(('CUDAExecutionProvider', {
                    'device_id': 0,
                    'gpu_mem_limit': 7 * 1024 * 1024 * 1024,  # 7GB
                    'arena_extend_strategy': 'kSameAsRequested',
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }))
                logger.info("✅ Using CUDA GPU acceleration")
        
        # Always add CPU as fallback
        providers.append('CPUExecutionProvider')
        
        # Create session
        self.session = ort.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=providers
        )
        
        # Get input/output info
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        logger.info(f"✅ Loaded ONNX model: {self.model_path.name}")
        logger.info(f"   Input: {self.input_name}")
        logger.info(f"   Output: {self.output_name}")
        logger.info(f"   Providers: {self.session.get_providers()}")
    
    def predict(self, input_data: np.ndarray) -> np.ndarray:
        """Single prediction"""
        return self.session.run([self.output_name], {self.input_name: input_data})[0]
    
    def predict_batch(
        self,
        inputs: List[np.ndarray],
        batch_size: int = 128
    ) -> np.ndarray:
        """
        Batch prediction with optimal batch size for RTX 5060.
        Automatically batches inputs for better GPU utilization.
        """
        if not inputs:
            return np.array([])
        
        # Convert to numpy array
        input_array = np.array(inputs)
        
        # If small batch, predict directly
        if len(inputs) <= batch_size:
            return self.predict(input_array)
        
        # Split into batches
        results = []
        for i in range(0, len(inputs), batch_size):
            batch = input_array[i:i + batch_size]
            batch_result = self.predict(batch)
            results.append(batch_result)
        
        return np.concatenate(results)


# ============================================================================
# TensorFlow Optimization
# ============================================================================

def configure_tensorflow_performance():
    """
    Configure TensorFlow for optimal CPU/GPU performance.
    Call this at application startup.
    """
    try:
        import tensorflow as tf
    except ImportError:
        logger.warning("TensorFlow not installed")
        return
    
    logger.info("⚙️ Configuring TensorFlow for hardware optimization...")
    
    # CPU Threading (24 threads for Core Ultra 9)
    intra_op = int(os.getenv("TF_INTRA_OP_PARALLELISM_THREADS", "8"))  # P-cores
    inter_op = int(os.getenv("TF_INTER_OP_PARALLELISM_THREADS", "16"))  # E-cores
    
    tf.config.threading.set_intra_op_parallelism_threads(intra_op)
    tf.config.threading.set_inter_op_parallelism_threads(inter_op)
    
    logger.info(f"   ✓ CPU threads: intra={intra_op}, inter={inter_op}")
    
    # GPU Configuration
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            # Enable memory growth (don't allocate all 8GB at once)
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            
            # Set visible devices
            tf.config.set_visible_devices(gpus[0], 'GPU')
            
            logger.info(f"   ✓ GPU configured: {gpus[0].name}")
            logger.info("   ✓ Memory growth enabled")
        except RuntimeError as e:
            logger.warning(f"GPU configuration failed: {e}")
    else:
        logger.info("   ℹ No GPU detected, using CPU")
    
    # Mixed precision (faster on modern GPUs)
    try:
        from tensorflow.keras import mixed_precision
        policy = mixed_precision.Policy('mixed_float16')
        mixed_precision.set_global_policy(policy)
        logger.info("   ✓ Mixed precision (FP16) enabled")
    except Exception as e:
        logger.debug(f"Mixed precision not enabled: {e}")
    
    # XLA compilation (experimental, may improve performance)
    if os.getenv("TF_ENABLE_XLA", "0") == "1":
        tf.config.optimizer.set_jit(True)
        logger.info("   ✓ XLA JIT compilation enabled")


# ============================================================================
# PyTorch Optimization
# ============================================================================

def configure_pytorch_performance():
    """
    Configure PyTorch for optimal CPU/GPU performance.
    Call this at application startup.
    """
    try:
        import torch
    except ImportError:
        logger.warning("PyTorch not installed")
        return
    
    logger.info("⚙️ Configuring PyTorch for hardware optimization...")
    
    # CPU Threading
    num_threads = int(os.getenv("OMP_NUM_THREADS", "24"))
    torch.set_num_threads(num_threads)
    logger.info(f"   ✓ CPU threads: {num_threads}")
    
    # GPU Configuration
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        
        # Get GPU properties
        props = torch.cuda.get_device_properties(0)
        logger.info(f"   ✓ GPU detected: {props.name}")
        logger.info(f"   ✓ CUDA version: {torch.version.cuda}")
        logger.info(f"   ✓ Compute capability: {props.major}.{props.minor}")
        
        # Memory management
        torch.cuda.empty_cache()
        
        # Enable cuDNN autotuner (finds fastest algorithms)
        torch.backends.cudnn.benchmark = True
        logger.info("   ✓ cuDNN autotuner enabled")
        
        # Note: RTX 5060 has sm_120, PyTorch max is sm_90
        # Models will run but some optimizations may not work
        if props.major > 9:
            logger.warning(
                f"   ⚠ GPU compute capability {props.major}.{props.minor} "
                "exceeds PyTorch support (max 9.0). Some features may not work."
            )
    else:
        logger.info("   ℹ No GPU detected, using CPU")
    
    # Enable automatic mixed precision (AMP)
    logger.info("   ✓ Automatic Mixed Precision (AMP) available")


# ============================================================================
# Model Caching
# ============================================================================

class ModelCache:
    """
    Lazy-loading model cache with thread-safe access.
    Models are loaded once and reused across requests.
    """
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def get_or_load(
        self,
        model_id: str,
        loader_func: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Get model from cache or load it.
        
        Args:
            model_id: Unique identifier for the model
            loader_func: Function to load the model if not in cache
            *args, **kwargs: Arguments for loader_func
        
        Returns:
            Loaded model
        """
        if model_id not in self._models:
            with self._lock:
                # Double-check after acquiring lock
                if model_id not in self._models:
                    logger.info(f"🔄 Loading model: {model_id}")
                    self._models[model_id] = loader_func(*args, **kwargs)
                    logger.info(f"✅ Model loaded: {model_id}")
        
        return self._models[model_id]
    
    def clear(self, model_id: Optional[str] = None):
        """Clear cache (specific model or all)"""
        with self._lock:
            if model_id:
                self._models.pop(model_id, None)
                logger.info(f"🗑 Cleared model: {model_id}")
            else:
                self._models.clear()
                logger.info("🗑 Cleared all models from cache")


# Global model cache
_model_cache = ModelCache()


def get_model_cache() -> ModelCache:
    """Get global model cache"""
    return _model_cache


# ============================================================================
# Batch Inference Helper
# ============================================================================

class BatchInferenceQueue:
    """
    Queues multiple inference requests and processes them in batches.
    Improves GPU utilization by batching small requests.
    """
    
    def __init__(
        self,
        model,
        batch_size: int = 128,
        max_wait_time: float = 0.1  # 100ms max wait
    ):
        self.model = model
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        
        self.queue = []
        self.queue_lock = threading.Lock()
        self.processing = False
    
    async def predict(self, input_data: np.ndarray) -> np.ndarray:
        """
        Add prediction to queue and wait for batch processing.
        
        Note: This is a simplified implementation. For production,
        use a proper async queue like asyncio.Queue.
        """
        # For now, just call model directly
        # TODO: Implement proper batch queuing
        return self.model.predict(input_data)


# ============================================================================
# Initialization
# ============================================================================

def initialize_ml_optimizations():
    """
    Initialize all ML optimizations at application startup.
    Call this in FastAPI's startup event.
    """
    logger.info("🚀 Initializing ML optimizations...")
    
    # Configure frameworks
    configure_tensorflow_performance()
    configure_pytorch_performance()
    
    # Create thread pool
    get_inference_thread_pool()
    
    logger.info("✅ ML optimizations complete!")


# ============================================================================
# Example Usage
# ============================================================================

"""
# In your FastAPI app:

from agrisense_app.backend.ml.inference_optimized import (
    initialize_ml_optimizations,
    get_model_cache,
    ONNXModelOptimized
)

@app.on_event("startup")
async def startup():
    initialize_ml_optimizations()

# Load model with caching
def load_disease_model():
    return ONNXModelOptimized(
        "models/disease_detection.onnx",
        use_gpu=True
    )

@app.post("/api/predict/disease")
async def predict_disease(data: SensorData):
    # Get cached model
    model = get_model_cache().get_or_load(
        "disease_detection",
        load_disease_model
    )
    
    # Prepare input
    input_array = np.array([[
        data.temperature,
        data.humidity,
        data.soil_moisture,
        # ... more features
    ]], dtype=np.float32)
    
    # Predict
    prediction = model.predict(input_array)
    
    return {"prediction": prediction.tolist()}
"""
