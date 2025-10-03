"""
Integration tests for VLM API endpoints
Tests REST API routes for disease detection and weed management
"""

import pytest
import sys
from pathlib import Path
import io
from PIL import Image
from fastapi.testclient import TestClient

# Add backend to path
backend_path = Path(__file__).parent.parent / "agrisense_app" / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def client():
    """Create FastAPI test client"""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_plant_image():
    """Create a sample plant image for disease analysis"""
    img = Image.new('RGB', (640, 480), color=(50, 150, 50))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return ('plant.jpg', img_bytes, 'image/jpeg')


@pytest.fixture
def sample_field_image():
    """Create a sample field image for weed analysis"""
    img = Image.new('RGB', (800, 600), color=(60, 160, 60))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return ('field.jpg', img_bytes, 'image/jpeg')


class TestVLMAPIHealth:
    """Test VLM API health and status endpoints"""
    
    def test_vlm_health_endpoint(self, client):
        """Test VLM health check endpoint"""
        response = client.get("/api/vlm/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "vlm_version" in data
        assert "supported_crops" in data
    
    def test_vlm_status_endpoint(self, client):
        """Test VLM detailed status endpoint"""
        response = client.get("/api/vlm/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "vlm_engine" in data
        assert "disease_detector" in data
        assert "weed_detector" in data
        assert "crop_database" in data


class TestCropEndpoints:
    """Test crop information endpoints"""
    
    def test_list_all_crops(self, client):
        """Test listing all crops"""
        response = client.get("/api/vlm/crops")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_crops" in data
        assert "categories" in data
        assert "crops" in data
        assert data["total_crops"] > 0
        assert isinstance(data["crops"], list)
    
    def test_list_crops_by_category(self, client):
        """Test filtering crops by category"""
        response = client.get("/api/vlm/crops?category=cereal")
        
        assert response.status_code == 200
        data = response.json()
        assert "crops" in data
        # Should have cereal crops
        assert any("rice" in crop.lower() or "wheat" in crop.lower() 
                  for crop in data["crops"])
    
    def test_get_crop_info(self, client):
        """Test getting specific crop information"""
        response = client.get("/api/vlm/crops/rice")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"].lower() == "rice (paddy)"
        assert "scientific_name" in data
        assert "category" in data
        assert "growth_stages" in data
        assert "optimal_conditions" in data
        assert "common_diseases" in data
        assert "common_weeds" in data
    
    def test_get_crop_info_not_found(self, client):
        """Test getting info for non-existent crop"""
        response = client.get("/api/vlm/crops/invalid_crop_12345")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_get_disease_library(self, client):
        """Test getting disease library for a crop"""
        response = client.get("/api/vlm/crops/rice/diseases")
        
        assert response.status_code == 200
        data = response.json()
        assert data["crop_name"].lower() == "rice (paddy)"
        assert "diseases" in data
        assert len(data["diseases"]) > 0
        
        # Check disease structure
        disease = data["diseases"][0]
        assert "name" in disease
        assert "symptoms" in disease
        assert "treatment" in disease
        assert "prevention" in disease
    
    def test_get_weed_library(self, client):
        """Test getting weed library for a crop"""
        response = client.get("/api/vlm/crops/wheat/weeds")
        
        assert response.status_code == 200
        data = response.json()
        assert data["crop_name"].lower() == "wheat"
        assert "weeds" in data
        assert len(data["weeds"]) > 0
        
        # Check weed structure
        weed = data["weeds"][0]
        assert "name" in weed
        assert "characteristics" in weed
        assert "control_methods" in weed


class TestDiseaseAnalysisEndpoint:
    """Test disease analysis endpoint"""
    
    def test_analyze_disease_basic(self, client, sample_plant_image):
        """Test basic disease analysis"""
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": sample_plant_image},
            data={"crop_name": "rice"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "disease"
        assert data["crop_name"] == "Rice (Paddy)"
        assert "disease_name" in data
        assert "confidence" in data
        assert "severity" in data
        assert "treatment_recommendations" in data
        assert "prevention_tips" in data
    
    def test_analyze_disease_with_cost(self, client, sample_plant_image):
        """Test disease analysis with cost estimation"""
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": sample_plant_image},
            data={
                "crop_name": "wheat",
                "include_cost": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cost_estimate" in data
        assert "total_per_acre" in data["cost_estimate"]
        assert "currency" in data["cost_estimate"]
        assert data["cost_estimate"]["currency"] == "INR"
    
    def test_analyze_disease_with_expected_diseases(self, client, sample_plant_image):
        """Test disease analysis with expected diseases"""
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": sample_plant_image},
            data={
                "crop_name": "rice",
                "expected_diseases": "Blast Disease,Bacterial Leaf Blight"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "disease"
    
    def test_analyze_disease_missing_image(self, client):
        """Test disease analysis without image"""
        response = client.post(
            "/api/vlm/analyze/disease",
            data={"crop_name": "rice"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_disease_invalid_crop(self, client, sample_plant_image):
        """Test disease analysis with invalid crop"""
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": sample_plant_image},
            data={"crop_name": "invalid_crop_12345"}
        )
        
        assert response.status_code in [400, 404, 500]  # Error response


class TestWeedAnalysisEndpoint:
    """Test weed analysis endpoint"""
    
    def test_analyze_weed_basic(self, client, sample_field_image):
        """Test basic weed analysis"""
        response = client.post(
            "/api/vlm/analyze/weed",
            files={"image": sample_field_image},
            data={"crop_name": "wheat"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "weed"
        assert data["crop_name"] == "Wheat"
        assert "weeds_identified" in data
        assert "infestation_level" in data
        assert "control_recommendations" in data
        assert "estimated_yield_impact" in data
    
    def test_analyze_weed_with_preferences(self, client, sample_field_image):
        """Test weed analysis with control preferences"""
        response = client.post(
            "/api/vlm/analyze/weed",
            files={"image": sample_field_image},
            data={
                "crop_name": "maize",
                "growth_stage": "vegetative",
                "preferred_control": "organic"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "control_recommendations" in data
        # Should prioritize organic methods
        assert "organic" in data["control_recommendations"]
    
    def test_analyze_weed_with_cost(self, client, sample_field_image):
        """Test weed analysis with cost estimation"""
        response = client.post(
            "/api/vlm/analyze/weed",
            files={"image": sample_field_image},
            data={
                "crop_name": "rice",
                "include_cost": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cost_estimate" in data
        assert "total_per_acre" in data["cost_estimate"]
    
    def test_analyze_weed_missing_image(self, client):
        """Test weed analysis without image"""
        response = client.post(
            "/api/vlm/analyze/weed",
            data={"crop_name": "wheat"}
        )
        
        assert response.status_code == 422  # Validation error


class TestComprehensiveAnalysis:
    """Test comprehensive analysis endpoint"""
    
    def test_comprehensive_analysis(self, client, sample_plant_image, sample_field_image):
        """Test comprehensive analysis with both images"""
        response = client.post(
            "/api/vlm/analyze/comprehensive",
            files={
                "plant_image": sample_plant_image,
                "field_image": sample_field_image
            },
            data={"crop_name": "rice"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "comprehensive"
        assert "disease_analysis" in data
        assert "weed_analysis" in data
        assert "combined_recommendations" in data
        assert "priority_actions" in data
    
    def test_comprehensive_analysis_with_cost(self, client, sample_plant_image, sample_field_image):
        """Test comprehensive analysis with cost estimation"""
        response = client.post(
            "/api/vlm/analyze/comprehensive",
            files={
                "plant_image": sample_plant_image,
                "field_image": sample_field_image
            },
            data={
                "crop_name": "wheat",
                "include_cost": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "cost_estimate" in data
        assert "success_probability" in data
    
    def test_comprehensive_analysis_missing_images(self, client):
        """Test comprehensive analysis without images"""
        response = client.post(
            "/api/vlm/analyze/comprehensive",
            data={"crop_name": "maize"}
        )
        
        assert response.status_code == 422  # Validation error


class TestAPIPerformance:
    """Test API performance and limits"""
    
    def test_large_image_handling(self, client):
        """Test handling of large images"""
        # Create a larger image
        img = Image.new('RGB', (4000, 3000), color=(50, 150, 50))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)
        
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": ('large.jpg', img_bytes, 'image/jpeg')},
            data={"crop_name": "rice"}
        )
        
        # Should handle or reject gracefully
        assert response.status_code in [200, 413, 422]
    
    def test_response_time_disease(self, client, sample_plant_image):
        """Test disease analysis response time"""
        import time
        start = time.time()
        
        response = client.post(
            "/api/vlm/analyze/disease",
            files={"image": sample_plant_image},
            data={"crop_name": "wheat"}
        )
        
        duration = time.time() - start
        
        assert response.status_code == 200
        # Should complete in reasonable time (< 10 seconds)
        assert duration < 10.0
    
    def test_response_time_weed(self, client, sample_field_image):
        """Test weed analysis response time"""
        import time
        start = time.time()
        
        response = client.post(
            "/api/vlm/analyze/weed",
            files={"image": sample_field_image},
            data={"crop_name": "maize"}
        )
        
        duration = time.time() - start
        
        assert response.status_code == 200
        # Should complete in reasonable time (< 10 seconds)
        assert duration < 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
