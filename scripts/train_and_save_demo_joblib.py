"""Train a small demo sklearn classifier from the datasets/raw/crop_disease_dataset.csv
and write the resulting model to agrisense_app/backend/user_disease_model.joblib.

This is intended to produce a user-supplied model artifact to exercise the
`scripts/validate_and_install_model.py` installer in-place.
"""

from pathlib import Path
import json

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib


DATA_CSV = Path("datasets/raw/crop_disease_dataset.csv")
OUT_MODEL = Path("agrisense_app/backend/user_disease_model.joblib")


def canonical_label(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def main():
    if not DATA_CSV.exists():
        print("Dataset not found:", DATA_CSV)
        return

    df = pd.read_csv(DATA_CSV)
    # pick a few numeric features commonly present in the CSV
    features = [
        "temperature_c",
        "humidity_pct",
        "leaf_wetness_hours",
        "ndvi",
        "lesion_count_per_leaf",
        "severity_percent",
    ]
    # drop rows missing target or features
    df = df.dropna(subset=["disease_label"] + features)

    X = df[features].astype(float)
    y_raw = df["disease_label"].astype(str).apply(canonical_label)

    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    # Train a small RandomForest
    clf = RandomForestClassifier(n_estimators=60, random_state=42)
    clf.fit(X, y)

    # attach classes_ as readable strings (keep as numpy ndarray to match sklearn types)
    clf.classes_ = le.classes_.copy()

    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, OUT_MODEL)
    print("Wrote demo joblib model to", OUT_MODEL)
    print("Classes:", list(clf.classes_))


if __name__ == "__main__":
    main()
