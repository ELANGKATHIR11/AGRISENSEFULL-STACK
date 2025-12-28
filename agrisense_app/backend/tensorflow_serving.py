"""
TensorFlow Serving integration for AgriSense ML models
Provides model serving, batch inference, and version management
"""

import os
import json
import aiohttp
import numpy as np
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Configuration
TF_SERVING_URL = os.getenv("TENSORFLOW_SERVING_URL", "http://localhost:8501")
TF_SERVING_ENABLED = os.getenv("AGRISENSE_USE_TENSORFLOW_SERVING", "0").lower() in ("1", "true", "yes")
MODEL_BASE_PATH = Path(os.getenv("AGRISENSE_MODEL_PATH", "./models"))


@dataclass
class ModelConfig:
    name: str
    version: Optional[int] = None
    input_signature: Optional[Dict[str, Any]] = None
    output_signature: Optional[Dict[str, Any]] = None
    preprocessing: Optional[str] = None
    postprocessing: Optional[str] = None


# Model configurations
MODEL_CONFIGS = {
    "water_model": ModelConfig(
        name="water_recommendation",
        input_signature={
            "inputs": {
                "dtype": "float32",
                "shape": [-1, 8],  # [soil_moisture, temperature, humidity, ph, npk, light, plant_age]
            }
        },
        output_signature={"outputs": {"dtype": "float32", "shape": [-1, 1]}},  # water amount in liters
    ),
    "fertilizer_model": ModelConfig(
        name="fertilizer_recommendation",
        input_signature={"inputs": {"dtype": "float32", "shape": [-1, 8]}},
        output_signature={"outputs": {"dtype": "float32", "shape": [-1, 3]}},  # [nitrogen, phosphorus, potassium] grams
    ),
    "crop_model": ModelConfig(
        name="crop_recommendation",
        input_signature={
            "inputs": {
                "dtype": "float32",
                "shape": [-1, 7],  # [nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]
            }
        },
        output_signature={"outputs": {"dtype": "float32", "shape": [-1, 22]}},  # crop probabilities
    ),
    "yield_model": ModelConfig(
        name="yield_prediction",
        input_signature={"inputs": {"dtype": "float32", "shape": [-1, 12]}},  # comprehensive yield features
        output_signature={"outputs": {"dtype": "float32", "shape": [-1, 1]}},  # yield in kg/hectare
    ),
}


