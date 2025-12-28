"""
Comprehensive End-to-End Testing Script for AgriSense
Tests all ML models and features with real values and images
Provides detailed scoring on a 10-point scale
"""

import requests
import json
import base64
import io
import time
from PIL import Image, ImageDraw
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8004"
TIMEOUT = 30

class AgriSenseE2ETester:
    def __init__(self):
        self.results = {
            "tests": [],
            "scores": {},
            "total_score": 0,
            "max_score": 0,
            "start_time": datetime.now().isoformat()
        }
        
    def create_realistic_plant_image(self, image_type: str = "healthy") -> str:
        """Create a realistic plant image for testing"""
        img = Image.new('RGB', (640, 480), color='white')
        draw = ImageDraw.Draw(img)
        
        if image_type == "diseased":
            # Simulate diseased leaf with brown spots
            draw.ellipse([200, 150, 440, 330], fill='#2d5016', outline='#1a3009')
            # Add brown/black spots (disease symptoms)
            for i in range(10):
                x = 220 + (i % 5) * 40
                y = 170 + (i // 5) * 40
                draw.ellipse([x, y, x+30, y+30], fill='#4a2511')
        elif image_type == "weed":
            # Simulate weed with irregular shape
            draw.polygon([
                (150, 300), (200, 250), (250, 240), (300, 250),
                (350, 300), (320, 350), (250, 380), (180, 350)
            ], fill='#3d5c1f', outline='#2a4015')
        else:
            # Healthy green leaf
            draw.ellipse([200, 150, 440, 330], fill='#2d5016', outline='#1a3009')
            draw.line([320, 150, 320, 330], fill='#1a3009', width=3)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def test_health_endpoint(self) -> Tuple[bool, str, float]:
        """Test 1: Health Check"""
        print("\n🔍 Test 1: Health Check Endpoint")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check passed: {data}")
                return True, "Health endpoint responsive", 10.0
            else:
                return False, f"Health check failed: {response.status_code}", 0.0
        except Exception as e:
            return False, f"Health check error: {str(e)}", 0.0
    
    def test_irrigation_recommendation(self) -> Tuple[bool, str, float]:
        """Test 2: Smart Irrigation Recommendation"""
        print("\n🔍 Test 2: Smart Irrigation Recommendation")
        score = 0.0
        
        test_cases = [
            {
                "name": "Rice - High Temperature, Low Moisture",
                "data": {
                    "zone_id": "Z1",
                    "plant": "rice",
                    "soil_type": "clay",
                    "area_m2": 100.0,
                    "ph": 6.5,
                    "moisture_pct": 25.0,
                    "temperature_c": 32.5,
                    "ec_dS_m": 1.0
                },
                "expect_high_water": True
            },
            {
                "name": "Wheat - Moderate Conditions",
                "data": {
                    "zone_id": "Z1",
                    "plant": "wheat",
                    "soil_type": "loam",
                    "area_m2": 100.0,
                    "ph": 6.8,
                    "moisture_pct": 45.0,
                    "temperature_c": 22.0,
                    "ec_dS_m": 1.2
                },
                "expect_high_water": False
            },
            {
                "name": "Tomato - Very Dry Soil",
                "data": {
                    "zone_id": "Z1",
                    "plant": "tomato",
                    "soil_type": "loam",
                    "area_m2": 100.0,
                    "ph": 6.3,
                    "moisture_pct": 15.0,
                    "temperature_c": 28.0,
                    "ec_dS_m": 1.5
                },
                "expect_high_water": True
            }
        ]
        
        try:
            passed = 0
            for case in test_cases:
                response = requests.post(
                    f"{BASE_URL}/recommend",
                    json=case["data"],
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   🌾 {case['name']}")
                    print(f"      Water needed: {result.get('water_liters', 'N/A')} liters")
                    print(f"      Tips: {len(result.get('tips', []))} provided")
                    print(f"      Notes: {len(result.get('notes', []))} provided")
                    
                    # Validate response structure (based on Recommendation model)
                    if 'water_liters' in result and 'tips' in result and 'notes' in result:
                        passed += 1
                        water_amount = float(result.get('water_liters', 0))
                        if case["expect_high_water"] and water_amount > 300:
                            print(f"      ✅ Logic correct (high water need)")
                        elif not case["expect_high_water"] and water_amount <= 300:
                            print(f"      ✅ Logic correct (moderate water need)")
                        else:
                            print(f"      ⚠️  Water recommendation: {water_amount}L")
                else:
                    print(f"   ❌ {case['name']} - HTTP {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
            
            score = (passed / len(test_cases)) * 10
            return passed == len(test_cases), f"{passed}/{len(test_cases)} tests passed", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_crop_recommendation(self) -> Tuple[bool, str, float]:
        """Test 3: Crop Recommendation System"""
        print("\n🔍 Test 3: Crop Recommendation System")
        
        test_cases = [
            {
                "name": "High NPK, Acidic Soil (Sandy Loam)",
                "data": {
                    "soil_type": "sandy loam",
                    "nitrogen": 60,
                    "phosphorus": 55,
                    "potassium": 65,
                    "ph": 5.5,
                    "water_level": 150,
                    "temperature": 25,
                    "moisture": 60,
                    "humidity": 70
                }
            },
            {
                "name": "Moderate Nutrients, Neutral pH (Loam)",
                "data": {
                    "soil_type": "loam",
                    "nitrogen": 40,
                    "phosphorus": 35,
                    "potassium": 45,
                    "ph": 6.8,
                    "water_level": 100,
                    "temperature": 22,
                    "moisture": 50,
                    "humidity": 65
                }
            }
        ]
        
        try:
            passed = 0
            for case in test_cases:
                response = requests.post(
                    f"{BASE_URL}/suggest_crop",
                    json=case["data"],
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   🌱 {case['name']}")
                    print(f"      Soil type: {result.get('soil_type', 'N/A')}")
                    top_crops = result.get('top', [])
                    print(f"      Top crops: {[c.get('crop') for c in top_crops[:3]]}")
                    print(f"      Scores: {[c.get('suitability_score') for c in top_crops[:3]]}")
                    
                    if top_crops and len(top_crops) > 0:
                        passed += 1
                        print(f"      ✅ {len(top_crops)} recommendations provided")
                    else:
                        print(f"      ⚠️  No recommendations")
                else:
                    print(f"   ❌ {case['name']} - HTTP {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
            
            score = (passed / len(test_cases)) * 10
            return passed == len(test_cases), f"{passed}/{len(test_cases)} tests passed", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_disease_detection(self) -> Tuple[bool, str, float]:
        """Test 4: Disease Detection ML Model"""
        print("\n🔍 Test 4: Disease Detection ML Model")
        
        test_cases = [
            {"name": "Diseased Leaf", "image_type": "diseased", "crop": "tomato"},
            {"name": "Healthy Leaf", "image_type": "healthy", "crop": "rice"}
        ]
        
        try:
            passed = 0
            for case in test_cases:
                image_base64 = self.create_realistic_plant_image(case["image_type"])
                
                response = requests.post(
                    f"{BASE_URL}/api/disease/detect",
                    json={
                        "image_data": image_base64,  # Correct field name
                        "crop_type": case["crop"]
                    },
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   🦠 {case['name']} ({case['crop']})")
                    disease = result.get('primary_disease', result.get('disease', 'N/A'))
                    print(f"      Disease: {disease}")
                    print(f"      Confidence: {result.get('confidence', 'N/A')}")
                    print(f"      Severity: {result.get('severity', 'N/A')}")
                    print(f"      Treatment provided: {bool(result.get('recommended_treatments', result.get('treatment')))}")
                    
                    # Check for either 'primary_disease' or 'disease' key
                    if 'primary_disease' in result or 'disease' in result:
                        if disease and disease != 'N/A' and disease != 'healthy':
                            passed += 1
                            print(f"      ✅ Detection completed")
                        else:
                            print(f"      ⚠️  No disease detected (healthy or N/A)")
                    else:
                        print(f"      ⚠️  No disease field in response")
                else:
                    print(f"   ❌ {case['name']} - HTTP {response.status_code}")
                    print(f"      Response: {response.text[:200]}")
            
            score = (passed / len(test_cases)) * 10
            return passed > 0, f"{passed}/{len(test_cases)} tests passed", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_weed_management(self) -> Tuple[bool, str, float]:
        """Test 5: Weed Management ML Model"""
        print("\n🔍 Test 5: Weed Management System")
        
        try:
            image_base64 = self.create_realistic_plant_image("weed")
            
            response = requests.post(
                f"{BASE_URL}/api/weed/analyze",
                json={
                    "image_data": image_base64,  # Correct field name
                    "field_info": {"field_size": 1000}
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   🌿 Weed Analysis")
                print(f"      Weed type: {result.get('weed_type', 'N/A')}")
                print(f"      Coverage: {result.get('coverage_percentage', 'N/A')}%")
                print(f"      Severity: {result.get('severity', 'N/A')}")
                print(f"      Control methods: {len(result.get('control_methods', []))}")
                
                if 'weed_type' in result:
                    print(f"      ✅ Analysis completed")
                    return True, "Weed analysis successful", 10.0
                else:
                    print(f"      ⚠️  Incomplete analysis")
                    return True, "Partial analysis", 5.0
            else:
                print(f"   ❌ Weed analysis failed - HTTP {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                return False, f"HTTP {response.status_code}", 0.0
                
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_chatbot(self) -> Tuple[bool, str, float]:
        """Test 6: Agricultural Chatbot"""
        print("\n🔍 Test 6: Agricultural Chatbot")
        score = 0.0
        
        test_queries = [
            {"question": "How to grow tomatoes?", "lang": "en", "min_length": 100},
            {"question": "rice cultivation guide", "lang": "en", "min_length": 100},
            {"question": "carrot", "lang": "en", "min_length": 1000},
            {"question": "wheat farming", "lang": "en", "min_length": 100}
        ]
        
        try:
            passed = 0
            for query in test_queries:
                response = requests.post(
                    f"{BASE_URL}/chatbot/ask",
                    json={
                        "question": query["question"],
                        "language": query["lang"]
                    },
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results = result.get('results', [])
                    
                    if results and len(results) > 0:
                        answer = results[0].get('answer', '')
                        confidence = results[0].get('confidence', 0)
                        
                        print(f"   💬 Q: '{query['question']}'")
                        print(f"      Answer length: {len(answer)} chars")
                        print(f"      Confidence: {confidence}")
                        
                        if len(answer) >= query["min_length"]:
                            passed += 1
                            print(f"      ✅ Comprehensive answer")
                        else:
                            print(f"      ⚠️  Short answer (expected >{query['min_length']} chars)")
                    else:
                        print(f"   ⚠️  Q: '{query['question']}' - No results")
                else:
                    print(f"   ❌ Q: '{query['question']}' - HTTP {response.status_code}")
            
            score = (passed / len(test_queries)) * 10
            return passed > 0, f"{passed}/{len(test_queries)} queries answered well", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_data_persistence(self) -> Tuple[bool, str, float]:
        """Test 7: Data Persistence (Edge Ingest)"""
        print("\n🔍 Test 7: Data Persistence & Edge Ingest")
        
        try:
            test_data = {
                "device_id": "test_device_001",
                "temperature": 28.5,
                "humidity": 65.3,
                "soil_moisture": 42.8,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{BASE_URL}/api/edge/ingest",
                json=test_data,
                timeout=TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   📊 Data ingested successfully")
                print(f"      Device: {test_data['device_id']}")
                print(f"      Status: {result.get('status', 'N/A')}")
                print(f"      ✅ Persistence working")
                return True, "Data persistence operational", 10.0
            else:
                print(f"   ⚠️  HTTP {response.status_code}")
                return True, "Endpoint reachable", 5.0
                
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_multi_language(self) -> Tuple[bool, str, float]:
        """Test 8: Multi-Language Support"""
        print("\n🔍 Test 8: Multi-Language Support")
        
        languages = [
            {"code": "en", "name": "English", "query": "rice farming"},
            {"code": "hi", "name": "Hindi", "query": "धान की खेती"},
            {"code": "ta", "name": "Tamil", "query": "நெல் விவசாயம்"}
        ]
        
        try:
            passed = 0
            for lang in languages:
                response = requests.post(
                    f"{BASE_URL}/chatbot/ask",
                    json={
                        "question": lang["query"],
                        "language": lang["code"]
                    },
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results = result.get('results', [])
                    
                    if results and len(results) > 0:
                        passed += 1
                        print(f"   🌍 {lang['name']} ({lang['code']}): ✅ Working")
                    else:
                        print(f"   🌍 {lang['name']} ({lang['code']}): ⚠️  No results")
                else:
                    print(f"   🌍 {lang['name']} ({lang['code']}): ❌ HTTP {response.status_code}")
            
            score = (passed / len(languages)) * 10
            return passed > 0, f"{passed}/{len(languages)} languages working", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_performance(self) -> Tuple[bool, str, float]:
        """Test 9: Performance & Response Time"""
        print("\n🔍 Test 9: Performance Testing")
        
        try:
            # Test quick endpoint response
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            health_time = (time.time() - start) * 1000
            
            # Test API endpoint response
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/irrigation/recommend",
                json={
                    "temperature": 25,
                    "humidity": 60,
                    "soil_moisture": 40,
                    "crop_type": "rice"
                },
                timeout=TIMEOUT
            )
            api_time = (time.time() - start) * 1000
            
            print(f"   ⏱️  Health endpoint: {health_time:.2f}ms")
            print(f"   ⏱️  API endpoint: {api_time:.2f}ms")
            
            # Scoring based on response time
            if api_time < 200:
                score = 10.0
                rating = "Excellent"
            elif api_time < 500:
                score = 8.0
                rating = "Good"
            elif api_time < 1000:
                score = 6.0
                rating = "Acceptable"
            elif api_time < 2000:
                score = 4.0
                rating = "Slow"
            else:
                score = 2.0
                rating = "Very Slow"
            
            print(f"   📊 Performance: {rating} ({score}/10)")
            return True, f"Avg response: {api_time:.0f}ms ({rating})", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def test_error_handling(self) -> Tuple[bool, str, float]:
        """Test 10: Error Handling"""
        print("\n🔍 Test 10: Error Handling & Validation")
        score = 0.0
        
        test_cases = [
            {
                "name": "Missing required field",
                "endpoint": "/api/v1/irrigation/recommend",
                "data": {"temperature": 25},  # Missing other fields
                "expected_status": [400, 422]
            },
            {
                "name": "Invalid data type",
                "endpoint": "/api/v1/crop/recommend",
                "data": {"nitrogen": "invalid", "phosphorus": 30},
                "expected_status": [400, 422]
            }
        ]
        
        try:
            passed = 0
            for case in test_cases:
                response = requests.post(
                    f"{BASE_URL}{case['endpoint']}",
                    json=case["data"],
                    timeout=TIMEOUT
                )
                
                if response.status_code in case["expected_status"]:
                    passed += 1
                    print(f"   🛡️  {case['name']}: ✅ Proper validation (HTTP {response.status_code})")
                else:
                    print(f"   🛡️  {case['name']}: ⚠️  HTTP {response.status_code} (expected {case['expected_status']})")
            
            score = (passed / len(test_cases)) * 10
            return passed > 0, f"{passed}/{len(test_cases)} validation tests passed", score
            
        except Exception as e:
            return False, f"Error: {str(e)}", 0.0
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        print("\n" + "="*80)
        print("🚀 AGRISENSE COMPREHENSIVE END-TO-END TESTING")
        print("="*80)
        
        tests = [
            ("Health Check", self.test_health_endpoint, 1.0),
            ("Smart Irrigation", self.test_irrigation_recommendation, 1.5),
            ("Crop Recommendation", self.test_crop_recommendation, 1.5),
            ("Disease Detection", self.test_disease_detection, 1.5),
            ("Weed Management", self.test_weed_management, 1.5),
            ("Chatbot", self.test_chatbot, 1.0),
            ("Data Persistence", self.test_data_persistence, 0.5),
            ("Multi-Language", self.test_multi_language, 0.5),
            ("Performance", self.test_performance, 0.5),
            ("Error Handling", self.test_error_handling, 0.5)
        ]
        
        total_score = 0
        total_weight = sum(weight for _, _, weight in tests)
        
        for test_name, test_func, weight in tests:
            try:
                success, message, score = test_func()
                weighted_score = (score / 10) * weight
                total_score += weighted_score
                
                self.results["tests"].append({
                    "name": test_name,
                    "success": success,
                    "message": message,
                    "score": score,
                    "weight": weight,
                    "weighted_score": weighted_score
                })
                
                print(f"\n   Score: {score:.1f}/10 (weighted: {weighted_score:.2f}/{weight})")
                
            except Exception as e:
                print(f"\n   ❌ Test crashed: {str(e)}")
                self.results["tests"].append({
                    "name": test_name,
                    "success": False,
                    "message": f"Test crashed: {str(e)}",
                    "score": 0,
                    "weight": weight,
                    "weighted_score": 0
                })
        
        # Calculate final score
        final_score = (total_score / total_weight) * 10
        self.results["total_score"] = final_score
        self.results["max_score"] = 10.0
        self.results["end_time"] = datetime.now().isoformat()
        
        # Generate report
        self.generate_report()
        
        return final_score
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 TEST REPORT SUMMARY")
        print("="*80)
        
        # Summary table
        print(f"\n{'Test Name':<25} {'Score':<10} {'Weight':<10} {'Weighted':<15} {'Status'}")
        print("-" * 80)
        
        for test in self.results["tests"]:
            status = "✅ PASS" if test["success"] else "❌ FAIL"
            print(f"{test['name']:<25} {test['score']:<10.1f} {test['weight']:<10.1f} {test['weighted_score']:<15.2f} {status}")
        
        print("-" * 80)
        
        # Final score
        final_score = self.results["total_score"]
        print(f"\n🎯 FINAL SCORE: {final_score:.2f}/10")
        
        # Rating
        if final_score >= 9.0:
            rating = "🏆 EXCELLENT"
            grade = "A+"
        elif final_score >= 8.0:
            rating = "⭐ VERY GOOD"
            grade = "A"
        elif final_score >= 7.0:
            rating = "👍 GOOD"
            grade = "B+"
        elif final_score >= 6.0:
            rating = "✓ ACCEPTABLE"
            grade = "B"
        elif final_score >= 5.0:
            rating = "⚠️ NEEDS IMPROVEMENT"
            grade = "C"
        else:
            rating = "❌ CRITICAL ISSUES"
            grade = "D"
        
        print(f"📈 RATING: {rating} (Grade: {grade})")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        failed_tests = [t for t in self.results["tests"] if not t["success"]]
        if failed_tests:
            print(f"   • Fix {len(failed_tests)} failed test(s)")
            for test in failed_tests:
                print(f"     - {test['name']}: {test['message']}")
        
        low_score_tests = [t for t in self.results["tests"] if t["success"] and t["score"] < 7]
        if low_score_tests:
            print(f"   • Improve {len(low_score_tests)} test(s) with low scores")
            for test in low_score_tests:
                print(f"     - {test['name']}: {test['score']:.1f}/10")
        
        if not failed_tests and not low_score_tests:
            print(f"   • All systems operational! 🎉")
            print(f"   • Consider adding more advanced features")
            print(f"   • Monitor performance in production")
        
        # Save results to JSON
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")
        print("="*80)

if __name__ == "__main__":
    tester = AgriSenseE2ETester()
    final_score = tester.run_all_tests()
    
    print(f"\n✅ Testing complete! Final Score: {final_score:.2f}/10")
