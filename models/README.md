# models/

This folder should contain pointers, small example model files, or subfolders that document where large model artifacts live.

Policies

- Prefer Git LFS or external storage for large Keras/TensorFlow/PyTorch model files.
- Keep a `versions/` subfolder or `MANIFEST.md` describing model names, expected shapes, and how to regenerate them with the training scripts in `agrisense_app/backend/`.

Example:

```text
agrisense_app/backend/best_crop_tf.keras  # can be moved to models/best_crop_tf.keras if small
```

Recommendation:

- Keep runtime model artifacts alongside the backend under `agrisense_app/backend/models/` where the loading code expects them.
- If you want to track model files in the top-level `models/` folder, prefer small artifacts only and use Git LFS for anything larger than a few MB.
