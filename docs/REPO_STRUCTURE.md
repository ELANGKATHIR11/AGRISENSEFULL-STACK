# Repository structure and safe reorganization plan

This document explains the current layout of the repository, proposes a minimal, safe reorganization to make the project easier to navigate, and provides a non-destructive plan you can run locally. No files are deleted by the plan — it only suggests moves and creates a few helper files.

Why this document

- The repository mixes application code, datasets, artifacts, docs, and mobile/web clients at the repo root. That makes it harder to find the working backend or to run tools like tests and CI.
- A small reorg will make development and CI easier while preserving history and keeping large binaries out of Git.

High-level current layout (important paths)

- `agrisense_app/` — primary Python application (backend, frontend, models, and scripts)
- `scripts/` — utility scripts for training, evaluation, and experiments
- `docs/` — project docs (blueprints, integration notes)
- `mobile/` — mobile client and related assets
- `AGRISENSE_IoT/`, `agrisense_pi_edge_minimal/` — edge and IoT code and firmware
- CSVs and datasets at repo root (e.g. `sikkim_crop_dataset.csv`, `data_core.csv`, `merged_chatbot_training_dataset.csv`) — move these to a `data/` folder and exclude large raw data from Git in favor of a data/README and pointers to external storage
- Model artifacts (e.g. `best_crop_tf.keras`, `best_yield_tf.keras`, `best_fert_model.keras`) — keep them under `agrisense_app/backend/models/` and use Git LFS or external storage for large files

Concrete candidates found in this repository (non-exhaustive)

CSV files at repo root that are safe to move into `data/`:

- `sikkim_crop_dataset.csv`
- `data_core.csv`
- `merged_chatbot_training_dataset.csv`
- `weather_cache.csv`
- `Farming_FAQ_Assistant_Dataset.csv`
- `Farming_FAQ_Assistant_Dataset (2).csv`

Model and artifact files found under `agrisense_app/backend/` (consider consolidating into `agrisense_app/backend/models/`):

- `best_fert_model.keras`
- `best_water_model.keras`
- `chatbot_question_encoder.keras`
- `fert_model.keras`
- `water_model.keras`
- `crop_tf.keras`
- `yield_tf.keras`

Notes:

- Many scripts reference the CSVs by name (e.g. `repo_root / "data_core.csv"`). If you move the CSVs to `data/`, update those script paths or add a small compatibility shim at repo root that forwards to `data/` (a tiny Python script that sets environment variables or symlinks).
- Use `git mv` so history for moved files is preserved. If files are large, consider adding them to Git LFS first and then moving.

Goals for the reorganization

1. Make it obvious where to find the backend, frontend, ML artifacts, datasets, and infra code.
2. Keep all changes non-destructive and reversible (use git mv so history is preserved).
3. Add docs and helper scripts that automate the proposed moves and checks.
4. Keep CI and tasks working by not changing import paths; the plan limits renames that break imports.

Recommended target layout (minimal, safe)

- repo-root/
  - agrisense_app/ (unchanged)
  - backend/ -> symlink or lightweight pointer to `agrisense_app/backend` (optional)
  - frontend/ -> symlink to `agrisense_app/frontend` (optional)
  - data/ (new) — move CSV/dataset files here and add `data/README.md` explaining origin and any DO NOT COMMIT rules
  - models/ (new) — move smaller, versioned model artifacts or create `models/README.md` pointing to `agrisense_app/backend/models`
  - scripts/ (unchanged)
  - docs/ (unchanged)
  - mobile/ (unchanged)
  - infra/ (unchanged)

Why not move everything at once

- Imports, CI, and relative paths inside scripts assume `agrisense_app` location. Large refactors risk breaking things. This plan prioritizes clarity and documentation first, then small, reversible moves.

Non-destructive step-by-step plan (commands are suggestions — review before running)

1. Create new folders for `data/` and `models/` at repo root.

   git checkout -b reorg/docs-and-skel
   mkdir data models

2. Move dataset CSVs into `data/` using git mv (preserves history):

   git mv "sikkim_crop_dataset.csv" data/
   git mv "data_core.csv" data/
   git mv "merged_chatbot_training_dataset.csv" data/
   git mv "weather_cache.csv" data/
   git mv "Farming_FAQ_Assistant_Dataset.csv" data/

   # Keep a high-level index file
   echo "# data/ — dataset index" > data/README.md
   git add data/README.md && git commit -m "docs(data): move csv datasets to data/ and add index"

3. Move only small model artifacts or create pointers to big ones. Example:

   mkdir -p agrisense_app/backend/models
   git mv best_crop_tf.keras agrisense_app/backend/models/ || echo "skip large file"

   If files are large, consider using Git LFS or leaving them in place and document where they live

4. Add top-level README updates and a CONTRIBUTING.md (this repo already has good READMEs; we add a short contributing file).

5. Optionally create `backend/` and `frontend/` lightweight scripts or symlinks that point to `agrisense_app` to make it obvious for new contributors; avoid breaking imports.

Testing and validation

- After each git mv and commit, run the backend start (or run tests if present):

  python -m uvicorn agrisense_app.backend.main:app --reload --port 8004

- Run `python scripts/test_chatbot_inprocess.py` (or the equivalent test harness in `scripts/`) to verify the chatbot still loads artifacts.

Files added in this change

- `docs/REPO_STRUCTURE.md` (this file)
- `CONTRIBUTING.md` (small guidelines)
- `.editorconfig` (basic indentation rules)
- `scripts/propose_reorg.ps1` (PowerShell script that prints suggested git mv commands — safe, no destructive ops)

Rollout strategy

- Start with the docs and small moves.
- Open a PR with the moves and request CI checks and smoke tests.

If you'd like, I can now run the small edits (create the new files above) and add the PowerShell helper that prints exact git mv commands for your current repo contents. This will not move any files yet — it only creates helper docs and a script you can review and run locally.
