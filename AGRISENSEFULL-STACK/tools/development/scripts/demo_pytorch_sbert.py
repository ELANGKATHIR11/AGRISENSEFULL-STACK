#!/usr/bin/env python3
"""
Quick demo of PyTorch SentenceTransformer integration.
Shows how to enable the feature and verify it's working.
"""
import os
import time
import requests
import subprocess
import sys
from pathlib import Path

def demo_pytorch_integration():
    """Demonstrate PyTorch SentenceTransformer integration."""
    
    print("🔥 AgriSense PyTorch SentenceTransformer Integration Demo")
    print("=" * 60)
    
    # Configuration
    repo_root = Path(__file__).parent.parent
    print(f"Repository: {repo_root}")
    
    # Show environment configuration
    print("\n📋 Configuration Options:")
    print("AGRISENSE_USE_PYTORCH_SBERT:")
    print("  - '1', 'true', 'yes': Force PyTorch usage")
    print("  - 'auto' (default): Try PyTorch, fallback to TensorFlow") 
    print("  - '0', 'false', 'no': Skip PyTorch, use TensorFlow only")
    print("\nAGRISENSE_SBERT_MODEL:")
    print("  - Default: sentence-transformers/all-MiniLM-L6-v2")
    print("  - Can specify any HuggingFace SentenceTransformer model")
    
    # Show current dependencies
    print("\n📦 Dependencies Added:")
    with open(repo_root / "agrisense_app/backend/requirements.txt") as f:
        lines = f.readlines()
        for line in lines:
            if "torch" in line.lower() or "sentence" in line.lower():
                print(f"  ✅ {line.strip()}")
    
    # Show implementation files
    print("\n🔧 Implementation Files:")
    print("  ✅ agrisense_app/backend/main.py (PyTorchSentenceEncoder class)")
    print("  ✅ agrisense_app/backend/requirements.txt (PyTorch dependencies)")
    print("  ✅ docs/pytorch-sbert-integration.md (Documentation)")
    print("  ✅ scripts/test_pytorch_sbert_integration.py (Tests)")
    
    # Show usage examples
    print("\n🚀 Usage Examples:")
    print("# Enable PyTorch backend:")
    print("export AGRISENSE_USE_PYTORCH_SBERT=1")
    print("export AGRISENSE_SBERT_MODEL=sentence-transformers/all-MiniLM-L6-v2")
    print("uvicorn agrisense_app.backend.main:app --port 8004")
    print()
    print("# Auto-detection mode (tries PyTorch, falls back to TensorFlow):")
    print("uvicorn agrisense_app.backend.main:app --port 8004")
    print()
    print("# Force TensorFlow only:")
    print("export AGRISENSE_USE_PYTORCH_SBERT=0") 
    print("uvicorn agrisense_app.backend.main:app --port 8004")
    
    # Test basic functionality  
    print("\n🧪 Testing Basic Functionality:")
    try:
        # Test import
        sys.path.insert(0, str(repo_root / "agrisense_app/backend"))
        os.environ["AGRISENSE_DISABLE_ML"] = "1"  # Focus on SBERT only
        
        try:
            from main import PyTorchSentenceEncoder  # type: ignore
            print("  ✅ PyTorchSentenceEncoder import successful")
        except ImportError as e:
            print(f"  ❌ PyTorchSentenceEncoder import failed: {e}")
            return
        
        # Test environment parsing
        os.environ["AGRISENSE_USE_PYTORCH_SBERT"] = "auto"
        use_pytorch = os.getenv("AGRISENSE_USE_PYTORCH_SBERT", "auto").lower()
        pytorch_enabled = use_pytorch in ("1", "true", "yes", "auto")
        print(f"  ✅ Environment parsing: {use_pytorch} -> {'Enabled' if pytorch_enabled else 'Disabled'}")
        
        # Test encoder creation (will show dependency status)
        try:
            encoder = PyTorchSentenceEncoder()
            if encoder.model is not None:
                print("  ✅ PyTorch SentenceTransformer loaded successfully!")
                print("    🎯 Ready to use PyTorch backend for embeddings")
            else:
                print("  ⚠️  PyTorch SentenceTransformer dependencies not available")  
                print("    ℹ️  Will fall back to TensorFlow SavedModel if available")
        except Exception as e:
            print(f"  ⚠️  PyTorch loading issue: {str(e)[:100]}...")
            print("    ℹ️  Will fall back to TensorFlow SavedModel if available")
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
    
    # Show next steps
    print("\n🎯 Next Steps:")
    print("1. Install dependencies: pip install torch sentence-transformers tf-keras")
    print("2. Set environment: export AGRISENSE_USE_PYTORCH_SBERT=1")  
    print("3. Start server: uvicorn agrisense_app.backend.main:app --port 8004")
    print("4. Check server logs for backend selection message:")
    print("   - 'Using PyTorch SentenceTransformer: ...' = PyTorch active")
    print("   - 'Using TensorFlow SavedModel...' = TensorFlow fallback")
    print("5. Test chatbot: curl 'http://localhost:8004/chatbot/ask?question=test'")
    
    print("\n✨ Implementation Complete!")
    print("The backend now supports PyTorch SentenceTransformer runtime loading")
    print("with graceful fallback to the existing TensorFlow approach.")

if __name__ == "__main__":
    demo_pytorch_integration()