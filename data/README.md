# data/

This folder is the recommended home for dataset files and small curated CSVs used by scripts and tests.

Recommended policy

- Move CSV files from the repo root into this folder using `git mv` so history is preserved.
- Keep only small, curated examples in Git. Large raw datasets should be stored externally (S3, Google Cloud, or a release asset) and referenced here with a small pointer file.
- Add a small index like `MANIFEST.md` listing dataset sources and any preprocessing steps.

Example commands (preview first):

# mkdir data && git mv sikkim_crop_dataset.csv data/

If you follow the repo reorganization, update any script that constructs file paths (many scripts look for `repo_root / "data_core.csv"`). Prefer using `Path(__file__).resolve().parents[1] / 'data'` if you need a robust relative path.
