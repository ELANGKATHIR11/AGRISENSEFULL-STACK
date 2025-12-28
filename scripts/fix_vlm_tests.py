#!/usr/bin/env python3
"""
Fix VLM test files to match updated dataclass signatures
Adds missing image_analysis parameter to all DiseaseDetectionResult and WeedDetectionResult instantiations
"""

import re
from pathlib import Path

def fix_disease_detector_tests():
    """Fix test_vlm_disease_detector.py"""
    test_file = Path(__file__).parent.parent / "tests" / "test_vlm_disease_detector.py"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Fix test_result_creation
    pattern1 = r'(result = DiseaseDetectionResult\(\s+crop_name="Rice",\s+disease_name="Blast Disease",\s+confidence=0\.85,\s+severity=DiseaseSeverity\.MODERATE,\s+affected_area_percentage=30\.5,\s+symptoms_detected=\["Brown spots", "Leaf discoloration"\],\s+treatment_recommendations=\["Apply fungicide"\],\s+prevention_tips=\["Use resistant varieties"\],)\s+(urgent_action_required=False\s+\))'
    
    replacement1 = r'\1\n            image_analysis={},\n            \2'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Fix test_result_serialization
    pattern2 = r'(result = DiseaseDetectionResult\(\s+crop_name="Wheat",\s+disease_name="Rust",\s+confidence=0\.9,\s+severity=DiseaseSeverity\.SEVERE,\s+affected_area_percentage=60\.0,\s+symptoms_detected=\["Orange pustules"\],\s+treatment_recommendations=\["Spray Propiconazole"\],\s+prevention_tips=\["Remove infected plants"\],)\s+(urgent_action_required=True\s+\))'
    
    replacement2 = r'\1\n            image_analysis={},\n            \2'
    
    content = re.sub(pattern2, replacement2, content)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {test_file.name}")

def fix_weed_detector_tests():
    """Fix test_vlm_weed_detector.py"""
    test_file = Path(__file__).parent.parent / "tests" / "test_vlm_weed_detector.py"
    
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Fix test_result_creation (first occurrence)
    pattern1 = r'(result = WeedDetectionResult\(\s+crop_name="Rice",\s+weeds_identified=\["Barnyard Grass"\],\s+infestation_level=WeedInfestationLevel\.MODERATE,\s+weed_coverage_percentage=25\.5,\s+control_recommendations=\{\s+ControlMethod\.CHEMICAL: \["Apply herbicide"\],\s+ControlMethod\.ORGANIC: \["Hand weeding"\]\s+\},\s+priority_level="medium",\s+estimated_yield_impact="Moderate \(15-25%\)",\s+best_control_timing=\["Early morning"\],)\s+(multiple_weeds_detected=False\s+\))'
    
    replacement1 = r'\1\n            image_analysis={},\n            \2'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Fix test_result_serialization (second occurrence)
    pattern2 = r'(result = WeedDetectionResult\(\s+crop_name="Wheat",\s+weeds_identified=\["Wild Oat", "Phalaris"\],\s+infestation_level=WeedInfestationLevel\.HIGH,\s+weed_coverage_percentage=40\.0,\s+control_recommendations=\{\s+ControlMethod\.CHEMICAL: \["Sulfosulfuron"\],\s+ControlMethod\.MECHANICAL: \["Inter-row cultivation"\]\s+\},\s+priority_level="high",\s+estimated_yield_impact="High \(25-40%\)",\s+best_control_timing=\["Post-emergence"\],)\s+(multiple_weeds_detected=True\s+\))'
    
    replacement2 = r'\1\n            image_analysis={},\n            \2'
    
    content = re.sub(pattern2, replacement2, content)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed {test_file.name}")

def main():
    print("🔧 Fixing VLM test files...\n")
    
    try:
        fix_disease_detector_tests()
        fix_weed_detector_tests()
        
        print("\n🎉 All test files fixed!")
        print("\nNext: Run pytest to verify fixes")
        print("Command: pytest tests/test_vlm_disease_detector.py tests/test_vlm_weed_detector.py -v")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
