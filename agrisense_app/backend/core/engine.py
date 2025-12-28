from agrisense_app.backend.et0 import extraterrestrial_radiation_ra, et0_hargreaves  # type: ignore
import os
import yaml
from typing import Dict, Any, Tuple, List, Optional, Union
import numpy as np  # type: ignore
from joblib import load  # type: ignore
try:
    from ..nlp.response_generator import TemplateResponseGenerator  # Added for natural language explanations
except ImportError:  # pragma: no cover - fallback for script entrypoints
    from agrisense_app.backend.nlp.response_generator import TemplateResponseGenerator
from ..ml import predict_reading  # Import ML prediction function

# Removed unused import of et0 as et due to errors and lack of usage.

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
        _disable_ml = str(os.getenv("AGRISENSE_DISABLE_ML", "0")).lower() in ("1", "true", "yes")
        self.ml_enabled = not _disable_ml
        if not _disable_ml:
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
        else:
            # ML disabled; try lightweight joblib artifacts only (if present)
            wm = os.path.join(HERE, "water_model.joblib")
            fm = os.path.join(HERE, "fert_model.joblib")
            try:
                self.water_model = load(wm) if os.path.exists(wm) else None
            except Exception:
                self.water_model = None
            try:
                self.fert_model = load(fm) if os.path.exists(fm) else None
            except Exception:
                self.fert_model = None

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

    def _baseline_water_lpm2(
        self, pcfg: Dict[str, Union[float, str]], soil_type: str, moisture: float, temp: float
    ) -> float:
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
        area_m2: float,
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

    def _detailed_tips(
        self,
        pcfg: Dict[str, Union[float, str]],
        ph: float,
        moisture: float,
        temp: float,
        ec: float,
        n_ppm: Optional[float],
        p_ppm: Optional[float],
        k_ppm: Optional[float],
        soil_type: str,
        area_m2: float,
    ) -> List[str]:
        """Generate concrete, farmer-friendly tips when parameters are out of ideal ranges.
        Tips are action-oriented and specific (what, how much, when).
        """
        tips: List[str] = []
        name = str(pcfg.get("name", "crop"))
        # pH guidance
        ph_min = float(pcfg.get("ph_min", 5.5))
        ph_max = float(pcfg.get("ph_max", 8.5))
        if ph < ph_min:
            # Estimate ag lime (CaCO3) need: rough thumb-rule ~0.5 kg per 10 m2 to raise ~0.2-0.3 pH in light soils
            lime_kg = max(0.0, area_m2 * 0.05)
            tips.append(
                f"pH low ({ph:.1f} < {ph_min:.1f}) for {name}. Apply agricultural lime ~ {lime_kg:.1f} kg over {area_m2:.0f} m2; irrigate lightly and recheck in 2-4 weeks."
            )
        elif ph > ph_max:
            # Use elemental sulfur for alkalinity reduction; very rough guidance 0.02–0.05 kg/m2 depending on soil
            sulfur_kg = max(0.0, area_m2 * 0.03)
            tips.append(
                f"pH high ({ph:.1f} > {ph_max:.1f}) for {name}. Incorporate elemental sulfur ~ {sulfur_kg:.1f} kg over {area_m2:.0f} m2; keep soil moist and recheck pH after 3-6 weeks."
            )

        # Moisture guidance (use crop parameters if present)
        try:
            m_max = float(pcfg.get("moisture_max", 80.0))
            m_opt = float(pcfg.get("moisture_optimal", 60.0))
            m_min = float(pcfg.get("moisture_min", 20.0))
        except Exception:
            m_max, m_opt, m_min = 80.0, 60.0, 20.0
        if moisture < m_min:
            # Water to reach mid of optimal band
            target = max(m_opt - 5.0, m_min + 5.0)
            tips.append(
                f"Soil moisture low ({moisture:.1f}% < {m_min:.0f}%). Irrigate today to reach ~{target:.0f}%: split into 2 cycles to reduce runoff, especially on {soil_type} soils."
            )
        elif moisture > m_max:
            tips.append(
                f"Soil moisture high ({moisture:.1f}% > {m_max:.0f}%). Pause irrigation; improve drainage or use raised beds to avoid root stress."
            )

        # EC guidance (salinity)
        if ec >= 3.0:
            tips.append(
                f"High salinity (EC {ec:.2f} dS/m). Avoid heavy fertilization, flush salts with a deep irrigation in cool hours, and consider gypsum if sodicity suspected."
            )
        elif ec <= 0.2:
            tips.append(
                f"Very low EC ({ec:.2f} dS/m). Nutrient levels may be insufficient - apply balanced fertilizer and mulching to improve retention."
            )

        # Nitrogen / Phosphorus / Potassium guidance against targets
        n_target = self.targets_ppm["N"]
        p_target = self.targets_ppm["P"]
        k_target = self.targets_ppm["K"]
        if n_ppm is not None and n_ppm < n_target:
            deficit = n_target - n_ppm
            # Convert N ppm deficit to urea requirement considering 46% N, 0.1 scaling already used elsewhere
            urea_g = max(0.0, deficit * area_m2 * 0.1) / 0.46
            tips.append(
                f"Nitrogen low (N {n_ppm:.0f} < {n_target}). Apply urea ~ {urea_g:.0f} g split into 2 doses a week apart; irrigate lightly after each application."
            )
        if p_ppm is not None and p_ppm < p_target:
            deficit = p_target - p_ppm
            # Use DAP: 46% P2O5; convert P to P2O5 via factor 1/0.436
            p2o5_needed = max(0.0, deficit * area_m2 * 0.1) / 0.436
            dap_g = p2o5_needed / 0.46
            tips.append(
                f"Phosphorus low (P {p_ppm:.0f} < {p_target}). Apply DAP ~ {dap_g:.0f} g; mix into topsoil, avoid direct contact with roots."
            )
        if k_ppm is not None and k_ppm < k_target:
            deficit = k_target - k_ppm
            # Use MOP: 60% K2O; convert K to K2O via factor 1/0.8301
            k2o_needed = max(0.0, deficit * area_m2 * 0.1) / 0.8301
            mop_g = k2o_needed / 0.60
            tips.append(
                f"Potassium low (K {k_ppm:.0f} < {k_target}). Apply MOP ~ {mop_g:.0f} g; water after application to aid uptake."
            )

        # Temperature hints
        if temp >= 35:
            tips.append(
                "High temperature - prefer early morning/evening irrigation and use mulch to reduce evaporation."
            )
        elif temp <= 12:
            tips.append("Low temperature - avoid overwatering; consider row covers to reduce stress.")

        # Soil type specifics
        st = soil_type.strip().lower()
        if st == "sand":
            tips.append("Sandy soil drains fast—use smaller, more frequent irrigation cycles and add organic matter.")
        elif st == "clay":
            tips.append("Clay soil holds water—ensure good drainage and avoid working soil when wet.")

        return tips

    def _generate_explanation(self, reading: Dict, result: Dict) -> str:
        """
        Generate natural language explanation for the recommendation
        """
        # Create a template-based generator
        generator = TemplateResponseGenerator()

        entities = {
            "crop": reading.get("crop", "your crops"),
            "water_amount": str(result.get("water_liters", "an appropriate amount of")),
            "problem": reading.get("problem", "potential issues"),
        }

        intent_map = {
            "irrigation": "irrigation_help",
            "fertilization": "crop_advice",
            "disease_treatment": "disease_help",
            "weed_management": "disease_help",
        }

        intent = intent_map.get(result.get("recommendation_type", "general"), "general_help")

        return generator.generate_response(intent, entities)

    def recommend(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendation, using ML if enabled
        """
        try:
            if self.ml_enabled:
                return predict_reading(reading)
        except Exception as e:
            print(f"ML prediction failed: {e}")
            
        return self._rule_based_recommend(reading)
        
    def _rule_based_recommend(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure rule-based recommendation (original implementation)
        """
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

        # Optional climate adjustment via ET0 (Hargreaves) if minimal inputs present.
        # Provide latitude and today’s Tmax/Tmin via env or defaults to tune baseline slightly.
        try:
            lat = float(os.getenv("AGRISENSE_LAT", "27.3"))  # Sikkim approx
            # Prefer reading-provided extremes if available
            tmax = float(os.getenv("AGRISENSE_TMAX_C", str(max(temp, float(reading.get("tmax_c", temp))))))
            tmin = float(os.getenv("AGRISENSE_TMIN_C", str(min(temp, float(reading.get("tmin_c", temp - 5))))))
            tmean = (tmax + tmin) / 2.0
            import datetime as _dt

            j = int(
                os.getenv("AGRISENSE_DOY", str((_dt.date.today() - _dt.date(_dt.date.today().year, 1, 1)).days + 1))
            )
            ra = extraterrestrial_radiation_ra(lat, j)
            et0 = et0_hargreaves(tmin, tmax, tmean, ra)
            # Convert ET0 mm/day to an adjustment factor around 1.0 using a mild scaling
            # Typical ET0 3..7 mm/day; scale 0.9..1.2 range
            adj = 1.0 + max(-0.2, min(0.2, (et0 - 5.0) * 0.05))
            water_lpm2 *= adj
        except Exception:
            pass

        # ML water blend
        soil_ix: int = {"sand": 0, "loam": 1, "clay": 2}.get(soil_type.strip().lower(), 1)
        if self.water_model is not None:
            Xw = np.array([[moisture, temp, ec, ph, soil_ix, float(pcfg["kc"])]])  # type: ignore
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
            Xf = np.array([[moisture, temp, ec, ph, soil_ix, float(pcfg["kc"])]])  # type: ignore
            try:
                pred = self.fert_model.predict(Xf, verbose=0)  # type: ignore
            except TypeError:
                # Unused variable - model prediction result
                pass
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

        p2o5_needed: float = p_g * P_to_P2O5
        dap_g: float = p2o5_needed / DAP_P2O5 if p2o5_needed > 0 else 0.0
        n_from_dap: float = dap_g * DAP_N
        urea_g: float = max(0.0, (n_g - n_from_dap)) / UREA_N if (n_g - n_from_dap) > 0 else 0.0
        k2o_needed: float = k_g * K_to_K2O
        mop_g: float = k2o_needed / MOP_K2O if k2o_needed > 0 else 0.0

        fert_eq: Dict[str, float] = {
            "urea_g": round(urea_g, 1),
            "dap_g": round(dap_g, 1),
            "mop_g": round(mop_g, 1),
            "n_from_dap_g": round(n_from_dap, 1),
        }

        # Moisture guidance
        if "moisture_optimal" in pcfg:
            out = {
                "water_liters": round(water_total, 1),
                "fert_n_g": round(n_g, 1),
                "fert_p_g": round(p_g, 1),
                "fert_k_g": round(k_g, 1),
                "notes": notes,
                "tips": self._detailed_tips(
                    pcfg=pcfg,
                    ph=ph,
                    moisture=moisture,
                    temp=temp,
                    ec=ec,
                    n_ppm=n_ppm,
                    p_ppm=p_ppm,
                    k_ppm=k_ppm,
                    soil_type=soil_type,
                    area_m2=area_m2,
                ),
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
            out["target_moisture_pct"] = float(pcfg["moisture_optimal"])

            # Generate natural language explanation
            explanation = self._generate_explanation(reading, out)
            out["explanation"] = explanation

            return out
        else:
            return {
                "water_liters": round(water_total, 1),
                "fert_n_g": round(n_g, 1),
                "fert_p_g": round(p_g, 1),
                "fert_k_g": round(k_g, 1),
                "notes": notes,
                "tips": self._detailed_tips(
                    pcfg=pcfg,
                    ph=ph,
                    moisture=moisture,
                    temp=temp,
                    ec=ec,
                    n_ppm=n_ppm,
                    p_ppm=p_ppm,
                    k_ppm=k_ppm,
                    soil_type=soil_type,
                    area_m2=area_m2,
                ),
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
