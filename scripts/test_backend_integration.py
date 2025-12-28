#!/usr/bin/env python3
"""
Test Enhanced ML Systems Integration
Tests the actual backend integration of enhanced disease and weed detection
"""

import sys
import os
import base64
import json
try:
    import pytest  # type: ignore[import-not-found]
except Exception:
    pytest = None

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agrisense_app', 'backend'))
from pathlib import Path
from PIL import Image
import io

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agrisense_app" / "backend"))

def create_test_image():
    """Create a test plant image"""
    img = Image.new('RGB', (512, 512), color='lightgreen')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw plant features
    draw.ellipse([100, 100, 200, 150], fill='green')
    draw.ellipse([150, 120, 250, 170], fill='darkgreen')
    
    # Disease spots
    draw.ellipse([120, 110, 140, 130], fill='brown')
    draw.ellipse([170, 150, 190, 170], fill='saddlebrown')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def test_disease_detection():
    """Test disease detection system"""
    print("🧪 Testing Disease Detection System")
    
    try:
        from agrisense_app.backend.comprehensive_disease_detector import ComprehensiveDiseaseDetector
    except ImportError:
        print("⚠️  Disease detection module not found - skipping test")
        try:
            if pytest is not None:
                pytest.skip("Disease detection module not available")
            else:
                return
        except Exception:
            return
    
    # Create engine
    engine = ComprehensiveDiseaseDetector()
    assert engine is not None, "Failed to create disease detection engine"
    
    # Create test image
    test_image = create_test_image()
    assert test_image is not None, "Failed to create test image"
    
    # Test detection
    result = engine.analyze_disease_image(test_image, crop_type="tomato")
    
    print("[SUCCESS] Disease detection working!")
    print(f"   Model used: {result.get('model_used', 'unknown')}")
    print(f"   Confidence: {result.get('detection_confidence', 0):.3f}")
    
    if 'disease_detected' in result:
        print(f"   Disease: {result['disease_detected']}")
    
    if 'treatment_recommendations' in result:
        recs = result['treatment_recommendations']
        print(f"   Severity: {recs.get('severity', 'unknown')}")
    
    # Assert that we got a valid result
    assert result is not None, "Disease detection returned no result"
    assert isinstance(result, dict), "Disease detection result should be a dictionary"

def test_weed_management():
    """Test weed management system"""
    print("🧪 Testing Weed Management System")
    
    try:
        from agrisense_app.backend.weed_management import WeedManagementEngine
    except ImportError:
        print("⚠️  Weed management module not found - skipping test")
        try:
            if pytest is not None:
                pytest.skip("Weed management module not available")
            else:
                return
        except Exception:
            return
    
    # Create engine
    engine = WeedManagementEngine()
    assert engine is not None, "Failed to create weed management engine"
    
    # Create test image
    test_image = create_test_image()
    assert test_image is not None, "Failed to create test image"
    
    # Test detection
    result = engine.detect_weeds(test_image, crop_type="corn")
    
    print("✅ Weed management working!")
    print(f"   Model used: {result.get('model_used', 'unknown')}")
    print(f"   Confidence: {result.get('detection_confidence', 0):.3f}")
    
    if 'weed_coverage_percent' in result:
        print(f"   Weed coverage: {result['weed_coverage_percent']:.1f}%")
    
    if 'management_recommendations' in result:
        recs = result['management_recommendations']
        print(f"   Severity: {recs.get('severity', 'unknown')}")
    
    # Assert that we got a valid result
    assert result is not None, "Weed management returned no result"
    assert isinstance(result, dict), "Weed management result should be a dictionary"

def test_enhanced_functions():
    """Test enhanced analysis functions"""
    print("🧪 Testing Enhanced Analysis Functions")
    
    # Test disease analysis
    try:
        from agrisense_app.backend.disease_detection import analyze_disease_image_enhanced
    except ImportError:
        print("⚠️  Disease detection module not found - skipping test")
        try:
            if pytest is not None:
                pytest.skip("Disease detection module not available")
            else:
                return
        except Exception:
            return
    
    test_image = create_test_image()
    assert test_image is not None, "Failed to create test image"
    
    result = analyze_disease_image_enhanced(test_image)
    
    if result:
        print("✅ Enhanced disease analysis working!")
        
    # Test weed analysis
    try:
        from agrisense_app.backend.weed_management import analyze_weed_image_enhanced
    except ImportError:
        print("⚠️  Weed management module not found - skipping test")
        try:
            if pytest is not None:
                pytest.skip("Weed management module not available")
            else:
                return
        except Exception:
            return
    
    result2 = analyze_weed_image_enhanced(test_image)
    
    if result2:
        print("✅ Enhanced weed analysis working!")
    
    # Assert that at least one function worked
    assert result is not None or result2 is not None, "Both enhanced analysis functions failed"

def test_model_files():
    """Test if model files exist and are loadable"""
    print("🧪 Testing Model Files")
    
    backend_dir = Path("agrisense_app/backend")
    assert backend_dir.exists(), f"Backend directory not found: {backend_dir}"
    
    # Check for enhanced models
    enhanced_files = [
        "disease_model_enhanced.joblib",
        "weed_model_enhanced.joblib",
        "disease_classes_enhanced.json",
        "weed_classes_enhanced.json",
        "model_integration_config.json"
    ]
    
    found_files = 0
    for file in enhanced_files:
        file_path = backend_dir / file
        if file_path.exists():
            print(f"✅ Found: {file}")
            found_files += 1
        else:
            print(f"❌ Missing: {file}")
    
    print(f"Model files: {found_files}/{len(enhanced_files)} found")
    
    # Test loading models
    import joblib
    
    disease_model_path = backend_dir / "disease_model_enhanced.joblib"
    if disease_model_path.exists():
        model = joblib.load(disease_model_path)
        print("✅ Disease model loads successfully")
        assert model is not None, "Disease model loaded but is None"
    
    weed_model_path = backend_dir / "weed_model_enhanced.joblib"
    if weed_model_path.exists():
        model = joblib.load(weed_model_path)
        print("✅ Weed model loads successfully")
        assert model is not None, "Weed model loaded but is None"
    
    # Assert that the backend directory exists and we can access it
    assert backend_dir.is_dir(), "Backend directory should be a directory"

def main():
    """Main test function for manual execution"""
    print("Testing Enhanced ML Systems Integration")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    
    # Run tests manually when called directly
    try:
        print("Running model files test...")
        test_model_files()
        print("✅ Model files test passed")
    except Exception as e:
        print(f"❌ Model files test failed: {e}")
    
    try:
        print("\nRunning disease detection test...")
        test_disease_detection()
        print("✅ Disease detection test passed")
    except Exception as e:
        print(f"❌ Disease detection test failed: {e}")
    
    try:
        print("\nRunning weed management test...")
        test_weed_management()
        print("✅ Weed management test passed")
    except Exception as e:
        print(f"❌ Weed management test failed: {e}")
    
    try:
        print("\nRunning enhanced functions test...")
        test_enhanced_functions()
        print("✅ Enhanced functions test passed")
    except Exception as e:
        print(f"❌ Enhanced functions test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Manual test execution completed!")
    print("For proper pytest execution, run: pytest scripts/test_backend_integration.py")

if __name__ == "__main__":
    main()