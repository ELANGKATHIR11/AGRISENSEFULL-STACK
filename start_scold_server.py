"""
SCOLD VLM Server Launcher for AgriSense
========================================

Starts the SCOLD Vision-Language Model server for agricultural image analysis.
Supports disease detection, weed identification, and crop health assessment.

Usage:
    python start_scold_server.py
    python start_scold_server.py --port 8001
    python start_scold_server.py --model-path ./AI_Models/scold
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import torch
    except ImportError:
        missing.append("torch")
    
    try:
        import transformers
    except ImportError:
        missing.append("transformers")
    
    try:
        import PIL
    except ImportError:
        missing.append("pillow")
    
    try:
        from fastapi import FastAPI
    except ImportError:
        missing.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Install with: pip install torch transformers pillow fastapi uvicorn")
        return False
    
    return True


def check_model_files(model_path: Path) -> bool:
    """Check if SCOLD model files exist"""
    if not model_path.exists():
        logger.error(f"Model path does not exist: {model_path}")
        logger.error("Clone SCOLD model with:")
        logger.error("  cd AI_Models && git clone https://huggingface.co/enalis/scold")
        return False
    
    # Check for essential files
    required_files = ["config.json", "pytorch_model.bin"]
    missing = [f for f in required_files if not (model_path / f).exists()]
    
    if missing:
        logger.warning(f"Model files might be incomplete. Missing: {missing}")
    
    return True


def start_scold_server(
    host: str = "0.0.0.0",
    port: int = 8001,
    model_path: Path = None,
    reload: bool = False
):
    """Start SCOLD VLM server"""
    
    if model_path is None:
        model_path = Path(__file__).parent.parent / "AI_Models" / "scold"
    
    # Set environment variables
    os.environ["SCOLD_MODEL_PATH"] = str(model_path)
    os.environ["SCOLD_BASE_URL"] = f"http://{host}:{port}"
    
    logger.info("="* 60)
    logger.info("🚀 Starting SCOLD VLM Server for AgriSense")
    logger.info("="* 60)
    logger.info(f"Model Path: {model_path}")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"API Endpoints:")
    logger.info(f"  - http://{host}:{port}/health")
    logger.info(f"  - http://{host}:{port}/api/detect/disease")
    logger.info(f"  - http://{host}:{port}/api/detect/weed")
    logger.info(f"  - http://{host}:{port}/api/analyze")
    logger.info("="* 60)
    
    try:
        # Import server application
        from agrisense_app.backend.scold_server import app
        
        import uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        return 1
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Start SCOLD VLM Server for AgriSense"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind to (default: 8001)"
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        help="Path to SCOLD model files"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies and model files, don't start server"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Determine model path
    model_path = args.model_path
    if model_path is None:
        model_path = Path(__file__).parent.parent / "AI_Models" / "scold"
    
    # Check model files
    if not check_model_files(model_path):
        return 1
    
    if args.check_only:
        logger.info("✅ All checks passed!")
        return 0
    
    # Start server
    return start_scold_server(
        host=args.host,
        port=args.port,
        model_path=model_path,
        reload=args.reload
    )


if __name__ == "__main__":
    sys.exit(main())