class TensorFlowServingClient:
    """Client for TensorFlow Serving integration"""

    def __init__(self, base_url: str = TF_SERVING_URL):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        self.model_status: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if TensorFlow Serving is healthy"""
        try:
            if not self.session:
                return False

            async with self.session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    models = await response.json()
                    logger.info(f"TF Serving health check passed. Available models: {len(models.get('models', []))}")
                    return True
                else:
                    logger.warning(f"TF Serving health check failed with status: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"TF Serving health check failed: {e}")
            return False

    async def get_model_status(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model status and metadata"""
        try:
            if not self.session:
                return None

            async with self.session.get(f"{self.base_url}/v1/models/{model_name}") as response:
                if response.status == 200:
                    status = await response.json()
                    self.model_status[model_name] = status
                    return status
                else:
                    logger.warning(f"Failed to get model status for {model_name}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting model status for {model_name}: {e}")
            return None

    async def get_model_metadata(self, model_name: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get model metadata including input/output signatures"""
        try:
            if not self.session:
                return None

            url = f"{self.base_url}/v1/models/{model_name}/metadata"
            if version:
                url += f"?version={version}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    metadata = await response.json()
                    return metadata
                else:
                    logger.warning(f"Failed to get model metadata for {model_name}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting model metadata for {model_name}: {e}")
            return None

    async def predict(
        self,
        model_name: str,
        inputs: Union[np.ndarray, List[List[float]], Dict[str, Any]],
        version: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make prediction using TensorFlow Serving"""
        try:
            if not self.session:
                return None

            # Prepare request payload
            if isinstance(inputs, np.ndarray):
                inputs_data = inputs.tolist()
            elif isinstance(inputs, dict):
                inputs_data = inputs
            else:
                inputs_data = inputs

            # Build prediction URL
            url = f"{self.base_url}/v1/models/{model_name}:predict"
            if version:
                url = f"{self.base_url}/v1/models/{model_name}/versions/{version}:predict"

            # Prepare payload based on model config
            config = MODEL_CONFIGS.get(model_name)
            if config and config.input_signature:
                payload = {"signature_name": "serving_default", "inputs": inputs_data}
            else:
                payload = {"instances": inputs_data}

            # Make prediction request
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Prediction failed for {model_name}: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error making prediction for {model_name}: {e}")
            return None

    async def batch_predict(
        self,
        model_name: str,
        batch_inputs: List[Union[np.ndarray, List[float]]],
        batch_size: int = 32,
        version: Optional[int] = None,
    ) -> List[Optional[Dict[str, Any]]]:
        """Make batch predictions with chunking"""
        results = []

        # Process in batches
        for i in range(0, len(batch_inputs), batch_size):
            batch = batch_inputs[i:i + batch_size]

            try:
                # Convert batch to appropriate format
                if isinstance(batch[0], np.ndarray):
                    batch_array = np.stack(batch)
                else:
                    batch_array = np.array(batch)

                # Make prediction
                result = await self.predict(model_name, batch_array, version)
                results.append(result)

            except Exception as e:
                logger.error(f"Error in batch prediction chunk {i//batch_size}: {e}")
                results.append(None)

        return results


# Global client instance
tf_serving_client: Optional[TensorFlowServingClient] = None


async def initialize_tf_serving():
    """Initialize TensorFlow Serving client"""
    global tf_serving_client

    if not TF_SERVING_ENABLED:
        logger.info("TensorFlow Serving disabled")
        return

    try:
        tf_serving_client = TensorFlowServingClient()
        await tf_serving_client.__aenter__()

        # Health check
        healthy = await tf_serving_client.health_check()
        if healthy:
            logger.info("TensorFlow Serving initialized successfully")

            # Check available models
            for model_name in MODEL_CONFIGS.keys():
                status = await tf_serving_client.get_model_status(model_name)
                if status:
                    logger.info(f"Model {model_name} is available")
                else:
                    logger.warning(f"Model {model_name} is not available")
        else:
            logger.warning("TensorFlow Serving health check failed")

    except Exception as e:
        logger.error(f"Failed to initialize TensorFlow Serving: {e}")
        tf_serving_client = None


async def cleanup_tf_serving():
    """Cleanup TensorFlow Serving client"""
    global tf_serving_client

    if tf_serving_client:
        try:
            await tf_serving_client.__aexit__(None, None, None)
            logger.info("TensorFlow Serving client closed")
        except Exception as e:
            logger.error(f"Error closing TensorFlow Serving client: {e}")
        finally:
            tf_serving_client = None


# High-level prediction functions


async def predict_water_need(sensor_data: Dict[str, float]) -> Optional[float]:
    """Predict water need using TensorFlow Serving"""
    if not tf_serving_client:
        return None

    try:
        # Prepare input features
        features = [
            sensor_data.get("soil_moisture", 50.0),
            sensor_data.get("temperature", 25.0),
            sensor_data.get("humidity", 60.0),
            sensor_data.get("ph", 7.0),
            sensor_data.get("nitrogen", 20.0),
            sensor_data.get("phosphorus", 20.0),
            sensor_data.get("potassium", 20.0),
            sensor_data.get("plant_age_days", 30.0),
        ]

        # Make prediction
        result = await tf_serving_client.predict("water_model", [features])

        if result and "predictions" in result:
            water_amount = float(result["predictions"][0][0])
            return max(0.0, water_amount)  # Ensure non-negative

        return None

    except Exception as e:
        logger.error(f"Error predicting water need: {e}")
        return None


async def predict_fertilizer_need(sensor_data: Dict[str, float]) -> Optional[Dict[str, float]]:
    """Predict fertilizer need using TensorFlow Serving"""
    if not tf_serving_client:
        return None

    try:
        # Prepare input features
        features = [
            sensor_data.get("soil_moisture", 50.0),
            sensor_data.get("temperature", 25.0),
            sensor_data.get("humidity", 60.0),
            sensor_data.get("ph", 7.0),
            sensor_data.get("nitrogen", 20.0),
            sensor_data.get("phosphorus", 20.0),
            sensor_data.get("potassium", 20.0),
            sensor_data.get("plant_age_days", 30.0),
        ]

        # Make prediction
        result = await tf_serving_client.predict("fertilizer_model", [features])

        if result and "predictions" in result:
            fert_amounts = result["predictions"][0]
            return {
                "nitrogen": max(0.0, float(fert_amounts[0])),
                "phosphorus": max(0.0, float(fert_amounts[1])),
                "potassium": max(0.0, float(fert_amounts[2])),
            }

        return None

    except Exception as e:
        logger.error(f"Error predicting fertilizer need: {e}")
        return None


async def predict_crop_recommendation(environmental_data: Dict[str, float]) -> Optional[List[Dict[str, Any]]]:
    """Predict crop recommendations using TensorFlow Serving"""
    if not tf_serving_client:
        return None

    try:
        # Prepare input features
        features = [
            environmental_data.get("nitrogen", 20.0),
            environmental_data.get("phosphorus", 20.0),
            environmental_data.get("potassium", 20.0),
            environmental_data.get("temperature", 25.0),
            environmental_data.get("humidity", 60.0),
            environmental_data.get("ph", 7.0),
            environmental_data.get("rainfall", 100.0),
        ]

        # Make prediction
        result = await tf_serving_client.predict("crop_model", [features])

        if result and "predictions" in result:
            probabilities = result["predictions"][0]

            # Map to crop names (this should match your training data)
            crop_names = [
                "rice",
                "maize",
                "chickpea",
                "kidney_beans",
                "pigeon_peas",
                "moth_beans",
                "mung_bean",
                "black_gram",
                "lentil",
                "pomegranate",
                "banana",
                "mango",
                "grapes",
                "watermelon",
                "muskmelon",
                "apple",
                "orange",
                "papaya",
                "coconut",
                "cotton",
                "jute",
                "coffee",
            ]

            # Create recommendations with probabilities
            recommendations = []
            for i, prob in enumerate(probabilities):
                if i < len(crop_names):
                    recommendations.append(
                        {"crop": crop_names[i], "suitability_score": float(prob), "confidence": float(prob)}
                    )

            # Sort by suitability score
            recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
            return recommendations[:10]  # Top 10 recommendations

        return None

    except Exception as e:
        logger.error(f"Error predicting crop recommendations: {e}")
        return None


async def predict_yield(crop_data: Dict[str, float]) -> Optional[float]:
    """Predict crop yield using TensorFlow Serving"""
    if not tf_serving_client:
        return None

    try:
        # Prepare input features (adjust based on your model)
        features = [
            crop_data.get("area_hectares", 1.0),
            crop_data.get("nitrogen", 20.0),
            crop_data.get("phosphorus", 20.0),
            crop_data.get("potassium", 20.0),
            crop_data.get("temperature", 25.0),
            crop_data.get("humidity", 60.0),
            crop_data.get("ph", 7.0),
            crop_data.get("rainfall", 100.0),
            crop_data.get("irrigation_frequency", 3.0),
            crop_data.get("fertilizer_amount", 50.0),
            crop_data.get("plant_density", 10000.0),
            crop_data.get("growth_stage", 0.5),
        ]

        # Make prediction
        result = await tf_serving_client.predict("yield_model", [features])

        if result and "predictions" in result:
            yield_value = float(result["predictions"][0][0])
            return max(0.0, yield_value)  # Ensure non-negative

        return None

    except Exception as e:
        logger.error(f"Error predicting yield: {e}")
        return None


# Utility functions


async def get_tf_serving_status() -> Dict[str, Any]:
    """Get comprehensive TensorFlow Serving status"""
    if not tf_serving_client:
        return {"enabled": TF_SERVING_ENABLED, "available": False, "models": {}}

    try:
        healthy = await tf_serving_client.health_check()
        models = {}

        for model_name in MODEL_CONFIGS.keys():
            status = await tf_serving_client.get_model_status(model_name)
            metadata = await tf_serving_client.get_model_metadata(model_name)

            models[model_name] = {"available": status is not None, "status": status, "metadata": metadata}

        return {"enabled": TF_SERVING_ENABLED, "available": healthy, "url": TF_SERVING_URL, "models": models}

    except Exception as e:
        logger.error(f"Error getting TF Serving status: {e}")
        return {"enabled": TF_SERVING_ENABLED, "available": False, "error": str(e), "models": {}}


# Model serving utilities


def create_model_config_file(model_name: str, model_path: Path) -> Path:
    """Create TensorFlow Serving model config file"""
    config = {
        "model_config_list": [
            {
                "name": model_name,
                "base_path": str(model_path),
                "model_platform": "tensorflow",
                "model_version_policy": {"latest": {"num_versions": 2}},
            }
        ]
    }

    config_path = model_path.parent / f"{model_name}_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


def generate_docker_compose() -> str:
    """Generate Docker Compose configuration for TensorFlow Serving"""
    return f"""version: '3.8'
services:
  tensorflow-serving:
    image: tensorflow/serving:latest
    ports:
      - "8501:8501"
      - "8500:8500"
    volumes:
      - {MODEL_BASE_PATH.absolute()}:/models
    environment:
      - MODEL_CONFIG_FILE=/models/model_config.json
      - MODEL_CONFIG_FILE_POLL_WAIT_SECONDS=60
    command:
      - --model_config_file=/models/model_config.json
      - --model_config_file_poll_wait_seconds=60
      - --allow_version_labels_for_unavailable_models=true
      - --enable_batching=true
      - --batching_parameters_file=/models/batching_config.txt
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/v1/models"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
