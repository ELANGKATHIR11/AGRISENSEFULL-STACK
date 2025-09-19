import os
import shutil
import json
import argparse
from pathlib import Path

BACKEND_DIR = Path("agrisense_app/backend")
META_PATH = BACKEND_DIR / "model_meta.json"


def ensure_meta():
    if not META_PATH.exists():
        META_PATH.write_text(
            json.dumps({"preferred_order": [], "models": {}}, indent=2)
        )


def install_joblib(src: Path, dst_name: str, labels=None):
    from joblib import load, dump

    m = load(src)
    # ensure classes_ exist and are strings
    if hasattr(m, "classes_"):
        classes = list(getattr(m, "classes_"))
        if any(not isinstance(c, str) for c in classes):
            if labels is not None:
                classes = labels
            else:
                classes = [str(x) for x in classes]
            try:
                m.classes_ = classes
            except Exception:
                print(
                    "Warning: unable to set classes_ on model object; model will be saved but classes_ may remain numeric."
                )
    else:
        if labels is not None:
            try:
                m.classes_ = labels
            except Exception:
                print(
                    "Warning: unable to set classes_ on model object; no classes_ present"
                )

    dst = BACKEND_DIR / dst_name
    dump(m, dst)
    print(f"Installed joblib model to {dst}")
    return dst


def install_keras(src: Path, dst_name: str):
    from tensorflow import keras

    dst = BACKEND_DIR / dst_name
    # prefer using TF saving utilities to ensure compatibility
    model = keras.models.load_model(str(src))
    model.save(str(dst))
    print(f"Installed Keras model to {dst}")
    return dst


def update_meta(filename: str, name: str, mtype: str, labels=None, description=None):
    ensure_meta()
    meta = json.loads(META_PATH.read_text())
    if filename not in meta.get("preferred_order", []):
        meta.setdefault("preferred_order", []).insert(0, filename)
    meta.setdefault("models", {})[filename] = {
        "name": name,
        "type": mtype,
        "description": description or "",
        "labels": labels or [],
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"Updated model_meta.json with {filename}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src", help="Path to the model file to install (.joblib or .keras)")
    p.add_argument("--name", help="Friendly name for the model", default="user-model")
    p.add_argument("--labels", help="Comma-separated labels for classes (optional)")
    p.add_argument(
        "--description", help="Short description", default="User provided model"
    )
    args = p.parse_args()

    src = Path(args.src)
    if not src.exists():
        print("Source model not found:", src)
        return

    labels = None
    if args.labels:
        labels = [l.strip() for l in args.labels.split(",") if l.strip()]

    if src.suffix == ".joblib":
        dst = install_joblib(src, "disease_model.joblib", labels=labels)
        update_meta(
            dst.name, args.name, "joblib", labels=labels, description=args.description
        )
    elif src.suffix in (".keras", ".h5"):
        dst = install_keras(src, "disease_tf.keras")
        update_meta(
            dst.name, args.name, "keras", labels=labels, description=args.description
        )
    else:
        print("Unsupported model extension. Provide .joblib or .keras/.h5 model file.")


if __name__ == "__main__":
    main()
