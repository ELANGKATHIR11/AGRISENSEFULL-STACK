# models/

This folder should contain pointers, small example model files, or subfolders that document where large model artifacts live.

Policies

- Prefer Git LFS or external storage for large Keras/TensorFlow/PyTorch model files.
- Keep a `versions/` subfolder or `MANIFEST.md` describing model names, expected shapes, and how to regenerate them with the training scripts in `agrisense_app/backend/`.

Example:
- `agrisense_app/backend/best_crop_tf.keras` can be moved to `models/best_crop_tf.keras` if it's small; otherwise leave it in place and add an entry here documenting its location.
