# Model artifacts and how to install them

This project accepts two primary model artifact types for disease inference:

- sklearn/joblib (.joblib)
- TensorFlow/Keras saved model (.keras or .h5; TF SavedModel directory also accepted)

## Expectations for artifacts

- For sklearn/joblib models:

  - The model should have a `classes_` attribute containing class labels as strings. If not present, pass `--labels "a,b,c"` to the installer.
  - The model file is typically a single `.joblib` file created with `joblib.dump(model, path)`.

- For TensorFlow/Keras models:
  - Provide either a single `.keras` file or a TF SavedModel directory. The installer will use `tf.keras.models.load_model()` and re-save to `agrisense_app/backend/`.

## How to install a model (local file)

Run the installer script from the repository root (examples for Windows PowerShell):

Install a joblib model (with explicit labels):

```pwsh
.venv\Scripts\python.exe scripts\validate_and_install_model.py C:\path\to\your_model.joblib --name "my-model" --labels "healthy,late_blight,powdery_mildew" --description "My trained model"
```

Install a Keras model:

```pwsh
.venv\Scripts\python.exe scripts\validate_and_install_model.py C:\path\to\your_model.keras --name "my-keras-model" --description "Trained Keras model"
```

## What the installer does

- Copies or re-saves the model into `agrisense_app/backend/` (joblib -> `disease_model.joblib`, keras -> `disease_tf.keras`).
- Attempts to ensure sklearn models have `classes_` as strings; you can override via `--labels`.
- Updates `agrisense_app/backend/model_meta.json` with a `models` entry and puts the new filename at the front of `preferred_order`.

## Notes

- If a joblib model was trained with a different scikit-learn version than the runtime, you may see a warning when unpickling (`InconsistentVersionWarning`). It often still loads, but for stability try to match versions or export to ONNX.
- For CI-friendly tests, commit a tiny sample `.joblib` model to the repository and the CI workflow will use it for smoke inference tests.
