"""Train TensorFlow models for water and fertilizer predictions using synthetic agronomy-like data.

Outputs:
- water_model.keras (Keras SavedModel, single-output regression)
- fert_model.keras (Keras SavedModel, 3-output regression [N, P, K] grams)
"""

import os
import numpy as np

try:
    from tensorflow import keras  # type: ignore
    from tensorflow.keras import layers  # type: ignore
except ImportError:
    import keras  # type: ignore
    from keras import layers  # type: ignore

HERE = os.path.dirname(__file__)


def generate_synthetic(n: int = 8000, seed: int = 42):
    rng = np.random.default_rng(seed)
    # soil_map = {"sand": 0, "loam": 1, "clay": 2}
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
        soil_ix = rng.integers(0, 3)
        moisture = rng.uniform(5, 65)  # %
        temp = rng.uniform(18, 40)  # C
        ph = rng.uniform(5.0, 7.8)
        ec = rng.uniform(0.2, 2.5)
        n_ppm = rng.uniform(5, 60)
        p_ppm = rng.uniform(3, 35)
        k_ppm = rng.uniform(50, 250)

        # Water target (L/m^2)
        base = 5.0 * kc * wf * (1 + max(0, temp - 25) * 0.03) * max(0, (55 - moisture) / 55)
        soil_mult = [1.1, 1.0, 0.9][soil_ix]
        water_lpm2 = base * soil_mult + rng.normal(0, 0.3)

        # Fert targets (g/m^2 per week) from ppm deficits
        def demand(ppm, target):
            return max(0, target - ppm) * 0.02

        n_g = demand(n_ppm, 40) + rng.normal(0, 1.0)
        p_g = demand(p_ppm, 20) + rng.normal(0, 0.5)
        k_g = demand(k_ppm, 150) + rng.normal(0, 1.5)

        return [moisture, temp, ec, ph, soil_ix, kc, water_lpm2, n_g, p_g, k_g]

    rows = [sample_row() for _ in range(n)]
    data = np.array(rows, dtype=np.float32)
    X = data[:, :6]
    y_water = data[:, 6]
    y_fert = data[:, 7:10]
    return X, y_water, y_fert


def build_regressor(input_dim: int, output_dim: int = 1) -> keras.Model:
    inputs = keras.Input(shape=(input_dim,), name="features")
    x = layers.Normalization(name="norm")(inputs)
    # simple MLP
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dense(64, activation="relu")(x)
    outputs = layers.Dense(output_dim, name="out")(x)
    model = keras.Model(inputs, outputs)
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])  # type: ignore
    return model


def main():
    X, y_water, y_fert = generate_synthetic()

    # Split
    n = X.shape[0]
    idx = np.arange(n)
    np.random.default_rng(0).shuffle(idx)
    tr = idx[: int(0.8 * n)]
    va = idx[int(0.8 * n):]

    Xtr, Xva = X[tr], X[va]
    yw_tr, yw_va = y_water[tr], y_water[va]
    yf_tr, yf_va = y_fert[tr], y_fert[va]

    # Water model
    water_model = build_regressor(X.shape[1], 1)
    # Adapt normalization
    norm_layer = water_model.get_layer("norm")
    norm_layer.adapt(Xtr)
    water_model.fit(Xtr, yw_tr, validation_data=(Xva, yw_va), epochs=20, batch_size=64, verbose=0)  # type: ignore
    water_path = os.path.join(HERE, "water_model.keras")
    water_model.save(water_path)
    print("Saved", water_path)

    # Fert model (3 outputs)
    fert_model = build_regressor(X.shape[1], 3)
    fert_norm = fert_model.get_layer("norm")
    fert_norm.adapt(Xtr)
    fert_model.fit(Xtr, yf_tr, validation_data=(Xva, yf_va), epochs=25, batch_size=64, verbose=0)  # type: ignore
    fert_path = os.path.join(HERE, "fert_model.keras")
    fert_model.save(fert_path)
    print("Saved", fert_path)


if __name__ == "__main__":
    # Reduce TF log noise
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    main()
