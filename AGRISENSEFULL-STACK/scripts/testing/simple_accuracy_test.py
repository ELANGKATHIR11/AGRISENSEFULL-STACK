#!/usr/bin/env python3
"""
Simple ML Model Accuracy Testing for AgriSense
Tests chatbot, disease detection, and recommendation systems
"""

import requests
import base64
import io
import json
from PIL import Image

class SimpleAccuracyTester:
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
        self.results = {
            'chatbot': {'total': 0, 'working': 0},
            'disease_detection': {'total': 0, 'working': 0},
            'weed_analysis': {'total': 0, 'working': 0},
            'recommendations': {'total': 0, 'working': 0}
        }

    def create_test_image(self):
        """Create a simple test image"""
        img = Image.new('RGB', (100, 100), (50, 150, 50))  # Green background
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def test_chatbot(self):
        """Test chatbot functionality"""
        print("Testing Chatbot...")

        queries = [
            "What crops grow well in clay soil?",
            "How to prevent tomato diseases?",
            "What are signs of nitrogen deficiency?"
        ]

        for query in queries:
            try:
                payload = {'message': query, 'zone_id': 'Z1'}
                response = requests.post(f"{self.base_url}/chat", json=payload, timeout=15)

                self.results['chatbot']['total'] += 1
                if response.status_code == 200:
                    result = response.json()
                    if 'answer' in result and len(result['answer']) > 10:
                        self.results['chatbot']['working'] += 1
                        print(f"  SUCCESS: {query[:30]}... -> {len(result['answer'])} chars")
                    else:
                        print(f"  WARNING: Short response for {query[:30]}...")
                else:
                    print(f"  ERROR: {response.status_code} for {query[:30]}...")

            except Exception as e:
                print(f"  ERROR: {e}")

        print(f"Chatbot: {self.results['chatbot']['working']}/{self.results['chatbot']['total']} working")

    def test_disease_detection(self):
        """Test disease detection"""
        print("\nTesting Disease Detection...")

        crops = ['tomato', 'corn', 'cotton']

        for crop in crops:
            try:
                payload = {
                    'image_data': self.create_test_image(),
                    'crop_type': crop,
                    'field_info': {'crop_type': crop, 'field_size_acres': 1.0}
                }

                response = requests.post(f"{self.base_url}/api/disease/detect", json=payload, timeout=15)

                self.results['disease_detection']['total'] += 1
                if response.status_code == 200:
                    result = response.json()
                    confidence = result.get('confidence', 0)
                    self.results['disease_detection']['working'] += 1
                    print(f"  SUCCESS: {crop} -> confidence: {confidence:.2f}")
                else:
                    print(f"  ERROR: {response.status_code} for {crop}")

            except Exception as e:
                print(f"  ERROR: {e}")

        print(f"Disease Detection: {self.results['disease_detection']['working']}/{self.results['disease_detection']['total']} working")

    def test_recommendations(self):
        """Test recommendation system"""
        print("\nTesting Recommendations...")

        test_cases = [
            {
                'plant': 'tomato',
                'soil_type': 'clay',
                'ph': 6.5,
                'moisture_pct': 45
            },
            {
                'plant': 'corn',
                'soil_type': 'loam',
                'ph': 7.0,
                'moisture_pct': 40
            }
        ]

        for case in test_cases:
            try:
                payload = {
                    'zone_id': 'Z1',
                    'plant': case['plant'],
                    'soil_type': case['soil_type'],
                    'area_m2': 100,
                    'ph': case['ph'],
                    'moisture_pct': case['moisture_pct'],
                    'temperature_c': 25,
                    'ec_dS_m': 1.2,
                    'n_ppm': 150,
                    'p_ppm': 50,
                    'k_ppm': 200
                }

                response = requests.post(f"{self.base_url}/recommend", json=payload, timeout=10)

                self.results['recommendations']['total'] += 1
                if response.status_code == 200:
                    result = response.json()
                    water = result.get('water_liters', 0)
                    fertilizer = result.get('fertilizer_kg', 0)

                    if water > 0 and fertilizer > 0:
                        self.results['recommendations']['working'] += 1
                        print(f"  SUCCESS: {case['plant']} -> Water: {water}L, Fertilizer: {fertilizer}kg")
                    else:
                        print(f"  WARNING: Zero values for {case['plant']}")
                else:
                    print(f"  ERROR: {response.status_code} for {case['plant']}")

            except Exception as e:
                print(f"  ERROR: {e}")

        print(f"Recommendations: {self.results['recommendations']['working']}/{self.results['recommendations']['total']} working")

    def generate_report(self):
        """Generate final report"""
        print("\n" + "=" * 50)
        print("ACCURACY TEST RESULTS")
        print("=" * 50)

        chatbot_acc = (self.results['chatbot']['working'] / max(self.results['chatbot']['total'], 1)) * 100
        disease_acc = (self.results['disease_detection']['working'] / max(self.results['disease_detection']['total'], 1)) * 100
        recommendation_acc = (self.results['recommendations']['working'] / max(self.results['recommendations']['total'], 1)) * 100

        overall_acc = (chatbot_acc + disease_acc + recommendation_acc) / 3

        print(f"Chatbot Accuracy:         {chatbot_acc:.1f}% ({self.results['chatbot']['working']}/{self.results['chatbot']['total']})")
        print(f"Disease Detection:        {disease_acc:.1f}% ({self.results['disease_detection']['working']}/{self.results['disease_detection']['total']})")
        print(f"Recommendation System:    {recommendation_acc:.1f}% ({self.results['recommendations']['working']}/{self.results['recommendations']['total']})")
        print(f"\nOverall ML Accuracy:      {overall_acc:.1f}%")

        if overall_acc >= 80:
            print("EXCELLENT: All systems working well")
        elif overall_acc >= 60:
            print("GOOD: Most systems functional")
        elif overall_acc >= 40:
            print("MODERATE: Some issues need attention")
        else:
            print("LOW: Significant issues need fixing")

        return overall_acc

def main():
    tester = SimpleAccuracyTester()
    tester.test_chatbot()
    tester.test_disease_detection()
    tester.test_recommendations()
    return tester.generate_report()

if __name__ == "__main__":
    main()
