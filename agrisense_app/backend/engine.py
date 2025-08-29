import os
import yaml
from typing import Dict, Any, Tuple, List, Optional, Union
import numpy as np  # type: ignore
from joblib import load  # type: ignore

HERE: str = os.path.dirname(__file__)

SOIL_MULT: Dict[str, float] = {"sand": 1.10, "loam": 1.00, "clay": 0.90}

class RecoEngine:
    def __init__(self, cfg_path: Optional[str] = None, crop_params_path: Optional[str] = None) -> None:
        # Load main config
        cfg_path = cfg_path or os.path.join(HERE, "config.yaml")
        with open(cfg_path, "r") as f:
            cfg = yaml.safe_load(f)
        self.cfg = cfg
        self.plants = cfg["plants"]
        self.defaults = cfg["defaults"]
        self.targets_ppm = cfg.get("targets_ppm", {"N": 40, "P": 20, "K": 150})
        self.rs_per_1000l = float(cfg.get("rs_per_1000l", 5.0))
        self.kwh_per_1000l = float(cfg.get("kwh_per_1000l", 0.9))
        self.grid_kgco2_per_kwh = float(cfg.get("grid_kgco2_per_kwh", 0.82))
        # Operational defaults (for user-facing suggestions)
        self.pump_flow_lpm = float(cfg.get("pump_lpm", 20.0))  # liters per minute assumed flow

        # Load ML models if available (can be disabled via env for faster dev)
        # Prefer TensorFlow Keras models if available
        self.water_model: Any = None
        self.fert_model: Any = None
        if not os.getenv("AGRISENSE_DISABLE_ML"):
            tf_water = os.path.join(HERE, "water_model.keras")
            tf_fert = os.path.join(HERE, "fert_model.keras")
            try:
                if os.path.exists(tf_water) and os.path.exists(tf_fert):
                    import tensorflow as tf  # type: ignore
                    self.water_model = tf.keras.models.load_model(tf_water)  # type: ignore[attr-defined]
                    self.fert_model = tf.keras.models.load_model(tf_fert)  # type: ignore[attr-defined]
                else:
                    wm = os.path.join(HERE, "water_model.joblib")
                    fm = os.path.join(HERE, "fert_model.joblib")
                    self.water_model = load(wm) if os.path.exists(wm) else None
                    self.fert_model = load(fm) if os.path.exists(fm) else None
            except Exception:
                # Fallback to joblib if TF load fails
                wm = os.path.join(HERE, "water_model.joblib")
                fm = os.path.join(HERE, "fert_model.joblib")
                self.water_model = load(wm) if os.path.exists(wm) else None
                self.fert_model = load(fm) if os.path.exists(fm) else None

        # Load detailed crop parameters if available
        self.crop_params: Dict[str, Dict[str, Union[float, str]]] = {}
        crop_params_path = crop_params_path or os.path.join(HERE, "crop_parameters.yaml")
        if os.path.exists(crop_params_path):
            with open(crop_params_path, "r") as f:
                crops_raw = yaml.safe_load(f).get("crops", {})
                if isinstance(crops_raw, dict):
                    # Ensure all values are dicts
                    self.crop_params = {str(k): dict(v) for k, v in crops_raw.items() if isinstance(v, dict)}  # type: ignore

    def _plant_cfg(self, plant: str) -> Dict[str, Union[float, str]]:
        # Normalize plant name
        plant_key = plant.lower().strip()
        p = self.plants.get(plant_key) or self.plants.get("generic") or next(iter(self.plants.values()))
        cfg: Dict[str, Union[float, str]] = {
            "kc": float(p.get("kc", 1.0)),
            "ph_min": float(p.get("ph_min", 5.5)),
            "ph_max": float(p.get("ph_max", 8.5)),
            "water_factor": float(p.get("water_factor", 1.0)),
            "n_need": str(p.get("n_need", "medium")),
            "name": plant_key,
        }
        # Enhance with detailed parameters if available
        if plant_key in self.crop_params:
            detailed: Dict[str, Union[float, str]] = self.crop_params[plant_key]
            for k, v in detailed.items():
                cfg[k] = v
        return cfg

    def _baseline_water_lpm2(self, pcfg: Dict[str, Union[float, str]], soil_type: str, moisture: float, temp: float) -> float:
        kc = float(pcfg.get("kc", 1.0))
        soil_mult = SOIL_MULT.get(soil_type.lower(), 1.0)
        base = 6.0 * kc * soil_mult
        if temp > 35:
            base *= 1.1
        elif temp < 15:
            base *= 0.9
        if moisture > 60:
            base *= 0.8
        elif moisture < 20:
            base *= 1.2
        return max(0.0, base)

    def _fert_from_rules(
        self,
        pcfg: Dict[str, Union[float, str]],
        ph: float,
        n_ppm: Optional[float],
        p_ppm: Optional[float],
        k_ppm: Optional[float],
        area_m2: float
    ) -> Tuple[float, float, float, List[str]]:
        notes: List[str] = []
        n_target = self.targets_ppm["N"]
        p_target = self.targets_ppm["P"]
        k_target = self.targets_ppm["K"]
        n_g = max(0.0, (n_target - (n_ppm or 0)) * area_m2 * 0.1)
        p_g = max(0.0, (p_target - (p_ppm or 0)) * area_m2 * 0.1)
        k_g = max(0.0, (k_target - (k_ppm or 0)) * area_m2 * 0.1)
        if ph < float(pcfg.get("ph_min", 5.5)):
            notes.append(f"Soil pH ({ph:.1f}) is below optimal for {pcfg['name']}. Consider liming.")
        elif ph > float(pcfg.get("ph_max", 8.5)):
            notes.append(f"Soil pH ({ph:.1f}) is above optimal for {pcfg['name']}. Consider acidifying amendments.")
        return n_g, p_g, k_g, notes

    def recommend(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        plant: str = str((reading.get("plant") or "generic")).lower()
        soil_type: str = str(reading.get("soil_type", "loam"))
        area_m2: float = float(reading.get("area_m2", self.defaults["area_m2"]))
        ph: float = float(reading.get("ph", 6.5))
        moisture: float = float(reading.get("moisture_pct", self.defaults["moisture_pct"]))
        temp: float = float(reading.get("temperature_c", self.defaults["temperature_c"]))
        ec: float = float(reading.get("ec_dS_m", self.defaults["ec_dS_m"]))
        n_ppm: Optional[float] = reading.get("n_ppm")
        p_ppm: Optional[float] = reading.get("p_ppm")
        k_ppm: Optional[float] = reading.get("k_ppm")

        # Clamp inputs and add notes if corrections applied
        notes: List[str] = []
        orig = {"moisture": moisture, "temp": temp, "ph": ph, "ec": ec}
        moisture = max(0.0, min(100.0, moisture))
        if orig["moisture"] != moisture:
            notes.append(f"Adjusted moisture to {moisture:.1f}% (input out of range)")
        temp = max(-10.0, min(60.0, temp))
        if orig["temp"] != temp:
            notes.append(f"Adjusted temperature to {temp:.1f}°C (input out of range)")
        ph = max(3.5, min(9.5, ph))
        if orig["ph"] != ph:
            notes.append(f"Adjusted pH to {ph:.1f} (input out of range)")
        ec = max(0.0, min(10.0, ec))
        if orig["ec"] != ec:
            notes.append(f"Adjusted EC to {ec:.2f} dS/m (input out of range)")

        # Plant config
        pcfg: Dict[str, Union[float, str]] = self._plant_cfg(plant)
        pcfg["name"] = plant

        # Baseline water
        water_lpm2: float = self._baseline_water_lpm2(pcfg, soil_type, moisture, temp)

        # ML water blend
        soil_ix: int = {"sand": 0, "loam": 1, "clay": 2}.get(soil_type.strip().lower(), 1)
        if self.water_model is not None:
            Xw = np.array([[moisture, temp, ec, ph, soil_ix, float(pcfg["kc"])]] )  # type: ignore
            # Support TF and sklearn models
            try:
                adj_pred = self.water_model.predict(Xw, verbose=0)  # type: ignore
            except TypeError:
                adj_pred = self.water_model.predict(Xw)  # type: ignore
            adj: float = float(adj_pred[0]) if np.ndim(adj_pred) == 1 else float(adj_pred[0][0])
            water_lpm2 = max(0.0, 0.6 * water_lpm2 + 0.4 * adj)

        # Fert from rules (+ ML blend)
        n_g, p_g, k_g, fert_notes = self._fert_from_rules(pcfg, ph, n_ppm, p_ppm, k_ppm, area_m2)
        notes.extend(fert_notes)
        if self.fert_model is not None:
            Xf = np.array([[moisture, temp, ec, ph, soil_ix, float(pcfg["kc"])]] )  # type: ignore
            try:
                pred = self.fert_model.predict(Xf, verbose=0)  # type: ignore
            except TypeError:
                pred = self.fert_model.predict(Xf)  # type: ignore
            # n_adj, p_adj, k_adj = pred[0] if np.ndim(pred) else (0.0, 0.0, 0.0)  # Unused variables
            # Optionally blend ML output with rule-based (not currently used)

        # Totals and savings
        water_total: float = water_lpm2 * area_m2
        naive: float = 8.0 * area_m2
        savings_liters: float = max(0.0, naive - water_total)
        cost_saving: float = savings_liters / 1000.0 * self.rs_per_1000l
        co2e: float = (savings_liters / 1000.0) * self.kwh_per_1000l * self.grid_kgco2_per_kwh

        # Actionable helpers
        water_per_m2: float = water_total / area_m2 if area_m2 > 0 else 0.0
        buckets_15l: float = water_total / 15.0
        irrigation_cycles: int = 2 if (water_per_m2 > 6.0 or soil_type in ("sand", "clay")) else 1
        flow_lpm: float = self.pump_flow_lpm
        run_minutes: float = water_total / max(1e-6, flow_lpm)

        # Fertilizer equivalents
        P_to_P2O5: float = 1.0 / 0.436
        K_to_K2O: float = 1.0 / 0.8301
        UREA_N: float = 0.46
        DAP_P2O5: float = 0.46
        DAP_N: float = 0.18
        MOP_K2O: float = 0.60

        p2o5_needed: float = (p_g * P_to_P2O5)
        dap_g: float = p2o5_needed / DAP_P2O5 if p2o5_needed > 0 else 0.0
        n_from_dap: float = dap_g * DAP_N
        urea_g: float = max(0.0, (n_g - n_from_dap)) / UREA_N if (n_g - n_from_dap) > 0 else 0.0
        k2o_needed: float = (k_g * K_to_K2O)
        mop_g: float = k2o_needed / MOP_K2O if k2o_needed > 0 else 0.0

        fert_eq: Dict[str, float] = {
            "urea_g": round(urea_g, 1),
            "dap_g": round(dap_g, 1),
            "mop_g": round(mop_g, 1),
            "n_from_dap_g": round(n_from_dap, 1),
        }

        # Moisture guidance
        if "moisture_optimal" in pcfg:
            try:
                moisture_max = float(pcfg["moisture_max"])
                moisture_optimal = float(pcfg["moisture_optimal"])
                moisture_min = float(pcfg["moisture_min"])
            except Exception:
                moisture_max = 80.0
                moisture_optimal = 60.0
                moisture_min = 20.0
            if moisture >= moisture_max:
                notes.append(f"Soil moisture ({moisture:.1f}%) above maximum threshold for {plant}. Risk of waterlogging.")
            elif moisture >= moisture_optimal:
                notes.append(f"Soil moisture ({moisture:.1f}%) adequate for {plant}. Consider skipping irrigation.")
            elif moisture <= moisture_min:
                notes.append(f"Soil moisture ({moisture:.1f}%) below minimum threshold for {plant}. Immediate irrigation needed.")
            else:
                dev_from_opt = abs(moisture - moisture_optimal)
                if dev_from_opt > 10:
                    notes.append(f"Soil moisture ({moisture:.1f}%) sub-optimal for {plant}. Target {moisture_optimal}%.")
                else:
                    notes.append(f"Soil moisture ({moisture:.1f}%) acceptable for {plant}.")
            if "season" in pcfg:
                notes.append(f"Note: {plant} is typically a {pcfg['season']} season crop.")
            if "preferred_soil" in pcfg and soil_type.lower() != str(pcfg["preferred_soil"]).lower():
                notes.append(f"Note: {plant} prefers {pcfg['preferred_soil']} soil. Current soil type may affect growth.")
        else:
            if moisture >= 55:
                notes.append("Soil sufficiently moist; consider skipping irrigation today.")
            elif moisture <= 20:
                notes.append("Soil very dry; prioritize irrigation.")
            else:
                notes.append("Moderate moisture; light irrigation advised if no rain expected.")

        out: Dict[str, Any] = {
            "water_liters": round(water_total, 1),
            "fert_n_g": round(n_g, 1),
            "fert_p_g": round(p_g, 1),
            "fert_k_g": round(k_g, 1),
            "notes": notes,
            "expected_savings_liters": round(savings_liters, 1),
            "expected_cost_saving_rs": round(cost_saving, 2),
            "expected_co2e_kg": round(co2e, 2),
            "water_per_m2_l": round(water_per_m2, 1),
            "water_buckets_15l": round(buckets_15l, 1),
            "irrigation_cycles": irrigation_cycles,
            "suggested_runtime_min": round(run_minutes, 1),
            "assumed_flow_lpm": round(flow_lpm, 1),
            "fertilizer_equivalents": fert_eq,
            "best_time": "Early morning or late evening",
        }
        if "moisture_optimal" in pcfg:
            out["target_moisture_pct"] = float(pcfg["moisture_optimal"])
        return out
