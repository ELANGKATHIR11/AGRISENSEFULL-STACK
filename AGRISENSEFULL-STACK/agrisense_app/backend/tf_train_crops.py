"""Train TensorFlow models on india_crop_dataset.csv (45+ crops).

Produces:
- yield_tf.keras: regression model predicting Expected_Yield_tonnes_ha
- crop_tf.keras: multiclass classifier predicting Crop
- crop_labels.json: class index to crop label mapping
"""

import os
import json
from typing import Optional
import numpy as np
import pandas as pd

try:
    from tensorflow import keras  # type: ignore
    from tensorflow.keras import layers  # type: ignore
except ImportError:
    import keras  # type: ignore
    from keras import layers  # type: ignore

HERE = os.path.dirname(__file__)
CSV = os.path.join(HERE, "india_crop_dataset.csv")

FEATURE_COLUMNS = [
    "pH_Optimal",
    "Nitrogen_Optimal_kg_ha",
    "Phosphorus_Optimal_kg_ha",
    "Potassium_Optimal_kg_ha",
    "Temperature_Optimal_C",
    "Water_Requirement_mm",
    "Moisture_Optimal_percent",
    "Humidity_Optimal_percent",
    # Encoded soil type appended later
]


def load_data():
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    # Basic validation
    for col in FEATURE_COLUMNS + ["Soil_Type", "Expected_Yield_tonnes_ha", "Crop"]:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # Encode soil type
    soil_types = sorted(df["Soil_Type"].astype(str).unique())
    soil_to_ix = {s: i for i, s in enumerate(soil_types)}
    df["Soil_Type_Encoded"] = df["Soil_Type"].astype(str).map(soil_to_ix)

    X = df[FEATURE_COLUMNS + ["Soil_Type_Encoded"]].to_numpy(dtype=np.float32)
    y_yield = df["Expected_Yield_tonnes_ha"].to_numpy(dtype=np.float32)

    # Crop labels
    crops = sorted(df["Crop"].astype(str).unique())
    crop_to_ix = {c: i for i, c in enumerate(crops)}
    y_crop = df["Crop"].astype(str).map(crop_to_ix).to_numpy(dtype=np.int32)

    meta = {
        "soil_types": soil_types,
        "crops": crops,
    }
    return X, y_yield, y_crop, meta


def build_mlp(input_dim: int, output_dim: int, final_activation: Optional[str] = None) -> keras.Model:
    inp = keras.Input(shape=(input_dim,), name="features")
    norm = layers.Normalization(name="norm")(inp)
    x = layers.Dense(128, activation="relu")(norm)
    x = layers.Dense(64, activation="relu")(x)
    out = layers.Dense(output_dim, activation=final_activation, name="out")(x)
    return keras.Model(inp, out)


def train():
    X, y_yield, y_crop, meta = load_data()
    n = X.shape[0]
    idx = np.arange(n)
    rng = np.random.default_rng(0)
    rng.shuffle(idx)
    tr = idx[: int(0.8 * n)]
    va = idx[int(0.8 * n):]

    Xtr, Xva = X[tr], X[va]
    yy_tr, yy_va = y_yield[tr], y_yield[va]
    yc_tr, yc_va = y_crop[tr], y_crop[va]

    # Yield regression
    reg = build_mlp(X.shape[1], 1, None)
    reg.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])  # type: ignore
    reg.get_layer("norm").adapt(Xtr)
    reg.fit(Xtr, yy_tr, validation_data=(Xva, yy_va), epochs=60, batch_size=32, verbose=0)  # type: ignore
    reg_path = os.path.join(HERE, "yield_tf.keras")
    reg.save(reg_path)
    print("Saved", reg_path)

    # Crop classifier
    num_classes = int(yc_tr.max()) + 1
    clf = build_mlp(X.shape[1], num_classes, final_activation="softmax")
    clf.compile(
        optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"]
    )  # type: ignore
    clf.get_layer("norm").adapt(Xtr)
    clf.fit(Xtr, yc_tr, validation_data=(Xva, yc_va), epochs=80, batch_size=32, verbose=0)  # type: ignore
    clf_path = os.path.join(HERE, "crop_tf.keras")
    clf.save(clf_path)
    print("Saved", clf_path)

    # Save labels/meta
    with open(os.path.join(HERE, "crop_labels.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("Saved crop_labels.json with labels and soil types")


if __name__ == "__main__":
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    train()
