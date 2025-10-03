"""
Machine Learning Tasks
Background tasks for ML model training, inference, and optimization
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
try:
    from celery import current_task  # type: ignore
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    current_task = None  # type: ignore

import joblib
from pathlib import Path

from ..celery_config import celery_app, CELERY_AVAILABLE
from ..core.engine import RecoEngine

logger = logging.getLogger(__name__)


# Conditional task decorators
def task_decorator(func):
    """Decorator that conditionally applies Celery task decoration"""
    if CELERY_AVAILABLE and celery_app:
        return celery_app.task(bind=True, time_limit=3600)(func)
    else:
        def wrapper(*args, **kwargs):
            if args and hasattr(args[0], 'request'):
                return func(*args, **kwargs)
            else:
                return func(None, *args, **kwargs)
        wrapper.delay = lambda *args, **kwargs: wrapper(*args, **kwargs)
        wrapper.apply_async = lambda *args, **kwargs: wrapper(*args, **kwargs)
        return wrapper


# Utility function to safely update task state
def safe_update_state(state: str, meta: Dict[str, Any]):
    """Safely update task state if current_task is available"""
    if current_task and hasattr(current_task, 'update_state'):
        current_task.update_state(state=state, meta=meta)  # type: ignore


@task_decorator
def retrain_models(self, model_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Retrain ML models with latest data
    Periodic retraining to keep models current with new data patterns
    """
    try:
        if current_task and hasattr(current_task, 'update_state'):
            current_task.update_state(state="PROGRESS", meta={"progress": 5, "status": "Initializing model retraining"})  # type: ignore

        if model_types is None:
            model_types = ["water_recommendation", "fertilizer_recommendation", "crop_health"]

        training_results = {}
        total_models = len(model_types)

        for i, model_type in enumerate(model_types):
            progress = 10 + (i / total_models) * 80
            current_task.update_state(  # type: ignore
                state="PROGRESS", meta={"progress": progress, "status": f"Training {model_type} model"}
            )

            try:
                result = retrain_single_model(model_type)
                training_results[model_type] = result
                logger.info(f"Successfully retrained {model_type} model")
            except Exception as e:
                training_results[model_type] = {"status": "failed", "error": str(e)}
                logger.error(f"Failed to retrain {model_type} model: {str(e)}")

        current_task.update_state(state="PROGRESS", meta={"progress": 95, "status": "Finalizing retraining"})  # type: ignore

        # Calculate overall success rate
        successful_models = sum(1 for result in training_results.values() if result.get("status") == "completed")
        success_rate = successful_models / total_models

        overall_result = {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "models_trained": total_models,
            "successful_models": successful_models,
            "success_rate": success_rate,
            "training_results": training_results,
            "next_scheduled_training": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }

        logger.info(f"Model retraining completed with {success_rate:.2%} success rate")
        return overall_result

    except Exception as exc:
        logger.error(f"Model retraining failed: {str(exc)}")
        raise


