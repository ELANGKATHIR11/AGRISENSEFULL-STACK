"""Train seed ML models on synthetic, agronomy-like distributions."""

import numpy as np
import pandas as pd
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from joblib import dump

HERE = os.path.dirname(__file__)

rng = np.random.default_rng(42)
N = 8000

soil_map = {"sand": 0, "loam": 1, "clay": 2}
plants = {
    "rice": (1.15, 1.2),
    "wheat": (1.0, 1.0),
    "maize": (1.05, 1.1),
    "tomato": (1.05, 1.1),
    "cotton": (1.15, 1.2),
    "chilli": (1.05, 1.0),
    "groundnut": (0.95, 0.9),
    "generic": (1.0, 1.0),
}


def sample_row():
    plant = rng.choice(list(plants.keys()))
    kc, wf = plants[plant]
    soil = rng.choice(list(soil_map.keys()))
    soil_ix = soil_map[soil]
    moisture = rng.uniform(5, 65)  # %
    temp = rng.uniform(18, 40)  # C
    ph = rng.uniform(5.0, 7.8)
    ec = rng.uniform(0.2, 2.5)
    n_ppm = rng.uniform(5, 60)
    p_ppm = rng.uniform(3, 35)
    k_ppm = rng.uniform(50, 250)

    # Latent rule for water L/m2: more when dry/hot; scaled by kc & soil
    base = 5.0 * kc * wf * (1 + max(0, temp - 25) * 0.03) * max(0, (55 - moisture) / 55)
    soil_mult = [1.1, 1.0, 0.9][soil_ix]
    water_lpm2 = base * soil_mult + rng.normal(0, 0.3)

    # Fert grams per m2 (weekly equivalent) from ppm deficits
    def demand(ppm, target):
        return max(0, target - ppm) * 0.02

    n_g = demand(n_ppm, 40) + rng.normal(0, 1.0)
    p_g = demand(p_ppm, 20) + rng.normal(0, 0.5)
    k_g = demand(k_ppm, 150) + rng.normal(0, 1.5)

    return [moisture, temp, ec, ph, soil_ix, kc, water_lpm2, n_g, p_g, k_g]


rows = [sample_row() for _ in range(N)]
df = pd.DataFrame(rows, columns=["moisture", "temp", "ec", "ph", "soil_ix", "kc", "water_lpm2", "n_g", "p_g", "k_g"])

X = df[["moisture", "temp", "ec", "ph", "soil_ix", "kc"]].values
y_water = df["water_lpm2"].values.astype(np.float64)
y_fert = df[["n_g", "p_g", "k_g"]].values.astype(np.float64)

water_model = RandomForestRegressor(n_estimators=120, random_state=0)
water_model.fit(X, y_water)

fert_model = MultiOutputRegressor(RandomForestRegressor(n_estimators=140, random_state=0))
fert_model.fit(X, y_fert)

dump(water_model, os.path.join(HERE, "water_model.joblib"))
dump(fert_model, os.path.join(HERE, "fert_model.joblib"))

print("Saved water_model.joblib and fert_model.joblib in", HERE)
