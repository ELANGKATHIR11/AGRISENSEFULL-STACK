import os
import json
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast, TYPE_CHECKING

# Lazy ML imports: these will be populated inside the class initializer
# to avoid heavy import-time overhead when the module is imported by
# tooling (generators, CI, etc.). Set placeholders here so runtime checks
# can determine whether those libraries are available.
joblib = None  # type: ignore
np = None
pd = None
RandomForestClassifier = None
RandomForestRegressor = None
LabelEncoder = None
StandardScaler = None

if TYPE_CHECKING:
    # Make types available to static checkers without importing heavy ML libs at runtime
    import joblib as _joblib  # type: ignore
    import numpy as _np
    import pandas as _pd
    from sklearn.ensemble import RandomForestClassifier as _RFC, RandomForestRegressor as _RFR
    from sklearn.preprocessing import LabelEncoder as _LabelEncoder, StandardScaler as _StandardScaler  # type: ignore
    # Expose for type annotations
    joblib = _joblib  # type: ignore
    np = _np  # type: ignore
    pd = _pd  # type: ignore
    RandomForestClassifier = _RFC  # type: ignore
    RandomForestRegressor = _RFR  # type: ignore
    LabelEncoder = _LabelEncoder  # type: ignore
    StandardScaler = _StandardScaler  # type: ignore

warnings.filterwarnings("ignore")

HERE = os.path.dirname(__file__)

# small safe helpers to avoid calling attributes on None (when numpy/pandas/etc. aren't available)
def _get_np():
    return globals().get("np")


