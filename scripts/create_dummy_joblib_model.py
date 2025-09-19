import numpy as np
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

# The disease_detection joblib path expects a feature vector computed from a 64x64 RGB image
# with 16-bin histograms per channel (3*16=48) plus 3 means and 3 stds = 54 features.
FEATURE_DIM = 54


def make_dummy_dataset(n=200):
    X = np.random.rand(n, FEATURE_DIM).astype(np.float32)
    # 3 class labels: healthy, late_blight, powdery_mildew (use string labels so classes_ is readable)
    labels = ["healthy", "late_blight", "powdery_mildew"]
    y = np.random.choice(labels, size=(n,))
    return X, y


def main():
    X, y = make_dummy_dataset(500)
    clf = RandomForestClassifier(n_estimators=20, random_state=42)
    clf.fit(X, y)
    dump(clf, "agrisense_app/backend/disease_model.joblib")
    print("Wrote agrisense_app/backend/disease_model.joblib")


if __name__ == "__main__":
    main()
