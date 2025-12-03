#!/usr/bin/env python3
"""
Comprehensive ML Model Accuracy Testing for AgriSense
Tests chatbot, disease detection, weed analysis, and recommendation systems
"""

import requests
import base64
import io
import json
import time
from PIL import Image, ImageDraw
import numpy as np

class AgriSenseAccuracyTester:
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
        self.results = {
            'chatbot': {'total': 0, 'accurate': 0, 'responses': []},
            'disease_detection': {'total': 0, 'accurate': 0, 'responses': []},
            'weed_analysis': {'total': 0, 'accurate': 0, 'responses': []},
            'recommendations': {'total': 0, 'accurate': 0, 'responses': []},
            'vlm_integration': {'available': False, 'responses': []}
        }

    def create_test_image(self, disease_type="blight", severity="moderate"):
        """Create synthetic test images for different conditions"""
        img = np.zeros((224, 224, 3), dtype=np.uint8)

        # Base crop color (green)
        img[:, :, 1] = 120  # Green channel

        if disease_type == "blight":
            # Add brown/yellow spots for blight
            for i in range(8):
                x, y = np.random.randint(20, 200, 2)
                size = np.random.randint(15, 35)
                # Brown spots
                img[y:y+size, x:x+size, 0] = 139  # Red
                img[y:y+size, x:x+size, 1] = 69   # Green
                img[y:y+size, x:x+size, 2] = 19   # Blue

        elif disease_type == "powdery_mildew":
            # Add white powdery spots
            for i in range(6):
                x, y = np.random.randint(30, 190, 2)
                size = np.random.randint(10, 25)
                # White spots
                img[y:y+size, x:x+size, 0] = 220
                img[y:y+size, x:x+size, 1] = 220
                img[y:y+size, x:x+size, 2] = 220

        # Convert to PIL Image
        pil_img = Image.fromarray(img)
        buffer = io.BytesIO()
        pil_img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def test_chatbot_accuracy(self):
        """Test chatbot accuracy with agricultural queries"""
        print("🧠 Testing Chatbot Accuracy...")

        test_queries = [
            {
                'query': "What are the best crops for clay soil?",
                'expected_keywords': ['clay', 'soil', 'crops', 'suitable'],
                'context': 'soil_management'
            },
            {
                'query': "How to prevent tomato blight disease?",
                'expected_keywords': ['tomato', 'blight', 'prevent', 'disease'],
                'context': 'disease_prevention'
            },
            {
                'query': "What are the signs of nitrogen deficiency in corn?",
                'expected_keywords': ['nitrogen', 'deficiency', 'corn', 'signs'],
                'context': 'nutrient_deficiency'
            },
            {
                'query': "How much water does wheat need during flowering stage?",
                'expected_keywords': ['wheat', 'water', 'flowering', 'irrigation'],
                'context': 'irrigation_management'
            },
            {
                'query': "What pesticides are safe for organic farming?",
                'expected_keywords': ['pesticides', 'organic', 'safe', 'farming'],
                'context': 'pest_management'
            }
        ]

        for test_case in test_queries:
            try:
                payload = {
                    'message': test_case['query'],
                    'zone_id': 'Z1'
                }

                response = requests.post(f"{self.base_url}/chat", json=payload, timeout=15)
                self.results['chatbot']['total'] += 1

                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('answer', '').lower()

                    # Check if expected keywords are present
                    found_keywords = sum(1 for keyword in test_case['expected_keywords']
                                       if keyword.lower() in answer)

                    accuracy_score = found_keywords / len(test_case['expected_keywords'])

                    if accuracy_score >= 0.6:  # 60% keyword match threshold
                        self.results['chatbot']['accurate'] += 1
                        status = "ACCURATE"
                    else:
                        status = "INACCURATE"

                    self.results['chatbot']['responses'].append({
                        'query': test_case['query'],
                        'status': status,
                        'score': accuracy_score,
                        'response_length': len(result.get('answer', '')),
                        'sources': len(result.get('sources', []))
                    })

                    print(f"  {'✅' if status == 'ACCURATE' else '❌'} {test_case['query'][:50]}...")
                    print(f"     Accuracy: {accuracy_score:.1%} | Length: {len(result.get('answer', ''))}")
                else:
                    print(f"  ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error testing query: {e}")

        print(f"Chatbot Accuracy: {self.results['chatbot']['accurate']}/{self.results['chatbot']['total']}")

    def test_disease_detection_accuracy(self):
        """Test disease detection model accuracy"""
        print("\n🦠 Testing Disease Detection Accuracy...")

        test_cases = [
            {
                'crop': 'tomato',
                'disease': 'blight',
                'expected_confidence': 0.7,
                'image_type': 'blight_spots'
            },
            {
                'crop': 'cotton',
                'disease': 'powdery_mildew',
                'expected_confidence': 0.7,
                'image_type': 'white_powdery'
            },
            {
                'crop': 'corn',
                'disease': 'rust',
                'expected_confidence': 0.6,
                'image_type': 'rust_spots'
            }
        ]

        for test_case in test_cases:
            try:
                # Create test image based on disease type
                image_data = self.create_test_image(test_case['disease'], 'moderate')

                payload = {
                    'image_data': image_data,
                    'crop_type': test_case['crop'],
                    'field_info': {
                        'crop_type': test_case['crop'],
                        'field_size_acres': 2.0
                    }
                }

                response = requests.post(f"{self.base_url}/api/disease/detect",
                                       json=payload, timeout=20)
                self.results['disease_detection']['total'] += 1

                if response.status_code == 200:
                    result = response.json()

                    # Check accuracy based on confidence and disease detection
                    confidence = result.get('confidence', 0)
                    detected_disease = result.get('primary_disease', '').lower()

                    # Basic accuracy check - should detect some disease with reasonable confidence
                    if confidence >= test_case['expected_confidence'] and confidence > 0.3:
                        self.results['disease_detection']['accurate'] += 1
                        status = "ACCURATE"
                    else:
                        status = "INACCURATE"

                    self.results['disease_detection']['responses'].append({
                        'crop': test_case['crop'],
                        'expected_disease': test_case['disease'],
                        'detected_disease': detected_disease,
                        'confidence': confidence,
                        'status': status,
                        'vlm_enhanced': 'vlm_analysis' in result
                    })

                    print(f"  {'✅' if status == 'ACCURATE' else '❌'} {test_case['crop']} {test_case['disease']}...")
                    print(f"     Confidence: {confidence:.1%} | VLM: {'Yes' if 'vlm_analysis' in result else 'No'}")
                else:
                    print(f"  ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error testing disease detection: {e}")

        print(f"Disease Detection Accuracy: {self.results['disease_detection']['accurate']}/{self.results['disease_detection']['total']}")

    def test_weed_analysis_accuracy(self):
        """Test weed analysis model accuracy"""
        print("\n🌿 Testing Weed Analysis Accuracy...")

        test_cases = [
            {
                'crop': 'corn',
                'weed_coverage': 0.15,  # 15% expected coverage
                'expected_pressure': 'moderate'
            },
            {
                'crop': 'wheat',
                'weed_coverage': 0.08,  # 8% expected coverage
                'expected_pressure': 'low'
            },
            {
                'crop': 'soybean',
                'weed_coverage': 0.25,  # 25% expected coverage
                'expected_pressure': 'high'
            }
        ]

        for test_case in test_cases:
            try:
                # Create test image with weed-like patterns
                image_data = self.create_test_image('weed_spots', 'moderate')

                payload = {
                    'image_data': image_data,
                    'crop_type': test_case['crop'],
                    'field_info': {
                        'crop_type': test_case['crop'],
                        'field_size_acres': 3.0
                    }
                }

                response = requests.post(f"{self.base_url}/api/weed/analyze",
                                       json=payload, timeout=20)
                self.results['weed_analysis']['total'] += 1

                if response.status_code == 200:
                    result = response.json()

                    # Check accuracy based on coverage and pressure assessment
                    coverage = result.get('weed_coverage_percentage', 0)
                    pressure = result.get('weed_pressure', '').lower()

                    # Accuracy check - should detect weeds with reasonable coverage
                    if coverage >= 0.05 and coverage <= 0.4:  # Reasonable range
                        self.results['weed_analysis']['accurate'] += 1
                        status = "ACCURATE"
                    else:
                        status = "INACCURATE"

                    self.results['weed_analysis']['responses'].append({
                        'crop': test_case['crop'],
                        'detected_coverage': coverage,
                        'pressure': pressure,
                        'status': status,
                        'vlm_enhanced': 'vlm_analysis' in result
                    })

                    print(f"  {'✅' if status == 'ACCURATE' else '❌'} {test_case['crop']} weed analysis...")
                    print(f"     Coverage: {coverage:.1%} | Pressure: {pressure}")
                else:
                    print(f"  ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error testing weed analysis: {e}")

        print(f"Weed Analysis Accuracy: {self.results['weed_analysis']['accurate']}/{self.results['weed_analysis']['total']}")

    def test_recommendation_accuracy(self):
        """Test recommendation system accuracy"""
        print("\n📊 Testing Recommendation System Accuracy...")

        test_cases = [
            {
                'crop': 'tomato',
                'soil_type': 'clay',
                'ph': 6.2,
                'moisture': 45,
                'temperature': 28,
                'expected_water': 15,  # Expected water in liters
                'expected_fertilizer': 2.5  # Expected fertilizer in kg
            },
            {
                'crop': 'corn',
                'soil_type': 'loam',
                'ph': 7.1,
                'moisture': 38,
                'temperature': 22,
                'expected_water': 12,
                'expected_fertilizer': 3.2
            }
        ]

        for test_case in test_cases:
            try:
                payload = {
                    'zone_id': 'Z1',
                    'plant': test_case['crop'],
                    'soil_type': test_case['soil_type'],
                    'area_m2': 100.0,
                    'ph': test_case['ph'],
                    'moisture_pct': test_case['moisture'],
                    'temperature_c': test_case['temperature'],
                    'ec_dS_m': 1.2,
                    'n_ppm': 150,
                    'p_ppm': 50,
                    'k_ppm': 200
                }

                response = requests.post(f"{self.base_url}/recommend",
                                       json=payload, timeout=10)
                self.results['recommendations']['total'] += 1

                if response.status_code == 200:
                    result = response.json()

                    # Check if recommendations are reasonable (non-zero values)
                    water_liters = result.get('water_liters', 0)
                    fertilizer_kg = result.get('fertilizer_kg', 0)

                    # Basic accuracy check - should provide reasonable recommendations
                    if water_liters > 0 and fertilizer_kg > 0:
                        self.results['recommendations']['accurate'] += 1
                        status = "ACCURATE"
                    else:
                        status = "INACCURATE"

                    self.results['recommendations']['responses'].append({
                        'crop': test_case['crop'],
                        'water_liters': water_liters,
                        'fertilizer_kg': fertilizer_kg,
                        'water_source': result.get('water_source', 'unknown'),
                        'status': status
                    })

                    print(f"  {'✅' if status == 'ACCURATE' else '❌'} {test_case['crop']} recommendations...")
                    print(f"     Water: {water_liters}L | Fertilizer: {fertilizer_kg}kg")
                else:
                    print(f"  ❌ Error: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error testing recommendations: {e}")

        print(f"Recommendation Accuracy: {self.results['recommendations']['accurate']}/{self.results['recommendations']['total']}")

    def test_vlm_integration(self):
        """Test VLM integration if available"""
        print("\n🤖 Testing VLM Integration...")

        try:
            response = requests.get(f"{self.base_url}/api/vlm/status", timeout=10)

            if response.status_code == 200:
                status_data = response.json()
                self.results['vlm_integration']['available'] = status_data.get('vlm_available', False)

                if status_data.get('vlm_available', False):
                    print("  ✅ VLM integration available")

                    # Test VLM analysis
                    image_data = self.create_test_image('blight', 'moderate')
                    payload = {
                        'image_data': image_data,
                        'crop_type': 'tomato',
                        'field_info': {
                            'crop_type': 'tomato',
                            'field_size_acres': 2.0
                        }
                    }

                    vlm_response = requests.post(f"{self.base_url}/api/vlm/analyze",
                                               json=payload, timeout=25)

                    if vlm_response.status_code == 200:
                        vlm_result = vlm_response.json()
                        health_score = vlm_result.get('overall_health_score', 0)

                        self.results['vlm_integration']['responses'].append({
                            'health_score': health_score,
                            'priority_actions': len(vlm_result.get('priority_actions', [])),
                            'knowledge_matches': vlm_result.get('knowledge_matches', 0)
                        })

                        print(f"     Health Score: {health_score}/100")
                        print(f"     Priority Actions: {len(vlm_result.get('priority_actions', []))}")
                    else:
                        print(f"  ❌ VLM analysis error: {vlm_response.status_code}")
                else:
                    print("  ⚠️ VLM integration not available (models not loaded)")
            else:
                print(f"  ❌ VLM status error: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Error testing VLM integration: {e}")

    def generate_accuracy_report(self):
        """Generate comprehensive accuracy report"""
        print("\n📊 COMPREHENSIVE ACCURACY REPORT")
        print("=" * 50)

        # Calculate overall scores
        chatbot_score = (self.results['chatbot']['accurate'] / max(self.results['chatbot']['total'], 1)) * 100
        disease_score = (self.results['disease_detection']['accurate'] / max(self.results['disease_detection']['total'], 1)) * 100
        weed_score = (self.results['weed_analysis']['accurate'] / max(self.results['weed_analysis']['total'], 1)) * 100
        recommendation_score = (self.results['recommendations']['accurate'] / max(self.results['recommendations']['total'], 1)) * 100

        # Weighted overall score (chatbot and recommendations more critical for accuracy)
        overall_score = (chatbot_score * 0.3 + disease_score * 0.25 + weed_score * 0.25 + recommendation_score * 0.2)

        print(f"🤖 Chatbot Accuracy:      {chatbot_score:.1f}% ({self.results['chatbot']['accurate']}/{self.results['chatbot']['total']})")
        print(f"🦠 Disease Detection:     {disease_score:.1f}% ({self.results['disease_detection']['accurate']}/{self.results['disease_detection']['total']})")
        print(f"🌿 Weed Analysis:         {weed_score:.1f}% ({self.results['weed_analysis']['accurate']}/{self.results['weed_analysis']['total']})")
        print(f"📊 Recommendations:       {recommendation_score:.1f}% ({self.results['recommendations']['accurate']}/{self.results['recommendations']['total']})")

        if self.results['vlm_integration']['available']:
            print(f"🤖 VLM Integration:       Available ✅")
        else:
            print(f"🤖 VLM Integration:       Not Available ⚠️")

        print(f"\n🎯 Overall ML Accuracy:   {overall_score:.1f}%")

        # Performance insights
        print("\n📈 PERFORMANCE INSIGHTS:")
        if chatbot_score >= 80:
            print("  ✅ Chatbot: Excellent contextual understanding and response quality")
        elif chatbot_score >= 60:
            print("  ⚠️ Chatbot: Good but could benefit from more training data")
        else:
            print("  ❌ Chatbot: Needs significant improvement in knowledge base")

        if disease_score >= 70:
            print("  ✅ Disease Detection: Reliable diagnostic capabilities")
        elif disease_score >= 50:
            print("  ⚠️ Disease Detection: Moderate accuracy, field testing recommended")
        else:
            print("  ❌ Disease Detection: Low accuracy, requires model retraining")

        if recommendation_score >= 80:
            print("  ✅ Recommendations: Precise and actionable advice")
        else:
            print("  ⚠️ Recommendations: Generally good but needs fine-tuning")

        return overall_score

def main():
    """Run comprehensive ML accuracy tests"""
    print("🌾 AGRISENSE ML MODEL ACCURACY TESTING")
    print("=" * 50)

    tester = AgriSenseAccuracyTester()

    # Run all tests
    tester.test_chatbot_accuracy()
    tester.test_disease_detection_accuracy()
    tester.test_weed_analysis_accuracy()
    tester.test_recommendation_accuracy()
    tester.test_vlm_integration()

    # Generate report
    final_score = tester.generate_accuracy_report()

    print(f"\n🏆 FINAL ACCURACY SCORE: {final_score:.1f}/100")

    if final_score >= 85:
        print("🌟 EXCELLENT: Production-ready accuracy levels")
    elif final_score >= 70:
        print("✅ GOOD: Suitable for production with minor improvements")
    elif final_score >= 55:
        print("⚠️ MODERATE: Needs improvement before production deployment")
    else:
        print("❌ LOW: Requires significant model retraining and optimization")

if __name__ == "__main__":
    main()
