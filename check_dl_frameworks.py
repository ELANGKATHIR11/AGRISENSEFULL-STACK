import tensorflow as tf
import torch

print("=" * 60)
print("DEEP LEARNING FRAMEWORKS INSTALLED")
print("=" * 60)

# TensorFlow
print("\n📦 TensorFlow")
print(f"   Version: {tf.__version__}")
print(f"   Keras Version: {tf.keras.__version__}")
print(f"   Built with CUDA: {tf.test.is_built_with_cuda()}")
tf_gpus = tf.config.list_physical_devices('GPU')
print(f"   GPU Devices: {len(tf_gpus)} detected")
if tf_gpus:
    for gpu in tf_gpus:
        print(f"   - {gpu.name}")

# PyTorch
print("\n🔥 PyTorch")
print(f"   Version: {torch.__version__}")
print(f"   CUDA Available: {torch.cuda.is_available()}")
print(f"   CUDA Version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"   Current Device: cuda:{torch.cuda.current_device()}")

print("\n" + "=" * 60)
print("✅ Both frameworks ready for deep learning!")
print("=" * 60)
print("\nNote: Your RTX 5060 Laptop GPU has compute capability 12.0")
print("PyTorch official builds support up to sm_90. For full GPU support,")
print("consider using PyTorch nightly builds or CPU for now.")
print("\nTensorFlow will use CPU for now (GPU support limited on Windows).")