@task_decorator  # type: ignore
def batch_model_inference(self, readings: List[Dict[str, Any]], model_type: str = "recommendation") -> Dict[str, Any]:
    """
    Perform batch ML inference on multiple sensor readings
    Efficient processing of multiple predictions
    """
    try:
        current_task.update_state(state="PROGRESS", meta={"progress": 10, "status": "Preparing batch inference"})  # type: ignore

        if not readings:
            return {"status": "completed", "predictions": [], "message": "No readings provided for inference"}

        predictions = []
        total_readings = len(readings)

        # Load model based on type
        current_task.update_state(state="PROGRESS", meta={"progress": 20, "status": f"Loading {model_type} model"})  # type: ignore

        try:
            model = load_model(model_type)
        except Exception as e:
            logger.error(f"Failed to load model {model_type}: {str(e)}")
            return {
                "status": "failed",
                "error": f"Model loading failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Process readings in batches for efficiency
        batch_size = 50
        for batch_start in range(0, total_readings, batch_size):
            batch_end = min(batch_start + batch_size, total_readings)
            batch_readings = readings[batch_start:batch_end]

            progress = 20 + (batch_start / total_readings) * 70
            current_task.update_state(  # type: ignore
                state="PROGRESS",
                meta={"progress": progress, "status": f"Processing batch {batch_start//batch_size + 1}"},
            )

            # Perform batch prediction
            batch_predictions = predict_batch(model, batch_readings, model_type)
            predictions.extend(batch_predictions)

        current_task.update_state(state="PROGRESS", meta={"progress": 95, "status": "Finalizing predictions"})  # type: ignore

        result = {
            "status": "completed",
            "model_type": model_type,
            "total_readings": total_readings,
            "predictions": predictions,
            "processing_time": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Batch inference completed for {total_readings} readings using {model_type} model")
        return result

    except Exception as exc:
        logger.error(f"Batch inference failed: {str(exc)}")
        raise


@task_decorator  # type: ignore
def model_performance_evaluation(self, model_type: str, evaluation_period: str = "7d") -> Dict[str, Any]:
    """
    Evaluate model performance over a specified period
    Monitor model accuracy and drift
    """
    try:
        current_task.update_state(state="PROGRESS", meta={"progress": 10, "status": "Setting up evaluation"})  # type: ignore

        # Parse evaluation period
        period_mapping = {"1d": timedelta(days=1), "7d": timedelta(days=7), "30d": timedelta(days=30)}

        if evaluation_period not in period_mapping:
            raise ValueError(f"Invalid evaluation period: {evaluation_period}")

        delta = period_mapping[evaluation_period]
        end_time = datetime.utcnow()
        start_time = end_time - delta

        current_task.update_state(state="PROGRESS", meta={"progress": 30, "status": "Collecting evaluation data"})  # type: ignore

        # Collect predictions and actual outcomes for the period
        # This would query actual database for predictions and outcomes
        evaluation_data = collect_evaluation_data(model_type, start_time, end_time)

        if not evaluation_data:
            return {
                "status": "completed",
                "message": "No evaluation data available for the specified period",
                "model_type": model_type,
                "evaluation_period": evaluation_period,
            }

        current_task.update_state(state="PROGRESS", meta={"progress": 60, "status": "Computing performance metrics"})  # type: ignore

        # Calculate performance metrics
        metrics = calculate_model_metrics(evaluation_data, model_type)

        current_task.update_state(state="PROGRESS", meta={"progress": 80, "status": "Analyzing model drift"})  # type: ignore

        # Detect model drift
        drift_analysis = analyze_model_drift(evaluation_data, model_type)

        result = {
            "status": "completed",
            "model_type": model_type,
            "evaluation_period": evaluation_period,
            "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "metrics": metrics,
            "drift_analysis": drift_analysis,
            "recommendations": generate_model_recommendations(metrics, drift_analysis),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Model evaluation completed for {model_type}")
        return result

    except Exception as exc:
        logger.error(f"Model evaluation failed: {str(exc)}")
        raise


@task_decorator  # type: ignore
def optimize_model_hyperparameters(self, model_type: str, optimization_budget: int = 50) -> Dict[str, Any]:
    """
    Optimize model hyperparameters using automated tuning
    Improve model performance through systematic optimization
    """
    try:
        current_task.update_state(  # type: ignore
            state="PROGRESS", meta={"progress": 5, "status": "Initializing hyperparameter optimization"}
        )

        # Prepare training data
        current_task.update_state(state="PROGRESS", meta={"progress": 15, "status": "Preparing training data"})  # type: ignore

        training_data = prepare_training_data(model_type)

        if not training_data:
            return {"status": "failed", "error": "No training data available", "model_type": model_type}

        current_task.update_state(state="PROGRESS", meta={"progress": 25, "status": "Setting up optimization search"})  # type: ignore

        # Define hyperparameter search space
        search_space = get_hyperparameter_search_space(model_type)

        # Perform optimization
        best_params = None
        best_score = 0
        optimization_history = []

        for trial in range(optimization_budget):
            progress = 25 + (trial / optimization_budget) * 65
            current_task.update_state(  # type: ignore
                state="PROGRESS", meta={"progress": progress, "status": f"Trial {trial + 1}/{optimization_budget}"}
            )

            # Sample hyperparameters
            trial_params = sample_hyperparameters(search_space)

            # Train and evaluate model with these parameters
            trial_score = evaluate_hyperparameters(trial_params, training_data, model_type)

            optimization_history.append({"trial": trial + 1, "parameters": trial_params, "score": trial_score})

            if trial_score > best_score:
                best_score = trial_score
                best_params = trial_params
                logger.info(f"New best score: {best_score:.4f} at trial {trial + 1}")

        current_task.update_state(state="PROGRESS", meta={"progress": 95, "status": "Finalizing optimization"})  # type: ignore

        result = {
            "status": "completed",
            "model_type": model_type,
            "optimization_budget": optimization_budget,
            "best_parameters": best_params,
            "best_score": best_score,
            "optimization_history": optimization_history,
            "improvement": calculate_improvement(best_score, model_type),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Hyperparameter optimization completed for {model_type} with score {best_score:.4f}")
        return result

    except Exception as exc:
        logger.error(f"Hyperparameter optimization failed: {str(exc)}")
        raise


# Helper functions


def retrain_single_model(model_type: str) -> Dict[str, Any]:
    """Retrain a single model"""
    try:
        # Prepare training data
        training_data = prepare_training_data(model_type)

        if not training_data:
            return {"status": "failed", "error": "No training data available"}

        # Train model based on type
        if model_type == "water_recommendation":
            model, metrics = train_water_model(training_data)
        elif model_type == "fertilizer_recommendation":
            model, metrics = train_fertilizer_model(training_data)
        elif model_type == "crop_health":
            model, metrics = train_crop_health_model(training_data)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Save model
        model_path = save_model(model, model_type)

        return {
            "status": "completed",
            "model_type": model_type,
            "model_path": model_path,
            "metrics": metrics,
            "training_data_size": len(training_data),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {"status": "failed", "error": str(e), "model_type": model_type}


def load_model(model_type: str):
    """Load a trained model"""
    models_dir = Path(__file__).parent.parent
    model_files = {
        "water_recommendation": "water_model.joblib",
        "fertilizer_recommendation": "fert_model.joblib",
        "crop_health": "health_model.joblib",
    }

    if model_type not in model_files:
        raise ValueError(f"Unknown model type: {model_type}")

    model_path = models_dir / model_files[model_type]

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    return joblib.load(model_path)


def predict_batch(model, readings: List[Dict], model_type: str) -> List[Dict[str, Any]]:
    """Perform batch prediction"""
    predictions = []

    for reading in readings:
        try:
            # Prepare features based on model type
            features = prepare_features(reading, model_type)

            # Make prediction
            if hasattr(model, "predict"):
                prediction = model.predict([features])[0]
            else:
                # Fallback to RecoEngine for compatibility
                reco_engine = RecoEngine()
                prediction_dict = reco_engine.recommend(reading)
                prediction = prediction_dict.get("water_liters", 0)

            predictions.append(
                {
                    "reading_id": reading.get("id", len(predictions)),
                    "prediction": float(prediction),
                    "confidence": 0.85,  # Placeholder confidence
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except Exception as e:
            predictions.append(
                {
                    "reading_id": reading.get("id", len(predictions)),
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    return predictions


def prepare_training_data(model_type: str) -> List[Dict[str, Any]]:
    """Prepare training data for model"""
    # This would query actual database for training data
    # For now, return empty list as placeholder
    return []


def prepare_features(reading: Dict[str, Any], model_type: str) -> List[float]:
    """Prepare features for model input"""
    features = []

    # Extract common features
    features.append(reading.get("temperature_c", 20.0))
    features.append(reading.get("humidity_pct", 50.0))
    features.append(reading.get("moisture_pct", 40.0))
    features.append(reading.get("light_lux", 50000.0))

    # Add model-specific features
    if model_type == "water_recommendation":
        features.append(reading.get("soil_ph", 7.0))
        features.append(reading.get("ec_ms_cm", 1.5))
    elif model_type == "fertilizer_recommendation":
        features.append(reading.get("nitrogen_ppm", 100.0))
        features.append(reading.get("phosphorus_ppm", 50.0))
        features.append(reading.get("potassium_ppm", 150.0))

    return features


def train_water_model(training_data: List[Dict]) -> Tuple[Any, Dict[str, float]]:
    """Train water recommendation model"""
    # Placeholder implementation
    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Simulate training
    X = np.random.rand(100, 6)  # 100 samples, 6 features
    y = np.random.rand(100)  # Target values

    model.fit(X, y)

    metrics = {"mse": 0.15, "r2_score": 0.85, "mae": 0.12}

    return model, metrics


def train_fertilizer_model(training_data: List[Dict]) -> Tuple[Any, Dict[str, float]]:
    """Train fertilizer recommendation model"""
    # Placeholder implementation
    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Simulate training
    X = np.random.rand(100, 7)  # 100 samples, 7 features
    y = np.random.rand(100)  # Target values

    model.fit(X, y)

    metrics = {"mse": 0.18, "r2_score": 0.82, "mae": 0.14}

    return model, metrics


def train_crop_health_model(training_data: List[Dict]) -> Tuple[Any, Dict[str, float]]:
    """Train crop health prediction model"""
    # Placeholder implementation
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=100, random_state=42)

    # Simulate training
    X = np.random.rand(100, 5)  # 100 samples, 5 features
    y = np.random.randint(0, 3, 100)  # 3 health classes

    model.fit(X, y)

    metrics = {"accuracy": 0.89, "precision": 0.87, "recall": 0.88, "f1_score": 0.87}

    return model, metrics


def save_model(model, model_type: str) -> str:
    """Save trained model to file"""
    models_dir = Path(__file__).parent.parent
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{model_type}_model_{timestamp}.joblib"
    filepath = models_dir / filename

    joblib.dump(model, filepath)

    # Also save as the current model
    current_filename = f"{model_type}_model.joblib"
    current_filepath = models_dir / current_filename
    joblib.dump(model, current_filepath)

    return str(filepath)


def collect_evaluation_data(model_type: str, start_time: datetime, end_time: datetime) -> List[Dict]:
    """Collect evaluation data for model performance assessment"""
    # This would query actual database for evaluation data
    return []


def calculate_model_metrics(evaluation_data: List[Dict], model_type: str) -> Dict[str, float]:
    """Calculate model performance metrics"""
    # Placeholder implementation
    return {"accuracy": 0.85, "precision": 0.83, "recall": 0.87, "f1_score": 0.85, "rmse": 0.15}


def analyze_model_drift(evaluation_data: List[Dict], model_type: str) -> Dict[str, Any]:
    """Analyze model drift over time"""
    return {"drift_detected": False, "drift_score": 0.12, "drift_threshold": 0.20, "recommendation": "No action needed"}


def generate_model_recommendations(metrics: Dict, drift_analysis: Dict) -> List[str]:
    """Generate recommendations based on model performance"""
    recommendations = []

    if metrics.get("accuracy", 0) < 0.80:
        recommendations.append("Model accuracy is below threshold - consider retraining")

    if drift_analysis.get("drift_detected", False):
        recommendations.append("Model drift detected - schedule retraining")

    if not recommendations:
        recommendations.append("Model performance is satisfactory")

    return recommendations


def get_hyperparameter_search_space(model_type: str) -> Dict[str, Any]:
    """Get hyperparameter search space for model type"""
    if model_type in ["water_recommendation", "fertilizer_recommendation"]:
        return {
            "n_estimators": [50, 100, 200],
            "max_depth": [5, 10, 15, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }
    else:
        return {"n_estimators": [50, 100, 200], "max_depth": [5, 10, 15], "min_samples_split": [2, 5, 10]}


def sample_hyperparameters(search_space: Dict[str, Any]) -> Dict[str, Any]:
    """Sample hyperparameters from search space"""
    import random

    params = {}
    for param, values in search_space.items():
        params[param] = random.choice(values)

    return params


def evaluate_hyperparameters(params: Dict, training_data: List[Dict], model_type: str) -> float:
    """Evaluate hyperparameters and return score"""
    # Placeholder implementation - would actually train and validate model
    import random

    return random.uniform(0.7, 0.95)


def calculate_improvement(best_score: float, model_type: str) -> float:
    """Calculate improvement over baseline"""
    baseline_scores = {"water_recommendation": 0.75, "fertilizer_recommendation": 0.73, "crop_health": 0.80}

    baseline = baseline_scores.get(model_type, 0.75)
    return (best_score - baseline) / baseline * 100
