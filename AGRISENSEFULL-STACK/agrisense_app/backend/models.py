from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict

# Accept arbitrary plant names and soil labels from UI/dataset
SoilType = str
PlantType = str

class SensorReading(BaseModel):
    zone_id: str = "Z1"
    plant: PlantType = "generic"
    soil_type: SoilType = "loam"
    area_m2: float = 100.0
    ph: float = 6.5
    moisture_pct: float = 35.0  # 0..100
    temperature_c: float = 28.0
    ec_dS_m: float = 1.0
    n_ppm: Optional[float] = None
    p_ppm: Optional[float] = None
    k_ppm: Optional[float] = None
    timestamp: Optional[str] = None  # ISO8601

class Recommendation(BaseModel):
    # Allow extra keys from engine.recommend output without validation errors
    model_config = ConfigDict(extra='allow')

    water_liters: float
    fert_n_g: float
    fert_p_g: float
    fert_k_g: float
    # Hackathon: explicitly include inferred water source ("tank"|"groundwater")
    water_source: Optional[str] = None
    notes: List[str]
    tips: List[str] = Field(default_factory=list)
    expected_savings_liters: float
    expected_cost_saving_rs: float
    expected_co2e_kg: float
    # Common extras from engine output (kept optional for forward-compat)
    water_per_m2_l: Optional[float] = None
    water_buckets_15l: Optional[float] = None
    irrigation_cycles: Optional[int] = None
    suggested_runtime_min: Optional[float] = None
    assumed_flow_lpm: Optional[float] = None
    best_time: Optional[str] = None
    fertilizer_equivalents: Optional[Dict[str, float]] = None
    target_moisture_pct: Optional[float] = None