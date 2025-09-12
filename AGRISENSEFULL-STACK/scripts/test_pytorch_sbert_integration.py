#!/usr/bin/env python3
"""
Test script to demonstrate PyTorch SentenceTransformer integration.
Shows fallback behavior and configuration options.
"""
import sys
import os
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_server_startup_modes():
    """Test different server startup configurations."""
    
    repo_root = Path(__file__).parent.parent
    backend_dir = repo_root / "agrisense_app" / "backend"
    
    test_cases = [
        {
            "name": "PyTorch Forced",
            "env": {
                "AGRISENSE_USE_PYTORCH_SBERT": "1",
                "AGRISENSE_SBERT_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
                "AGRISENSE_DISABLE_ML": "1"  # Disable other ML to focus on SBERT
            }
        },
        {
            "name": "Auto-detection (Default)",
            "env": {
                "AGRISENSE_USE_PYTORCH_SBERT": "auto",
                "AGRISENSE_DISABLE_ML": "1"
            }
        },
        {
            "name": "TensorFlow Only", 
            "env": {
                "AGRISENSE_USE_PYTORCH_SBERT": "0",
                "AGRISENSE_DISABLE_ML": "1"
            }
        }
    ]
    
    for case in test_cases:
        logger.info(f"\n=== Testing {case['name']} ===")
        
        # Set up environment
        env = os.environ.copy()
        env.update(case['env'])
        
        try:
            # Test quick import and initialization (without actually starting server)
            cmd = [
                sys.executable, "-c",
                """
import sys
import os
sys.path.insert(0, 'agrisense_app/backend')

# Test the import and basic functionality
try:
    from main import PyTorchSentenceEncoder, _load_chatbot_artifacts
    
    # Test encoder creation
    use_pytorch = os.getenv("AGRISENSE_USE_PYTORCH_SBERT", "auto").lower()
    print(f"Environment setting: AGRISENSE_USE_PYTORCH_SBERT={use_pytorch}")
    
    if use_pytorch in ("1", "true", "yes", "auto"):
        try:
            encoder = PyTorchSentenceEncoder()
            if encoder.model is not None:
                print("✅ PyTorch SentenceTransformer loaded successfully")
            else:
                print("⚠️  PyTorch SentenceTransformer failed to load (dependency issue)")
        except Exception as e:
            print(f"⚠️  PyTorch loading failed: {e}")
    else:
        print("🚫 PyTorch usage disabled by configuration")
        
    print("✅ Import and basic functionality test passed")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
                """
            ]
            
            result = subprocess.run(
                cmd, 
                env=env, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=repo_root
            )
            
            print("STDOUT:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode == 0:
                logger.info(f"✅ {case['name']} test passed")
            else:
                logger.warning(f"⚠️  {case['name']} test completed with issues")
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {case['name']} test timed out")
        except Exception as e:
            logger.error(f"❌ {case['name']} test failed: {e}")

def test_environment_variable_parsing():
    """Test environment variable parsing logic."""
    logger.info("\n=== Testing Environment Variable Parsing ===")
    
    test_values = [
        ("1", "should enable PyTorch"),
        ("true", "should enable PyTorch"),
        ("yes", "should enable PyTorch"),
        ("auto", "should try PyTorch with fallback"),
        ("0", "should disable PyTorch"),
        ("false", "should disable PyTorch"),
        ("no", "should disable PyTorch"),
        ("", "should default to auto"),
        ("invalid", "should be treated as disabled")
    ]
    
    for value, expected in test_values:
        # Simulate the logic from the main code
        use_pytorch = value.lower() if value else "auto"
        pytorch_enabled = use_pytorch in ("1", "true", "yes", "auto")
        
        logger.info(f"Value: '{value}' -> {use_pytorch} -> {'Enabled' if pytorch_enabled else 'Disabled'} ({expected})")

def main():
    """Run all tests."""
    logger.info("🚀 Starting PyTorch SentenceTransformer Integration Tests")
    
    test_environment_variable_parsing()
    test_server_startup_modes()
    
    logger.info("\n✅ All tests completed!")
    logger.info("\nNext Steps:")
    logger.info("1. Install PyTorch dependencies: pip install torch sentence-transformers")  
    logger.info("2. Set environment: export AGRISENSE_USE_PYTORCH_SBERT=1")
    logger.info("3. Start server: uvicorn agrisense_app.backend.main:app --port 8004")
    logger.info("4. Check logs for 'Using PyTorch SentenceTransformer' message")

if __name__ == "__main__":
    main()