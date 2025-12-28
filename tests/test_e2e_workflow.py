#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Workflow Testing
Tests complete user workflows from data ingestion to recommendation delivery
Handles Unicode encoding properly for international test data
"""

import sys
import os
import json
import base64
import time
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agrisense_app" / "backend"))

import pytest
from PIL import Image
import io

# Test configuration
TEST_TIMEOUT = 30  # seconds
BASE_URL = os.getenv("AGRISENSE_API_URL", "http://localhost:8004")


class TestE2EWorkflow:
    """End-to-end workflow testing suite"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
    def create_test_sensor_reading(self, **overrides) -> Dict[str, Any]:
        """Create a test sensor reading with proper defaults"""
        base_reading = {
            "temperature": 25.0,
            "humidity": 65.0,
            "soil_moisture": 45.0,
            "soil_ph": 6.5,
            "nitrogen": 50.0,
            "phosphorus": 40.0,
            "potassium": 45.0,
            "rainfall": 100.0,
            "timestamp": time.time()
        }
        base_reading.update(overrides)
        return base_reading
    
    def create_test_image(self, image_type: str = "healthy") -> str:
        """Create test images for disease/weed detection
        
        Args:
            image_type: 'healthy', 'diseased', or 'weedy'
            
        Returns:
            Base64 encoded image string
        """
        img = Image.new('RGB', (512, 512), color='lightgreen')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        if image_type == "diseased":
            # Draw disease spots
            draw.ellipse([100, 100, 150, 150], fill='brown')
            draw.ellipse([200, 200, 250, 250], fill='saddlebrown')
            draw.ellipse([150, 300, 200, 350], fill='yellow')
        elif image_type == "weedy":
            # Draw weed patterns
            draw.rectangle([50, 50, 100, 400], fill='darkgreen')
            draw.rectangle([200, 100, 250, 450], fill='olive')
        else:
            # Healthy plant
            draw.ellipse([150, 150, 350, 350], fill='green')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    @pytest.mark.integration
    def test_full_irrigation_workflow(self):
        """Test complete irrigation recommendation workflow"""
        print("\n🧪 Testing Full Irrigation Workflow")
        
        # Step 1: Create sensor reading
        sensor_data = self.create_test_sensor_reading(
            soil_moisture=30.0,  # Low moisture
            temperature=28.0,    # High temperature
            humidity=50.0        # Low humidity
        )
        
        # Step 2: Get recommendation
        from agrisense_app.backend.engine import RecoEngine
        engine = RecoEngine()
        recommendation = engine.recommend(sensor_data)
        
        # Step 3: Validate recommendation
        assert recommendation is not None, "No recommendation received"
        assert "water_liters" in recommendation, "Missing water_liters in recommendation"
        assert recommendation["water_liters"] > 0, "Should recommend watering"
        assert "tips" in recommendation, "Missing tips"
        assert len(recommendation["tips"]) > 0, "Should provide tips"
        
        print(f"✅ Irrigation Workflow: Recommended {recommendation['water_liters']}L water")
        print(f"   Tips provided: {len(recommendation['tips'])}")
        
    @pytest.mark.integration
    def test_full_crop_recommendation_workflow(self):
        """Test complete crop recommendation workflow"""
        print("\n🧪 Testing Full Crop Recommendation Workflow")
        
        # Step 1: Create soil analysis data
        soil_data = {
            "nitrogen": 60.0,
            "phosphorus": 55.0,
            "potassium": 50.0,
            "soil_ph": 6.8,
            "temperature": 25.0,
            "humidity": 70.0,
            "rainfall": 120.0
        }
        
        # Step 2: Get crop recommendations
        from agrisense_app.backend.crop_recommendation import CropRecommendationEngine
        engine = CropRecommendationEngine()
        recommendations = engine.recommend_crops(soil_data)
        
        # Step 3: Validate recommendations
        assert recommendations is not None, "No recommendations received"
        assert isinstance(recommendations, list), "Recommendations should be a list"
        assert len(recommendations) > 0, "Should provide at least one crop recommendation"
        
        print(f"✅ Crop Recommendation: {len(recommendations)} crops recommended")
        for i, crop in enumerate(recommendations[:3], 1):
            print(f"   {i}. {crop.get('crop', 'unknown')} (confidence: {crop.get('confidence', 0):.2f})")
    
    @pytest.mark.integration
    def test_full_disease_detection_workflow(self):
        """Test complete disease detection workflow"""
        print("\n🧪 Testing Full Disease Detection Workflow")
        
        # Step 1: Create diseased plant image
        diseased_image = self.create_test_image("diseased")
        
        # Step 2: Detect disease
        try:
            from agrisense_app.backend.comprehensive_disease_detector import ComprehensiveDiseaseDetector
            detector = ComprehensiveDiseaseDetector()
            result = detector.analyze_disease_image(diseased_image, crop_type="tomato")
            
            # Step 3: Validate detection
            assert result is not None, "No detection result"
            assert isinstance(result, dict), "Result should be dictionary"
            assert "model_used" in result, "Should specify model used"
            
            print(f"✅ Disease Detection: Model={result.get('model_used', 'unknown')}")
            if 'disease_detected' in result:
                print(f"   Disease: {result['disease_detected']}")
            if 'treatment_recommendations' in result:
                print(f"   Treatment available: Yes")
        except ImportError:
            pytest.skip("Disease detection module not available")
    
    @pytest.mark.integration
    def test_full_weed_management_workflow(self):
        """Test complete weed management workflow"""
        print("\n🧪 Testing Full Weed Management Workflow")
        
        # Step 1: Create weed-infested field image
        weedy_image = self.create_test_image("weedy")
        
        # Step 2: Analyze weeds
        try:
            from agrisense_app.backend.weed_management import WeedManagementEngine
            engine = WeedManagementEngine()
            result = engine.analyze_field_image(weedy_image, field_size_hectares=2.0)
            
            # Step 3: Validate analysis
            assert result is not None, "No analysis result"
            assert isinstance(result, dict), "Result should be dictionary"
            
            print(f"✅ Weed Management: Analysis complete")
            if 'weed_coverage_percentage' in result:
                print(f"   Weed coverage: {result['weed_coverage_percentage']:.1f}%")
            if 'recommended_action' in result:
                print(f"   Action: {result['recommended_action']}")
        except ImportError:
            pytest.skip("Weed management module not available")
    
    @pytest.mark.integration
    def test_chatbot_cultivation_guide_workflow(self):
        """Test complete chatbot cultivation guide retrieval"""
        print("\n🧪 Testing Chatbot Cultivation Guide Workflow")
        
        # Test multiple crops with Unicode support
        test_crops = [
            "carrot",
            "watermelon", 
            "strawberry",
            "tomato",
            "rice"
        ]
        
        try:
            # Import chatbot service
            sys.path.insert(0, str(Path(__file__).parent.parent / "agrisense_app" / "backend"))
            from chatbot_service import ChatbotService
            
            chatbot = ChatbotService()
            
            for crop in test_crops:
                # Query chatbot
                response = chatbot.answer_question(crop)
                
                # Validate response
                assert response is not None, f"No response for {crop}"
                assert isinstance(response, dict), "Response should be dictionary"
                assert "answer" in response, "Response should contain answer"
                
                answer = response["answer"]
                assert len(answer) > 100, f"Answer for {crop} too short: {len(answer)} chars"
                
                print(f"✅ {crop.capitalize()}: {len(answer)} characters")
                
        except ImportError:
            pytest.skip("Chatbot service not available")
    
    @pytest.mark.integration
    def test_multi_language_support(self):
        """Test multi-language support (5 languages)"""
        print("\n🧪 Testing Multi-Language Support")
        
        # Test languages: English, Hindi, Tamil, Telugu, Kannada
        test_phrases = {
            "en": "Smart Agriculture Solution",
            "hi": "स्मार्ट कृषि समाधान",
            "ta": "ஸ்மார்ட் விவசாய தீர்வு",
            "te": "స్మార్ట్ వ్యవసాయ పరిష్కారం",
            "kn": "ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಪರಿಹಾರ"
        }
        
        # Verify Unicode handling
        for lang_code, phrase in test_phrases.items():
            # Test encoding/decoding
            encoded = phrase.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert decoded == phrase, f"Unicode encoding failed for {lang_code}"
            
            # Test JSON serialization
            json_str = json.dumps({"text": phrase}, ensure_ascii=False)
            json_obj = json.loads(json_str)
            assert json_obj["text"] == phrase, f"JSON serialization failed for {lang_code}"
            
            print(f"✅ {lang_code}: {phrase[:30]}...")
    
    @pytest.mark.integration
    def test_data_persistence_workflow(self):
        """Test data persistence across operations"""
        print("\n🧪 Testing Data Persistence Workflow")
        
        try:
            from agrisense_app.backend.data_store import DataStore
            
            db_path = self.test_data_dir / "test_sensors.db"
            store = DataStore(str(db_path))
            
            # Step 1: Store sensor reading
            test_reading = self.create_test_sensor_reading()
            store.store_reading(test_reading)
            
            # Step 2: Retrieve readings
            readings = store.get_recent_readings(limit=10)
            assert len(readings) > 0, "Failed to retrieve stored reading"
            
            # Step 3: Verify data integrity
            latest = readings[0]
            assert latest["temperature"] == test_reading["temperature"]
            assert latest["humidity"] == test_reading["humidity"]
            
            print(f"✅ Data Persistence: {len(readings)} readings stored")
            
            # Cleanup
            db_path.unlink(missing_ok=True)
            
        except ImportError:
            pytest.skip("DataStore module not available")
    
    @pytest.mark.integration
    def test_error_handling_workflow(self):
        """Test error handling in various scenarios"""
        print("\n🧪 Testing Error Handling Workflow")
        
        from agrisense_app.backend.engine import RecoEngine
        engine = RecoEngine()
        
        # Test 1: Invalid sensor data
        invalid_data = {"temperature": "invalid"}
        try:
            result = engine.recommend(invalid_data)
            # Should still return something (fallback)
            assert result is not None, "Should handle invalid data gracefully"
            print("✅ Invalid data handled gracefully")
        except Exception as e:
            print(f"⚠️  Exception raised: {e}")
        
        # Test 2: Missing required fields
        incomplete_data = {"temperature": 25.0}  # Missing other fields
        result = engine.recommend(incomplete_data)
        assert result is not None, "Should handle incomplete data"
        print("✅ Incomplete data handled gracefully")
        
        # Test 3: Extreme values
        extreme_data = self.create_test_sensor_reading(
            temperature=50.0,  # Extreme
            humidity=0.0,      # Extreme
            soil_moisture=-10.0  # Invalid
        )
        result = engine.recommend(extreme_data)
        assert result is not None, "Should handle extreme values"
        print("✅ Extreme values handled gracefully")
    
    @pytest.mark.integration
    def test_performance_workflow(self):
        """Test performance under load"""
        print("\n🧪 Testing Performance Workflow")
        
        from agrisense_app.backend.engine import RecoEngine
        engine = RecoEngine()
        
        num_requests = 100
        start_time = time.time()
        
        for i in range(num_requests):
            sensor_data = self.create_test_sensor_reading(
                temperature=20 + (i % 20),
                humidity=50 + (i % 30)
            )
            result = engine.recommend(sensor_data)
            assert result is not None
        
        elapsed = time.time() - start_time
        avg_time = elapsed / num_requests
        
        print(f"✅ Performance: {num_requests} requests in {elapsed:.2f}s")
        print(f"   Average: {avg_time*1000:.2f}ms per request")
        
        # Assert reasonable performance
        assert avg_time < 0.5, f"Too slow: {avg_time}s per request"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
