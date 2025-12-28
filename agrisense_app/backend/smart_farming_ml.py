import os
import json
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

import joblib  # type: ignore
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

HERE = os.path.dirname(__file__)

# Type aliases
SensorData = Dict[str, Union[float, int, str]]
Recommendation = Dict[str, Union[str, float]]


class SmartFarmingRecommendationSystem:
    """Crop recommendation and suggestions system.

    - Loads dataset from CSV or uses a fallback sample
    - Trains RandomForest models for yield and crop classification
    - Optionally loads TensorFlow/Keras models if present
    - Provides recommendations and actionable suggestions
    """

    def __init__(self, dataset_path: str = "india_crop_dataset.csv") -> None:
        self.dataset_path: str = dataset_path
        self.crop_data: Optional[pd.DataFrame] = None
        self.yield_model: Optional[RandomForestRegressor] = None
        self.crop_classifier: Optional[RandomForestClassifier] = None
        self.water_optimizer: Optional[Any] = None
        self.fertilizer_optimizer: Optional[Any] = None
        self.scaler: StandardScaler = StandardScaler()
        self.label_encoder: LabelEncoder = LabelEncoder()
        self.soil_encoder: Optional[LabelEncoder] = None
        self.crop_encoder: Optional[LabelEncoder] = None

        # Optional TensorFlow models (loaded if available)
        self.tf_enabled: bool = False
        self.tf_yield_model: Optional[Any] = None
        self.tf_crop_model: Optional[Any] = None
        self.tf_meta: Optional[Dict[str, Any]] = None  # expects keys: soil_types, crops

        self.load_dataset()
        self.prepare_models()
        self._maybe_load_tf_models()

    def load_dataset(self) -> None:
        """Load crop dataset from CSV if available, else use a small sample."""
        csv_path = self.dataset_path
        if not os.path.isabs(csv_path):
            csv_path = os.path.join(HERE, csv_path)

        if os.path.exists(csv_path):
            try:
                df: pd.DataFrame = pd.read_csv(csv_path, encoding="utf-8-sig")  # type: ignore[call-overload]
                required_cols: List[str] = [
                    "Crop",
                    "Soil_Type",
                    "pH_Optimal",
                    "Nitrogen_Optimal_kg_ha",
                    "Phosphorus_Optimal_kg_ha",
                    "Potassium_Optimal_kg_ha",
                    "Temperature_Optimal_C",
                    "Water_Requirement_mm",
                    "Moisture_Optimal_percent",
                    "Humidity_Optimal_percent",
                    "Expected_Yield_tonnes_ha",
                    "Water_Efficiency_Index",
                    "Fertilizer_Efficiency_Index",
                ]
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    raise ValueError(f"Dataset missing columns: {missing}")
                self.crop_data = cast(pd.DataFrame, df[required_cols].copy())
                _shape = getattr(self.crop_data, "shape", (0, 0))
                print(f"Loaded dataset from {os.path.basename(csv_path)} with shape {_shape}")
                return
            except Exception as e:
                print(f"Failed to load CSV dataset at {csv_path}: {e}. Falling back to sample data.")

        # Fallback sample dataset
        data: Dict[str, List[Union[str, float, int]]] = {
            "Crop": [
                "Rice",
                "Wheat",
                "Sugarcane",
                "Cotton",
                "Jute",
                "Groundnut",
                "Rapeseed_Mustard",
                "Gram",
                "Tur_Arhar",
                "Maize",
            ],
            "Soil_Type": [
                "Clay Loam",
                "Loam",
                "Clay Loam",
                "Black Cotton",
                "Clay Loam",
                "Sandy Loam",
                "Loam",
                "Clay Loam",
                "Clay Loam",
                "Loam",
            ],
            "pH_Optimal": [6.2, 6.8, 6.8, 7.0, 6.2, 6.5, 6.8, 7.0, 7.0, 6.8],
            "Nitrogen_Optimal_kg_ha": [100, 125, 200, 90, 60, 30, 80, 30, 35, 150],
            "Phosphorus_Optimal_kg_ha": [35, 40, 60, 30, 25, 60, 40, 60, 60, 60],
            "Potassium_Optimal_kg_ha": [35, 40, 80, 35, 30, 45, 35, 35, 40, 60],
            "Temperature_Optimal_C": [28, 20, 28, 27, 30, 26, 18, 22, 25, 24],
            "Water_Requirement_mm": [1200, 450, 1800, 600, 1200, 500, 300, 350, 650, 500],
            "Moisture_Optimal_percent": [70, 60, 75, 55, 80, 60, 55, 50, 60, 65],
            "Humidity_Optimal_percent": [80, 65, 80, 65, 90, 70, 60, 60, 70, 70],
            "Expected_Yield_tonnes_ha": [4.5, 3.2, 70, 1.8, 2.5, 1.2, 1.1, 0.9, 0.8, 2.5],
            "Water_Efficiency_Index": [0.85, 0.92, 0.8, 0.88, 0.83, 0.9, 0.93, 0.95, 0.89, 0.87],
            "Fertilizer_Efficiency_Index": [0.9, 0.88, 0.85, 0.87, 0.85, 0.92, 0.9, 0.94, 0.91, 0.86],
        }
        self.crop_data = pd.DataFrame(data)
        print("Loaded sample dataset (CSV not found)")
        print(f"Dataset shape: {self.crop_data.shape}")

    def prepare_models(self) -> None:
        assert self.crop_data is not None, "Dataset not loaded"

        # Attempt to load cached models/encoders first to avoid retraining on every cold start
        yield_path = os.path.join(HERE, "yield_prediction_model.joblib")
        clf_path = os.path.join(HERE, "crop_classification_model.joblib")
        soil_enc_path = os.path.join(HERE, "soil_encoder.joblib")
        crop_enc_path = os.path.join(HERE, "crop_encoder.joblib")
        try:
            if all(os.path.exists(p) for p in [yield_path, clf_path, soil_enc_path, crop_enc_path]):
                self.yield_model = cast(Any, joblib).load(yield_path)  # type: ignore[attr-defined]
                self.crop_classifier = cast(Any, joblib).load(clf_path)  # type: ignore[attr-defined]
                self.soil_encoder = cast(Any, joblib).load(soil_enc_path)  # type: ignore[attr-defined]
                self.crop_encoder = cast(Any, joblib).load(crop_enc_path)  # type: ignore[attr-defined]
                # Also ensure encoded columns exist for feature building when needed
                if "Soil_Type_Encoded" not in self.crop_data.columns:
                    assert self.soil_encoder is not None
                    self.crop_data["Soil_Type_Encoded"] = cast(LabelEncoder, self.soil_encoder).transform(
                        self.crop_data["Soil_Type"]
                    )  # type: ignore[index]
                if "Crop_Encoded" not in self.crop_data.columns:
                    assert self.crop_encoder is not None
                    self.crop_data["Crop_Encoded"] = cast(LabelEncoder, self.crop_encoder).transform(
                        self.crop_data["Crop"]
                    )  # type: ignore[index]
                print("Loaded cached ML models and encoders.")
                return
        except Exception as e:
            print(f"Failed to load cached models, will retrain: {e}")

        # Encode categorical variables for training
        soil_encoder: LabelEncoder = LabelEncoder()
        self.crop_data["Soil_Type_Encoded"] = soil_encoder.fit_transform(
            self.crop_data["Soil_Type"]
        )  # type: ignore[index]
        crop_encoder: LabelEncoder = LabelEncoder()
        self.crop_data["Crop_Encoded"] = crop_encoder.fit_transform(self.crop_data["Crop"])  # type: ignore[index]

        # Features for training
        feature_columns: List[str] = [
            "pH_Optimal",
            "Nitrogen_Optimal_kg_ha",
            "Phosphorus_Optimal_kg_ha",
            "Potassium_Optimal_kg_ha",
            "Temperature_Optimal_C",
            "Water_Requirement_mm",
            "Moisture_Optimal_percent",
            "Humidity_Optimal_percent",
            "Soil_Type_Encoded",
        ]

        X: pd.DataFrame = cast(pd.DataFrame, self.crop_data[feature_columns])

        # Train yield prediction model
        y_yield: pd.Series = cast(pd.Series, self.crop_data["Expected_Yield_tonnes_ha"])  # type: ignore[index]
        self.yield_model = RandomForestRegressor(n_estimators=100, random_state=42)
        X_arr = np.asarray(X, dtype=float)
        y_yield_arr = np.asarray(y_yield, dtype=float)
        cast(Any, self.yield_model).fit(X_arr, y_yield_arr)

        # Train crop classification model
        y_crop: pd.Series = cast(pd.Series, self.crop_data["Crop_Encoded"])  # type: ignore[index]
        self.crop_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        y_crop_arr = np.asarray(y_crop, dtype=int)
        cast(Any, self.crop_classifier).fit(X_arr, y_crop_arr)

        # Store encoders
        self.soil_encoder = soil_encoder
        self.crop_encoder = crop_encoder

        # Save models and encoders for next runs
        jb: Any = joblib
        jb.dump(self.yield_model, yield_path)
        jb.dump(self.crop_classifier, clf_path)
        jb.dump(self.soil_encoder, soil_enc_path)
        jb.dump(self.crop_encoder, crop_enc_path)

        print("ML models trained and saved successfully!")

    def _maybe_load_tf_models(self) -> None:
        """Load optional TensorFlow models if available; otherwise keep TF disabled."""
        # Honor global ML disable flag to keep dev/tests light
        if str(os.getenv("AGRISENSE_DISABLE_ML", "0")).lower() in ("1", "true", "yes"):
            print("AGRISENSE_DISABLE_ML is set; skipping TensorFlow model loading.")
            return
        try:
            import tensorflow as tf  # type: ignore  # noqa: F401

            if not hasattr(tf, "keras"):
                raise ImportError("tensorflow.keras not available")
        except Exception as e:
            print(f"TensorFlow not available: {e}. Proceeding without TF models.")
            return

        try:
            y_path = os.path.join(HERE, "yield_tf.keras")
            c_path = os.path.join(HERE, "crop_tf.keras")
            meta_path = os.path.join(HERE, "crop_labels.json")
            if os.path.exists(y_path) and os.path.exists(c_path) and os.path.exists(meta_path):
                from tensorflow import keras  # type: ignore

                self.tf_yield_model = keras.models.load_model(y_path)  # type: ignore[attr-defined]
                self.tf_crop_model = keras.models.load_model(c_path)  # type: ignore[attr-defined]
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.tf_meta = json.load(f)
                self.tf_enabled = True
                print("Loaded TensorFlow crop models: yield_tf.keras, crop_tf.keras")
            else:
                missing = [p for p in [y_path, c_path, meta_path] if not os.path.exists(p)]
                if missing:
                    print(
                        f"TensorFlow crop models not found, missing: {', '.join(os.path.basename(m) for m in missing)}"
                    )
        except Exception as e:
            print(f"Failed to load TensorFlow models: {e}. Proceeding without TF models.")

    def get_crop_recommendations(self, sensor_data: SensorData) -> List[Recommendation]:
        try:
            assert self.crop_data is not None, "Dataset not loaded"
            # Helper to coerce diverse pandas/numpy scalars or Series to float safely

            def _fv(x: Any) -> float:
                try:
                    return float(x)
                except Exception:
                    try:
                        arr = np.asarray(x, dtype=float)
                        return float(arr.ravel()[0])
                    except Exception:
                        return 0.0

            current_ph = float(sensor_data.get("ph", 7.0))
            current_n = float(sensor_data.get("nitrogen", 100))
            current_p = float(sensor_data.get("phosphorus", 40))
            current_k = float(sensor_data.get("potassium", 40))
            current_temp = float(sensor_data.get("temperature", 25))
            current_water = float(sensor_data.get("water_level", 500))
            current_moisture = float(sensor_data.get("moisture", 60))
            current_humidity = float(sensor_data.get("humidity", 70))
            soil_type = str(sensor_data.get("soil_type", "Loam"))

            # Encode soil type for classic models
            try:
                if self.soil_encoder is None:
                    raise ValueError("Soil encoder not initialized")
                transformed = np.asarray(self.soil_encoder.transform([soil_type]))
                _soil_encoded = int(transformed[0].item() if transformed.size > 0 else 0)
            except Exception:
                # Default encoding placeholder
                pass

            def _tf_soil_ix(soil: str) -> int:
                if self.tf_enabled and self.tf_meta and "soil_types" in self.tf_meta:
                    try:
                        return int(self.tf_meta["soil_types"].index(str(soil)))
                    except ValueError:
                        return 0
                return 0

            prob_by_crop: Dict[str, float] = {}
            if self.tf_enabled and self.tf_crop_model is not None and self.tf_meta is not None:
                try:
                    soil_ix = _tf_soil_ix(soil_type)
                    water_req_input = float(np.clip(current_water, 0, 3000))
                    X_clf = np.array(
                        [
                            [
                                current_ph,
                                current_n,
                                current_p,
                                current_k,
                                current_temp,
                                water_req_input,
                                current_moisture,
                                current_humidity,
                                float(soil_ix),
                            ]
                        ],
                        dtype=np.float32,
                    )
                    probs = self.tf_crop_model.predict(X_clf, verbose=0)[0]
                    crops: List[str] = self.tf_meta.get("crops", [])
                    for i, c in enumerate(crops):
                        prob_by_crop[c] = float(probs[i]) if i < len(probs) else 0.0
                except Exception as e:
                    print(f"TF crop probability inference failed: {e}")

            crop_scores: List[Recommendation] = []
            for _, crop in self.crop_data.iterrows():
                ph_score = 1 - abs(current_ph - _fv(crop["pH_Optimal"])) / 2.0
                n_score = 1 - abs(current_n - _fv(crop["Nitrogen_Optimal_kg_ha"])) / 200.0
                p_score = 1 - abs(current_p - _fv(crop["Phosphorus_Optimal_kg_ha"])) / 100.0
                k_score = 1 - abs(current_k - _fv(crop["Potassium_Optimal_kg_ha"])) / 100.0
                temp_score = 1 - abs(current_temp - _fv(crop["Temperature_Optimal_C"])) / 20.0
                moisture_score = 1 - abs(current_moisture - _fv(crop["Moisture_Optimal_percent"])) / 50.0
                humidity_score = 1 - abs(current_humidity - _fv(crop["Humidity_Optimal_percent"])) / 50.0

                similarity_score = float(
                    np.mean(
                        [
                            ph_score,
                            n_score,
                            p_score,
                            k_score,
                            temp_score,
                            moisture_score,
                            humidity_score,
                        ]
                    )
                )
                similarity_score = max(0.0, similarity_score)

                expected_yield = _fv(crop["Expected_Yield_tonnes_ha"])
                if self.tf_enabled and self.tf_yield_model is not None and self.tf_meta is not None:
                    try:
                        soil_ix = _tf_soil_ix(soil_type)
                        X_reg = np.array(
                            [
                                [
                                    _fv(crop["pH_Optimal"]),
                                    _fv(crop["Nitrogen_Optimal_kg_ha"]),
                                    _fv(crop["Phosphorus_Optimal_kg_ha"]),
                                    _fv(crop["Potassium_Optimal_kg_ha"]),
                                    _fv(crop["Temperature_Optimal_C"]),
                                    _fv(crop["Water_Requirement_mm"]),
                                    _fv(crop["Moisture_Optimal_percent"]),
                                    _fv(crop["Humidity_Optimal_percent"]),
                                    float(soil_ix),
                                ]
                            ],
                            dtype=np.float32,
                        )
                        y_pred = self.tf_yield_model.predict(X_reg, verbose=0)[0][0]
                        expected_yield = float(max(0.0, float(y_pred)))
                    except Exception as e:
                        print(f"TF yield inference failed for {crop['Crop']}: {e}")

                prob_component = prob_by_crop.get(str(crop["Crop"]), None)
                if prob_component is None:
                    final_score = similarity_score
                else:
                    eff = 0.5 * (_fv(crop["Water_Efficiency_Index"]) + _fv(crop["Fertilizer_Efficiency_Index"]))
                    final_score = 0.6 * similarity_score + 0.3 * float(prob_component) + 0.1 * eff
                final_score = float(np.clip(final_score, 0.0, 1.0))

                crop_scores.append(
                    {
                        "crop": str(crop["Crop"]),
                        "suitability_score": final_score,
                        "expected_yield": expected_yield,
                        "water_efficiency": _fv(crop["Water_Efficiency_Index"]),
                        "fertilizer_efficiency": _fv(crop["Fertilizer_Efficiency_Index"]),
                    }
                )

            crop_scores.sort(key=lambda x: x["suitability_score"], reverse=True)
            return crop_scores[:5]
        except Exception as e:
            print(f"Error in crop recommendations: {e}")
            return []

    def get_farming_suggestions(self, sensor_data: SensorData, selected_crop: str) -> Dict[str, Any]:
        try:
            assert self.crop_data is not None, "Dataset not loaded"
            matches = self.crop_data[self.crop_data["Crop"] == selected_crop]
            if matches.empty:
                return {"error": f"Crop {selected_crop} not found in dataset"}
            crop_info = matches.iloc[0]

            suggestions: Dict[str, Any] = {
                "crop": selected_crop,
                "current_conditions": sensor_data,
                "optimal_conditions": {
                    "ph": crop_info["pH_Optimal"],
                    "nitrogen": crop_info["Nitrogen_Optimal_kg_ha"],
                    "phosphorus": crop_info["Phosphorus_Optimal_kg_ha"],
                    "potassium": crop_info["Potassium_Optimal_kg_ha"],
                    "temperature": crop_info["Temperature_Optimal_C"],
                    "moisture": crop_info["Moisture_Optimal_percent"],
                    "humidity": crop_info["Humidity_Optimal_percent"],
                    "water_requirement": crop_info["Water_Requirement_mm"],
                },
                "recommendations": [],
            }

            current_ph = float(sensor_data.get("ph", 7.0))
            optimal_ph = float(crop_info["pH_Optimal"])
            if abs(current_ph - optimal_ph) > 0.5:
                if current_ph < optimal_ph:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "pH",
                            "action": "increase",
                            "suggestion": f"Add lime to increase pH from {current_ph:.1f} to optimal {optimal_ph:.1f}",
                            "priority": "high" if abs(current_ph - optimal_ph) > 1.0 else "medium",
                        }
                    )
                else:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "pH",
                            "action": "decrease",
                            "suggestion": f"Add sulfur or organic matter to decrease pH from {current_ph:.1f} to optimal {optimal_ph:.1f}",
                            "priority": "high" if abs(current_ph - optimal_ph) > 1.0 else "medium",
                        }
                    )

            current_n = float(sensor_data.get("nitrogen", 100))
            optimal_n = float(crop_info["Nitrogen_Optimal_kg_ha"])
            if abs(current_n - optimal_n) > 20:
                if current_n < optimal_n:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "nitrogen",
                            "action": "increase",
                            "suggestion": f"Apply {optimal_n - current_n:.0f} kg/ha of nitrogen fertilizer (urea or ammonium sulfate)",
                            "priority": "high",
                            "eco_friendly_option": "Use organic compost or vermicompost as nitrogen source",
                        }
                    )
                else:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "nitrogen",
                            "action": "reduce",
                            "suggestion": f"Reduce nitrogen application by {current_n - optimal_n:.0f} kg/ha to prevent nutrient burn",
                            "priority": "medium",
                        }
                    )

            current_p = float(sensor_data.get("phosphorus", 40))
            optimal_p = float(crop_info["Phosphorus_Optimal_kg_ha"])
            if abs(current_p - optimal_p) > 15:
                if current_p < optimal_p:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "phosphorus",
                            "action": "increase",
                            "suggestion": f"Apply {optimal_p - current_p:.0f} kg/ha of phosphorus (DAP or SSP)",
                            "priority": "medium",
                            "eco_friendly_option": "Use bone meal or rock phosphate for slow release",
                        }
                    )

            current_k = float(sensor_data.get("potassium", 40))
            optimal_k = float(crop_info["Potassium_Optimal_kg_ha"])
            if abs(current_k - optimal_k) > 15:
                if current_k < optimal_k:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "potassium",
                            "action": "increase",
                            "suggestion": f"Apply {optimal_k - current_k:.0f} kg/ha of potassium (MOP or SOP)",
                            "priority": "medium",
                            "eco_friendly_option": "Use wood ash or potassium-rich organic matter",
                        }
                    )

            current_moisture = float(sensor_data.get("moisture", 60))
            optimal_moisture = float(crop_info["Moisture_Optimal_percent"])
            if abs(current_moisture - optimal_moisture) > 10:
                if current_moisture < optimal_moisture:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "water",
                            "action": "increase",
                            "suggestion": f"Increase irrigation - soil moisture is {current_moisture:.0f}%, needs {optimal_moisture:.0f}%",
                            "priority": "high",
                            "water_saving_tip": "Use drip irrigation or mulching to conserve water",
                        }
                    )
                else:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "water",
                            "action": "reduce",
                            "suggestion": f"Reduce watering - soil moisture is {current_moisture:.0f}%, optimal is {optimal_moisture:.0f}%",
                            "priority": "medium",
                            "drainage_tip": "Improve drainage to prevent waterlogging",
                        }
                    )

            current_temp = float(sensor_data.get("temperature", 25))
            optimal_temp = float(crop_info["Temperature_Optimal_C"])
            if abs(current_temp - optimal_temp) > 5:
                if current_temp < optimal_temp:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "temperature",
                            "action": "increase",
                            "suggestion": f"Temperature is {current_temp:.1f}°C, optimal is {optimal_temp:.1f}°C. Consider row covers or greenhouse",
                            "priority": "low",
                        }
                    )
                else:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "temperature",
                            "action": "decrease",
                            "suggestion": f"Temperature is {current_temp:.1f}°C, optimal is {optimal_temp:.1f}°C. Provide shade or cooling",
                            "priority": "medium",
                        }
                    )

            suggestions["expected_benefits"] = {
                "yield_increase_potential": f"{10 + len(suggestions['recommendations']) * 3}%",
                "water_savings_potential": f"{float(crop_info['Water_Efficiency_Index']) * 100:.0f}%",
                "fertilizer_efficiency": f"{float(crop_info['Fertilizer_Efficiency_Index']) * 100:.0f}%",
                "environmental_impact": "Reduced chemical runoff and improved soil health",
            }

            return suggestions
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return {"error": str(e)}

    def simulate_iot_data(self) -> Dict[str, Union[float, str]]:
        return {
            "ph": float(np.random.normal(6.8, 0.5)),
            "nitrogen": float(np.random.normal(100, 20)),
            "phosphorus": float(np.random.normal(40, 10)),
            "potassium": float(np.random.normal(40, 10)),
            "temperature": float(np.random.normal(25, 5)),
            "water_level": float(np.random.normal(500, 100)),
            "moisture": float(np.random.normal(60, 10)),
            "humidity": float(np.random.normal(70, 10)),
            "soil_type": str(np.random.choice(["Loam", "Clay Loam", "Sandy Loam", "Sandy", "Black Cotton"])),
        }

    def generate_report(self, sensor_data: SensorData) -> None:
        print("=" * 60)
        print("\U0001f331 SMART FARMING RECOMMENDATION REPORT \U0001f331")
        print("=" * 60)
        print(f"\U0001f4c5 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        print("\U0001f4ca CURRENT SENSOR READINGS:")
        print("-" * 30)
        for key, value in sensor_data.items():
            if isinstance(value, float):
                print(f"{key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        print()

        print("\U0001f33e TOP CROP RECOMMENDATIONS:")
        print("-" * 30)
        recommendations: List[Recommendation] = self.get_crop_recommendations(sensor_data)

        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['crop']}")
            print(f"   Suitability: {rec['suitability_score']:.2f} (0-1 scale)")
            print(f"   Expected Yield: {rec['expected_yield']:.1f} tonnes/ha")
            print(f"   Water Efficiency: {rec['water_efficiency']:.0%}")
            print(f"   Fertilizer Efficiency: {rec['fertilizer_efficiency']:.0%}")
            print()

        if recommendations:
            top_crop = str(recommendations[0]["crop"])
            print(f"\U0001f3af DETAILED SUGGESTIONS FOR {top_crop.upper()}:")
            print("-" * 40)

            suggestions = self.get_farming_suggestions(sensor_data, top_crop)

            recs = cast(List[Dict[str, Any]], suggestions.get("recommendations", []))
            if recs:
                for rec in recs:
                    priority: str = str(rec.get("priority", "low"))
                    priority_icon = (
                        "\U0001f534" if priority == "high" else ("\U0001f7e1" if priority == "medium" else "\U0001f7e2")
                    )
                    param: str = str(rec.get("parameter", ""))
                    sugg: str = str(rec.get("suggestion", ""))
                    print(f"{priority_icon} {param.upper()}: {sugg}")
                    if "eco_friendly_option" in rec:
                        print(f"   \U0001f333 Eco-friendly option: {rec['eco_friendly_option']}")
                    print()

            print("\U0001f4c8 EXPECTED BENEFITS:")
            print("-" * 20)
            benefits = cast(Dict[str, Any], suggestions.get("expected_benefits", {}))
            for key, value in benefits.items():
                print(f"• {key.replace('_', ' ').title()}: {value}")

            print()
            print("\U0001f30d SUSTAINABILITY TIPS:")
            print("-" * 25)
            print("• Use drip irrigation to reduce water usage by 30-50%")
            print("• Apply organic compost to improve soil health")
            print("• Practice crop rotation to maintain soil fertility")
            print("• Use integrated pest management to reduce chemical usage")
            print("• Monitor soil health regularly with IoT sensors")

        print("=" * 60)


if __name__ == "__main__":
    farming_system = SmartFarmingRecommendationSystem()
    sensor_data = farming_system.simulate_iot_data()
    farming_system.generate_report(sensor_data)

    print("\n" + "=" * 60)
    print("\U0001f4cb EXAMPLE API USAGE:")
    print("=" * 60)

    crop_recs = farming_system.get_crop_recommendations(sensor_data)
    print(f"Top 3 recommended crops: {[rec['crop'] for rec in crop_recs[:3]]}")

    suggestions = farming_system.get_farming_suggestions(sensor_data, "Rice")
    print(f"Number of suggestions for Rice: {len(suggestions.get('recommendations', []))}")

    print("\n\U0001f389 System ready for IoT integration!")
    print("\U0001f4a1 Connect your sensors and start getting real-time recommendations!")
