"""
Scan for sklearn joblib/pickle model files and re-save them using current joblib to remove
InconsistentVersionWarning and make them compatible with the runtime.

Usage:
  python scripts/repickle_sklearn_models.py --dir ml_models --backup
"""
import argparse
import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("repickle")
logging.basicConfig(level=logging.INFO)

try:
    import joblib
except Exception:
    joblib = None


def find_model_files(root: Path, patterns=("*.joblib", "*.pkl", "*.pickle")):
    for pat in patterns:
        for p in root.rglob(pat):
            yield p


def repickle_file(path: Path, backup=True):
    if joblib is None:
        logger.error("joblib not available in the environment. Activate your venv and try again.")
        return False

    logger.info(f"Processing {path}")
    try:
        # Backup original
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
            logger.info(f"Backed up original to {bak}")

        # Load and resave using joblib
        model = joblib.load(path)
        out_path = path.with_suffix('.resaved.joblib')
        joblib.dump(model, out_path)
        logger.info(f"Re-saved model to {out_path}")

        # Optionally replace original with resaved version
        # shutil.move(str(out_path), str(path))
        return True
    except Exception as e:
        logger.exception(f"Failed to repickle {path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Root directory to search for model files")
    parser.add_argument("--backup", action="store_true", help="Keep backups of original files")
    args = parser.parse_args()

    root = Path(args.dir).resolve()
    if not root.exists():
        logger.error("Specified directory does not exist: %s", root)
        return 1

    success = 0
    total = 0
    for p in find_model_files(root):
        total += 1
        if repickle_file(p, backup=args.backup):
            success += 1

    logger.info(f"Processed {total} files, successfully repickled {success}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
