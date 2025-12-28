import os
import sys
import json
import argparse
from typing import List, cast
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ML models and regenerate labels")
    parser.add_argument("--csv", dest="csv_override", help="Path to CSV dataset to use for training and labels", default=None)
    args = parser.parse_args()
    # Resolve repo structure
    REPO = os.path.dirname(os.path.dirname(__file__))
    BACKEND = os.path.join(REPO, 'backend')

    # Make backend importable
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)

    # Paths
    # Prefer Sikkim dataset if present, else India dataset
    sikkim_csv = os.path.join(REPO, 'sikkim_crop_dataset.csv')
    csv_path = os.path.join(BACKEND, 'india_crop_dataset.csv')
    if os.path.exists(sikkim_csv):
        csv_path = sikkim_csv
    if args.csv_override:
        # Accept absolute or relative paths; resolve relative to workspace root
        csv_candidate = args.csv_override
        if not os.path.isabs(csv_candidate):
            csv_candidate = os.path.abspath(os.path.join(REPO, csv_candidate))
        csv_path = csv_candidate
    labels_path = os.path.join(BACKEND, 'crop_labels.json')

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    # Regenerate labels metadata for frontend/backend harmony
    df: pd.DataFrame = cast(pd.DataFrame, pd.read_csv(csv_path, encoding='utf-8-sig'))  # type: ignore[reportUnknownMemberType]
    # Use set(...) instead of Series.unique() to avoid partially-unknown numpy types in type checkers
    crops: List[str] = sorted([str(x) for x in set(df['Crop'].dropna().astype(str).tolist())])
    soils: List[str] = sorted([str(x) for x in set(df['Soil_Type'].dropna().astype(str).tolist())])
    with open(labels_path, 'w', encoding='utf-8') as f:
        json.dump({"soil_types": soils, "crops": crops}, f, ensure_ascii=False, indent=2)
    print(f"Wrote crop_labels.json with {len(crops)} crops and {len(soils)} soil types -> {labels_path}")

    # Train and persist scikit-learn models
    from smart_farming_ml import SmartFarmingRecommendationSystem  # type: ignore
    # Instantiate to trigger training and artifact generation; pass chosen dataset
    SmartFarmingRecommendationSystem(dataset_path=csv_path)
    # prepare_models() is called in __init__; files saved in backend directory
    print("Training complete. Models saved:")
    for name in [
        'yield_prediction_model.joblib',
        'crop_classification_model.joblib',
        'soil_encoder.joblib',
        'crop_encoder.joblib',
    ]:
        path = os.path.join(BACKEND, name)
        print(f" - {name}: {'OK' if os.path.exists(path) else 'MISSING'} -> {path}")


if __name__ == '__main__':
    main()