class SmartFarmingRecommendationSystem:
    """Crop recommendation and suggestions system.

    - Loads dataset from CSV or uses a fallback sample
    - Trains RandomForest models for yield and crop classification
    - Optionally loads TensorFlow/Keras models if present
    - Provides recommendations and actionable suggestions
    """

    def       
        self.dataset_path: str = dataset_path

        # Lazy-import ML libraries to avoid heavy import-time cost. When
        # AGRISENSE_DISABLE_ML is set we skip importing ML packages so the
        # module can be imported safely in CI or small tooling processes.
        if os.getenv("AGRISENSE_DISABLE_ML"):
            print(
                "AGRISENSE_DISABLE_ML set: skipping ML library imports in SmartFarmingRecommendationSystem.__init__"
            )
        else:
            try:
                import joblib as _joblib  # type: ignore
                import numpy as _np
                import pandas as _pd
                from sklearn.ensemble import (
                    RandomForestClassifier as _RFC,
                    RandomForestRegressor as _RFR,
                )
                from sklearn.preprocessing import (
                    LabelEncoder as _LabelEncoder,
                    StandardScaler as _StandardScaler,
                )

                globals()["joblib"] = _joblib
                globals()["np"] = _np
                globals()["pd"] = _pd
                globals()["RandomForestClassifier"] = _RFC
                globals()["RandomForestRegressor"] = _RFR
                globals()["LabelEncoder"] = _LabelEncoder
                globals()["StandardScaler"] = _StandardScaler
            except Exception as e:
                print(f"SmartFarmingRecommendationSystem: failed lazy ML imports: {e}")

        # Runtime-safe storage (use Any where concrete ML classes may be absent)
        self.crop_data: Optional[Any] = None
        self.yield_model: Optional[Any] = None
        self.crop_classifier: Optional[Any] = None
        self.water_optimizer: Optional[Any] = None
        self.fertilizer_optimizer: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.label_encoder: Optional[Any] = None
        self.soil_encoder: Optional[Any] = None
        self.crop_encoder: Optional[Any] = None

        # Instantiate scaler/label encoder only if the classes were successfully imported
        if globals().get("StandardScaler") is not None:
            try:
                self.scaler = _instantiate_cls("StandardScaler")
            except Exception:
                self.scaler = None
        if globals().get("LabelEncoder") is not None:
            try:
                self.label_encoder = _instantiate_cls("LabelEncoder")
            except Exception:
                self.label_encoder = None

        # Optional TensorFlow models (loaded if available)
        self.tf_enabled: bool = False
        self.tf_yield_model: Optional[Any] = None
        self.tf_crop_model: Optional[Any] = None
        self.tf_meta: Optional[Dict[str, Any]] = None  # expects keys: soil_types, crops

        self.load_dataset()
        self.prepare_models()
        self._maybe_load_tf_models()
        # Lazy-import ML libraries to avoid heavy import-time cost. When
    def load_dataset(self) -> None:
        """Load crop dataset from CSV if available, else use a small sample."""
        csv_path = self.dataset_path
        if not os.path.isabs(csv_path):
            csv_path = os.path.join(HERE, csv_path)

        # Try to read CSV only if pandas is available
        if globals().get("pd") is not None and os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding="utf-8-sig")  # type: ignore[call-overload]
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
                self.crop_data = df[required_cols].copy()
                try:
                    shape_info = getattr(self.crop_data, "shape", None)
                    print(
                        f"Loaded dataset from {os.path.basename(csv_path)} with shape {shape_info}"
                    )
                except Exception:
                    print(f"Loaded dataset from {os.path.basename(csv_path)}")
                return
            except Exception as e:
                print(
                    f"Failed to load CSV dataset at {csv_path}: {e}. Falling back to sample data."
                )

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
    def prepare_models(self) -> None:
        assert self.crop_data is not None, "Dataset not loaded"

        # If essential ML libraries are not available, skip model preparation gracefully.
        required = ["joblib", "np", "pd", "RandomForestRegressor", "RandomForestClassifier", "LabelEncoder"]
        if any(globals().get(r) is None for r in required):
            print("ML libraries not fully available; skipping model training/loading.")
            return

        # Attempt to load cached models/encoders first to avoid retraining on every cold start
        yield_path = os.path.join(HERE, "yield_prediction_model.joblib")
        clf_path = os.path.join(HERE, "crop_classification_model.joblib")
        soil_enc_path = os.path.join(HERE, "soil_encoder.joblib")
        crop_enc_path = os.path.join(HERE, "crop_encoder.joblib")
        try:
            if all(os.path.exists(p) for p in [yield_path, clf_path, soil_enc_path, crop_enc_path]):
                jb = globals().get("joblib")
                if jb is None:
                    raise RuntimeError("joblib not available to load models")
                self.yield_model = cast(Any, jb).load(yield_path)  # type: ignore[attr-defined]
                self.crop_classifier = cast(Any, jb).load(clf_path)  # type: ignore[attr-defined]
                self.soil_encoder = cast(Any, jb).load(soil_enc_path)  # type: ignore[attr-defined]
                self.crop_encoder = cast(Any, jb).load(crop_enc_path)  # type: ignore[attr-defined]
                # Also ensure encoded columns exist for feature building when needed (pandas case)
                if hasattr(self.crop_data, "columns"):
                    if "Soil_Type_Encoded" not in self.crop_data.columns:
                        assert self.soil_encoder is not None
                        self.crop_data["Soil_Type_Encoded"] = cast(Any, self.soil_encoder).transform(self.crop_data["Soil_Type"])  # type: ignore[index]
                    if "Crop_Encoded" not in self.crop_data.columns:
                        assert self.crop_encoder is not None
                        self.crop_data["Crop_Encoded"] = cast(Any, self.crop_encoder).transform(self.crop_data["Crop"])  # type: ignore[index]
                print("Loaded cached ML models and encoders.")
                return
        except Exception as e:
            print(f"Failed to load cached models, will retrain: {e}")

        # Encode categorical variables for training (pandas assumed here because ML libs exist)
        soil_encoder = _instantiate_cls("LabelEncoder")
        self.crop_data["Soil_Type_Encoded"] = soil_encoder.fit_transform(
            self.crop_data["Soil_Type"]
        )
        crop_encoder = _instantiate_cls("LabelEncoder")
        self.crop_data["Crop_Encoded"] = crop_encoder.fit_transform(
            self.crop_data["Crop"]
        )

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

        X = self.crop_data[feature_columns]

        # Train yield prediction model
        y_yield = self.crop_data["Expected_Yield_tonnes_ha"]
        self.yield_model = _instantiate_cls("RandomForestRegressor", n_estimators=100, random_state=42)
        X_arr = _asarray(X, dtype=float)
        y_yield_arr = _asarray(y_yield, dtype=float)
        cast(Any, self.yield_model).fit(X_arr, y_yield_arr)

        # Train crop classification model
        y_crop = self.crop_data["Crop_Encoded"]
        self.crop_classifier = _instantiate_cls("RandomForestClassifier", n_estimators=100, random_state=42)
        y_crop_arr = _asarray(y_crop, dtype=int)
        cast(Any, self.crop_classifier).fit(X_arr, y_crop_arr)

        # Store encoders
        self.soil_encoder = soil_encoder
        self.crop_encoder = crop_encoder

        # Save models and encoders for next runs
        jb: Any = globals().get("joblib")
        if jb is not None:
            jb.dump(self.yield_model, yield_path)
            jb.dump(self.crop_classifier, clf_path)
            jb.dump(self.soil_encoder, soil_enc_path)
            jb.dump(self.crop_encoder, crop_enc_path)

        print("ML models trained and saved successfully!")
                1200,
                500,
                300,
                350,
                650,
                500,
            ],
            "Moisture_Optimal_percent": [70, 60, 75, 55, 80, 60, 55, 50, 60, 65],
            "Humidity_Optimal_percent": [80, 65, 80, 65, 90, 70, 60, 60, 70, 70],
            "Expected_Yield_tonnes_ha": [
                4.5,
                3.2,
                70,
                1.8,
                2.5,
                1.2,
                1.1,
                0.9,
                0.8,
                2.5,
            ],
            "Water_Efficiency_Index": [
    def get_crop_recommendations(self, sensor_data: SensorData) -> List[Recommendation]:
        try:
            assert self.crop_data is not None, "Dataset not loaded"

            current_ph = float(sensor_data.get("ph", 7.0))
            current_n = float(sensor_data.get("nitrogen", 100))
            current_p = float(sensor_data.get("phosphorus", 40))
            current_k = float(sensor_data.get("potassium", 40))
            current_temp = float(sensor_data.get("temperature", 25))
            current_water = float(sensor_data.get("water_level", 500))
            current_moisture = float(sensor_data.get("moisture", 60))
            current_humidity = float(sensor_data.get("humidity", 70))
            soil_type = str(sensor_data.get("soil_type", "Loam"))

            # Encode soil type for classic models (safe handling if encoder present)
            try:
                if self.soil_encoder is None:
                    raise ValueError("Soil encoder not initialized")
                transformed = self.soil_encoder.transform([soil_type])
                # transformed may be numpy array or list
                try:
                    first_val = transformed[0]
                except Exception:
                    first_val = transformed
                _soil_encoded = int(first_val) if first_val is not None else 0
            except Exception:
                _soil_encoded = 0  # Default encoding
            # use variable to avoid unused warning
            _ = _soil_encoded

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
                    water_req_input = float(_clip(current_water, 0, 3000))
                    X_clf = _array(
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
                        dtype=getattr(_get_np(), "float32", None),
                    )
                    probs = self.tf_crop_model.predict(X_clf, verbose=0)[0]
                    crops: List[str] = self.tf_meta.get("crops", [])
                    for i, c in enumerate(crops):
                        prob_by_crop[c] = float(probs[i]) if i < len(probs) else 0.0
                except Exception as e:
                    print(f"TF crop probability inference failed: {e}")

            crop_scores: List[Recommendation] = []
            # Support both pandas DataFrame and plain Python list of dicts
            if hasattr(self.crop_data, "iterrows"):
                iterator = self.crop_data.iterrows()
                extract = lambda row, key: row[key]
            else:
                iterator = enumerate(self.crop_data)
                extract = lambda row, key: row[key]

            for _, crop in iterator:
                # crop may be a pandas Series or a plain dict
                ph_score = 1 - abs(current_ph - float(extract(crop, "pH_Optimal"))) / 2.0
                n_score = 1 - abs(current_n - float(extract(crop, "Nitrogen_Optimal_kg_ha"))) / 200.0
                p_score = 1 - abs(current_p - float(extract(crop, "Phosphorus_Optimal_kg_ha"))) / 100.0
                k_score = 1 - abs(current_k - float(extract(crop, "Potassium_Optimal_kg_ha"))) / 100.0
                temp_score = 1 - abs(current_temp - float(extract(crop, "Temperature_Optimal_C"))) / 20.0
                moisture_score = 1 - abs(current_moisture - float(extract(crop, "Moisture_Optimal_percent"))) / 50.0
                humidity_score = 1 - abs(current_humidity - float(extract(crop, "Humidity_Optimal_percent"))) / 50.0

                similarity_score = float(
                    _mean(
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

                expected_yield = float(extract(crop, "Expected_Yield_tonnes_ha"))
                if (
                    self.tf_enabled
                    and self.tf_yield_model is not None
                    and self.tf_meta is not None
                ):
                    try:
                        soil_ix = _tf_soil_ix(soil_type)
                        X_reg = _array(
                            [
                                [
                                    float(extract(crop, "pH_Optimal")),
                                    float(extract(crop, "Nitrogen_Optimal_kg_ha")),
                                    float(extract(crop, "Phosphorus_Optimal_kg_ha")),
                                    float(extract(crop, "Potassium_Optimal_kg_ha")),
                                    float(extract(crop, "Temperature_Optimal_C")),
                                    float(extract(crop, "Water_Requirement_mm")),
                                    float(extract(crop, "Moisture_Optimal_percent")),
                                    float(extract(crop, "Humidity_Optimal_percent")),
                                    float(soil_ix),
                                ]
                            ],
                            dtype=getattr(_get_np(), "float32", None),
                        )
                        y_pred = self.tf_yield_model.predict(X_reg, verbose=0)[0][0]
                        expected_yield = float(max(0.0, float(y_pred)))
                    except Exception as e:
                        try:
                            crop_name = str(extract(crop, "Crop"))
                        except Exception:
                            crop_name = "<unknown>"
                        print(f"TF yield inference failed for {crop_name}: {e}")

                prob_component = prob_by_crop.get(str(extract(crop, "Crop")), None)
                if prob_component is None:
                    final_score = similarity_score
                else:
                    eff = float(
                        extract(crop, "Water_Efficiency_Index") if isinstance(crop, dict) else crop.get("Water_Efficiency_Index", 0.0)
                        + extract(crop, "Fertilizer_Efficiency_Index") if isinstance(crop, dict) else crop.get("Fertilizer_Efficiency_Index", 0.0)
    def get_farming_suggestions(self, sensor_data: SensorData, selected_crop: str) -> Dict[str, Any]:
        try:
            assert self.crop_data is not None, "Dataset not loaded"
            # Support both pandas DataFrame and plain list fallback
            if hasattr(self.crop_data, "loc") or hasattr(self.crop_data, "iloc") or hasattr(self.crop_data, "columns"):
                matches = self.crop_data[self.crop_data["Crop"] == selected_crop]
                if getattr(matches, "empty", False):
                    return {"error": f"Crop {selected_crop} not found in dataset"}
                crop_info = matches.iloc[0]
                get_val = lambda key: crop_info[key]
            else:
                matches = [r for r in self.crop_data if r.get("Crop") == selected_crop]
                if not matches:
                    return {"error": f"Crop {selected_crop} not found in dataset"}
                crop_info = matches[0]
                get_val = lambda key: crop_info.get(key)

            suggestions: Dict[str, Any] = {
                "crop": selected_crop,
                "current_conditions": sensor_data,
                "optimal_conditions": {
                    "ph": get_val("pH_Optimal"),
                    "nitrogen": get_val("Nitrogen_Optimal_kg_ha"),
                    "phosphorus": get_val("Phosphorus_Optimal_kg_ha"),
                    "potassium": get_val("Potassium_Optimal_kg_ha"),
                    "temperature": get_val("Temperature_Optimal_C"),
                    "moisture": get_val("Moisture_Optimal_percent"),
                    "humidity": get_val("Humidity_Optimal_percent"),
                    "water_requirement": get_val("Water_Requirement_mm"),
                },
                "recommendations": [],
            }

                self.tf_yield_model = keras.models.load_model(y_path)  # type: ignore[attr-defined]
                self.tf_crop_model = keras.models.load_model(c_path)  # type: ignore[attr-defined]
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.tf_meta = json.load(f)
                self.tf_enabled = True
                print("Loaded TensorFlow crop models: yield_tf.keras, crop_tf.keras")
            else:
                missing = [
                    p for p in [y_path, c_path, meta_path] if not os.path.exists(p)
                ]
                if missing:
                    print(
                        f"TensorFlow crop models not found, missing: {', '.join(os.path.basename(m) for m in missing)}"
                    )
        except Exception as e:
            print(
                f"Failed to load TensorFlow models: {e}. Proceeding without TF models."
            )

    def get_crop_recommendations(self, sensor_data: SensorData) -> List[Recommendation]:
        try:
            assert self.crop_data is not None, "Dataset not loaded"

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
                _soil_encoded = int(
                    transformed[0].item() if transformed.size > 0 else 0
                )
            except Exception:
                _soil_encoded = 0  # Default encoding

            def _tf_soil_ix(soil: str) -> int:
                if self.tf_enabled and self.tf_meta and "soil_types" in self.tf_meta:
                    try:
                        return int(self.tf_meta["soil_types"].index(str(soil)))
                    except ValueError:
                        return 0
                return 0

            prob_by_crop: Dict[str, float] = {}
            if (
                self.tf_enabled
                and self.tf_crop_model is not None
                and self.tf_meta is not None
            ):
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
                ph_score = 1 - abs(current_ph - float(crop["pH_Optimal"])) / 2.0
                n_score = (
                    1 - abs(current_n - float(crop["Nitrogen_Optimal_kg_ha"])) / 200.0
                )
                p_score = (
                    1 - abs(current_p - float(crop["Phosphorus_Optimal_kg_ha"])) / 100.0
                )
                k_score = (
                    1 - abs(current_k - float(crop["Potassium_Optimal_kg_ha"])) / 100.0
                )
                temp_score = (
                    1 - abs(current_temp - float(crop["Temperature_Optimal_C"])) / 20.0
                )
                moisture_score = (
                    1
                    - abs(current_moisture - float(crop["Moisture_Optimal_percent"]))
                    / 50.0
                )
                humidity_score = (
                    1
                    - abs(current_humidity - float(crop["Humidity_Optimal_percent"]))
                    / 50.0
                )

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
    def simulate_iot_data(self) -> Dict[str, Union[float, str]]:
        return {
            "ph": _rand_normal(6.8, 0.5),
            "nitrogen": _rand_normal(100, 20),
            "phosphorus": _rand_normal(40, 10),
            "potassium": _rand_normal(40, 10),
            "temperature": _rand_normal(25, 5),
            "water_level": _rand_normal(500, 100),
            "moisture": _rand_normal(60, 10),
            "humidity": _rand_normal(70, 10),
            "soil_type": _rand_choice(["Loam", "Clay Loam", "Sandy Loam", "Sandy", "Black Cotton"]),
        }
                                    float(crop["pH_Optimal"]),
                                    float(crop["Nitrogen_Optimal_kg_ha"]),
                                    float(crop["Phosphorus_Optimal_kg_ha"]),
                                    float(crop["Potassium_Optimal_kg_ha"]),
                                    float(crop["Temperature_Optimal_C"]),
                                    float(crop["Water_Requirement_mm"]),
                                    float(crop["Moisture_Optimal_percent"]),
                                    float(crop["Humidity_Optimal_percent"]),
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
                    eff = (
                        float(
                            crop.get("Water_Efficiency_Index", 0.0)
                            + crop.get("Fertilizer_Efficiency_Index", 0.0)
                        )
                        / 2.0
                    )
                    final_score = (
                        0.6 * similarity_score + 0.3 * float(prob_component) + 0.1 * eff
                    )
                final_score = float(np.clip(final_score, 0.0, 1.0))

                crop_scores.append(
                    {
                        "crop": str(crop["Crop"]),
                        "suitability_score": final_score,
                        "expected_yield": expected_yield,
                        "water_efficiency": float(crop["Water_Efficiency_Index"]),
                        "fertilizer_efficiency": float(
                            crop["Fertilizer_Efficiency_Index"]
                        ),
                    }
                )

            crop_scores.sort(key=lambda x: x["suitability_score"], reverse=True)
            return crop_scores[:5]
        except Exception as e:
            print(f"Error in crop recommendations: {e}")
            return []

    def get_farming_suggestions(
        self, sensor_data: SensorData, selected_crop: str
    ) -> Dict[str, Any]:
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
                            "priority": (
                                "high"
                                if abs(current_ph - optimal_ph) > 1.0
                                else "medium"
                            ),
                        }
                    )
                else:
                    suggestions["recommendations"].append(
                        {
                            "parameter": "pH",
                            "action": "decrease",
                            "suggestion": f"Add sulfur or organic matter to decrease pH from {current_ph:.1f} to optimal {optimal_ph:.1f}",
                            "priority": (
                                "high"
                                if abs(current_ph - optimal_ph) > 1.0
                                else "medium"
                            ),
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
            "soil_type": str(
                np.random.choice(
                    ["Loam", "Clay Loam", "Sandy Loam", "Sandy", "Black Cotton"]
                )
            ),
        }

    def generate_report(self, sensor_data: SensorData) -> None:
        print("=" * 60)
        print("\U0001f331 SMART FARMING RECOMMENDATION REPORT \U0001f331")
        print("=" * 60)
        print(
            f"\U0001f4c5 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
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
        recommendations: List[Recommendation] = self.get_crop_recommendations(
            sensor_data
        )

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
                        "\U0001f534"
                        if priority == "high"
                        else ("\U0001f7e1" if priority == "medium" else "\U0001f7e2")
                    )
                    param: str = str(rec.get("parameter", ""))
                    sugg: str = str(rec.get("suggestion", ""))
                    print(f"{priority_icon} {param.upper()}: {sugg}")
                    if "eco_friendly_option" in rec:
                        print(
                            f"   \U0001f333 Eco-friendly option: {rec['eco_friendly_option']}"
                        )
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
    print(
        f"Number of suggestions for Rice: {len(suggestions.get('recommendations', []))}"
    )

    print("\n\U0001f389 System ready for IoT integration!")
    print(
        "\U0001f4a1 Connect your sensors and start getting real-time recommendations!"
    )
