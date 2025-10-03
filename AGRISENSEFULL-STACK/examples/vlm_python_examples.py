"""
Python Examples for AgriSense VLM API
Complete working examples for disease detection and weed management
"""

import requests
import json
from pathlib import Path
from typing import Dict, List, Optional


# Configuration
API_BASE_URL = "http://localhost:8004/api/vlm"
API_TIMEOUT = 30  # seconds


class AgriSenseVLMClient:
    """Client for AgriSense VLM API"""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    def health_check(self) -> Dict:
        """Check VLM system health"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    def list_crops(self, category: Optional[str] = None) -> Dict:
        """List all supported crops"""
        params = {"category": category} if category else {}
        response = requests.get(
            f"{self.base_url}/crops",
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_crop_info(self, crop_name: str) -> Dict:
        """Get detailed crop information"""
        response = requests.get(
            f"{self.base_url}/crops/{crop_name}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_disease_library(self, crop_name: str) -> Dict:
        """Get all diseases for a crop"""
        response = requests.get(
            f"{self.base_url}/crops/{crop_name}/diseases",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def get_weed_library(self, crop_name: str) -> Dict:
        """Get all weeds for a crop"""
        response = requests.get(
            f"{self.base_url}/crops/{crop_name}/weeds",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_disease(
        self,
        image_path: str,
        crop_name: str,
        expected_diseases: Optional[List[str]] = None,
        include_cost: bool = False
    ) -> Dict:
        """Analyze plant disease from image"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'crop_name': crop_name,
                'include_cost': str(include_cost).lower()
            }
            if expected_diseases:
                data['expected_diseases'] = ','.join(expected_diseases)
            
            response = requests.post(
                f"{self.base_url}/analyze/disease",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    def analyze_weeds(
        self,
        image_path: str,
        crop_name: str,
        growth_stage: Optional[str] = None,
        preferred_control: Optional[str] = None,
        include_cost: bool = False
    ) -> Dict:
        """Analyze field weeds from image"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'crop_name': crop_name,
                'include_cost': str(include_cost).lower()
            }
            if growth_stage:
                data['growth_stage'] = growth_stage
            if preferred_control:
                data['preferred_control'] = preferred_control
            
            response = requests.post(
                f"{self.base_url}/analyze/weed",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    def analyze_comprehensive(
        self,
        plant_image_path: str,
        field_image_path: str,
        crop_name: str,
        growth_stage: Optional[str] = None,
        include_cost: bool = False
    ) -> Dict:
        """Comprehensive analysis (disease + weeds)"""
        with open(plant_image_path, 'rb') as pf, open(field_image_path, 'rb') as ff:
            files = {
                'plant_image': pf,
                'field_image': ff
            }
            data = {
                'crop_name': crop_name,
                'include_cost': str(include_cost).lower()
            }
            if growth_stage:
                data['growth_stage'] = growth_stage
            
            response = requests.post(
                f"{self.base_url}/analyze/comprehensive",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()


# ============================================================================
# Example 1: Health Check and System Status
# ============================================================================

def example_health_check():
    """Example: Check VLM system health"""
    print("=" * 60)
    print("Example 1: Health Check")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        health = client.health_check()
        print(f"✅ VLM Status: {health['status']}")
        print(f"📦 Version: {health['vlm_version']}")
        print(f"🌾 Supported Crops: {health['supported_crops']}")
        print(f"🔧 ML Enabled: {health['ml_enabled']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")


# ============================================================================
# Example 2: List Crops and Get Information
# ============================================================================

def example_list_crops():
    """Example: List all crops and get details"""
    print("\n" + "=" * 60)
    print("Example 2: List Crops")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        # List all crops
        crops_data = client.list_crops()
        print(f"\n📊 Total Crops: {crops_data['total_crops']}")
        print(f"📂 Categories: {list(crops_data['categories'].keys())}")
        print(f"\n🌾 Available Crops:")
        for crop in crops_data['crops'][:10]:  # Show first 10
            print(f"   • {crop}")
        
        # List cereal crops only
        cereals = client.list_crops(category="cereal")
        print(f"\n🌾 Cereal Crops: {cereals['crops']}")
        
        # Get detailed info for rice
        rice_info = client.get_crop_info("rice")
        print(f"\n🔍 Rice Details:")
        print(f"   Scientific Name: {rice_info['scientific_name']}")
        print(f"   Growth Stages: {', '.join(rice_info['growth_stages'][:3])}...")
        print(f"   Common Diseases: {', '.join(rice_info['common_diseases'][:2])}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# Example 3: Disease Analysis
# ============================================================================

def example_disease_analysis(image_path: str):
    """Example: Analyze plant disease"""
    print("\n" + "=" * 60)
    print("Example 3: Disease Analysis")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        # Analyze disease with cost estimation
        result = client.analyze_disease(
            image_path=image_path,
            crop_name="rice",
            expected_diseases=["Blast Disease", "Bacterial Leaf Blight"],
            include_cost=True
        )
        
        print(f"\n🌾 Crop: {result['crop_name']}")
        print(f"🦠 Disease: {result.get('disease_name', 'None detected')}")
        print(f"📊 Confidence: {result['confidence']:.1%}")
        print(f"⚠️  Severity: {result['severity']}")
        print(f"📏 Affected Area: {result['affected_area_percentage']:.1f}%")
        
        if result.get('urgent_action_required'):
            print(f"🚨 URGENT ACTION REQUIRED!")
        
        print(f"\n💊 Treatment Recommendations:")
        for i, treatment in enumerate(result['treatment_recommendations'][:3], 1):
            print(f"   {i}. {treatment}")
        
        print(f"\n🛡️  Prevention Tips:")
        for i, tip in enumerate(result['prevention_tips'][:3], 1):
            print(f"   {i}. {tip}")
        
        if 'cost_estimate' in result:
            cost = result['cost_estimate']
            print(f"\n💰 Cost Estimate:")
            print(f"   Fungicide: ₹{cost.get('fungicide_cost', 0):.0f}/acre")
            print(f"   Labor: ₹{cost.get('labor_cost', 0):.0f}/acre")
            print(f"   Total: ₹{cost['total_per_acre']:.0f}/acre")
        
        if 'success_probability' in result:
            print(f"\n✅ Success Probability: {result['success_probability']:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# Example 4: Weed Analysis
# ============================================================================

def example_weed_analysis(image_path: str):
    """Example: Analyze field weeds"""
    print("\n" + "=" * 60)
    print("Example 4: Weed Analysis")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        # Analyze weeds with organic preference
        result = client.analyze_weeds(
            image_path=image_path,
            crop_name="wheat",
            growth_stage="tillering",
            preferred_control="organic",
            include_cost=True
        )
        
        print(f"\n🌾 Crop: {result['crop_name']}")
        print(f"🌿 Weeds Identified: {', '.join(result['weeds_identified'])}")
        print(f"📊 Infestation Level: {result['infestation_level']}")
        print(f"📏 Coverage: {result['weed_coverage_percentage']:.1f}%")
        print(f"⚠️  Priority: {result['priority_level']}")
        print(f"📉 Yield Impact: {result['estimated_yield_impact']}")
        
        print(f"\n🛠️  Control Recommendations:")
        for method, recommendations in result['control_recommendations'].items():
            print(f"\n   {method.upper()} Method:")
            for rec in recommendations[:2]:
                print(f"      • {rec}")
        
        if 'best_control_timing' in result:
            print(f"\n⏰ Best Timing:")
            for timing in result['best_control_timing'][:2]:
                print(f"   • {timing}")
        
        if 'cost_estimate' in result:
            cost = result['cost_estimate']
            print(f"\n💰 Cost Estimate:")
            print(f"   Control Method: ₹{cost.get('control_method_cost', 0):.0f}/acre")
            print(f"   Labor: ₹{cost.get('labor_cost', 0):.0f}/acre")
            print(f"   Total: ₹{cost['total_per_acre']:.0f}/acre")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# Example 5: Comprehensive Analysis
# ============================================================================

def example_comprehensive_analysis(plant_image: str, field_image: str):
    """Example: Comprehensive analysis (disease + weeds)"""
    print("\n" + "=" * 60)
    print("Example 5: Comprehensive Analysis")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        result = client.analyze_comprehensive(
            plant_image_path=plant_image,
            field_image_path=field_image,
            crop_name="rice",
            growth_stage="vegetative",
            include_cost=True
        )
        
        print(f"\n🌾 Crop: {result['crop_name']}")
        print(f"📊 Analysis Type: {result['analysis_type']}")
        
        # Disease summary
        disease = result.get('disease_analysis', {})
        if disease:
            print(f"\n🦠 Disease Analysis:")
            print(f"   Disease: {disease.get('disease_name', 'None')}")
            print(f"   Severity: {disease.get('severity', 'N/A')}")
        
        # Weed summary
        weed = result.get('weed_analysis', {})
        if weed:
            print(f"\n🌿 Weed Analysis:")
            print(f"   Infestation: {weed.get('infestation_level', 'N/A')}")
            print(f"   Coverage: {weed.get('weed_coverage_percentage', 0):.1f}%")
        
        # Combined recommendations
        if 'combined_recommendations' in result:
            print(f"\n💡 Combined Recommendations:")
            for i, rec in enumerate(result['combined_recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        
        # Priority actions
        if 'priority_actions' in result:
            print(f"\n⚡ Priority Actions:")
            for action in result['priority_actions'][:3]:
                print(f"   {action}")
        
        # Time to action
        if 'estimated_time_to_action' in result:
            print(f"\n⏰ Time to Action: {result['estimated_time_to_action']}")
        
        # Total cost
        if 'cost_estimate' in result:
            total = result['cost_estimate'].get('total_per_acre', 0)
            print(f"\n💰 Total Estimated Cost: ₹{total:.0f}/acre")
        
        # Success probability
        if 'success_probability' in result:
            print(f"✅ Overall Success Probability: {result['success_probability']:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# Example 6: Disease and Weed Libraries
# ============================================================================

def example_libraries():
    """Example: Get disease and weed libraries"""
    print("\n" + "=" * 60)
    print("Example 6: Disease & Weed Libraries")
    print("=" * 60)
    
    client = AgriSenseVLMClient()
    
    try:
        # Get rice diseases
        diseases = client.get_disease_library("rice")
        print(f"\n🦠 Rice Diseases ({len(diseases['diseases'])} total):")
        for disease in diseases['diseases'][:3]:
            print(f"\n   📋 {disease['name']}")
            print(f"      Symptoms: {', '.join(disease['symptoms'][:2])}...")
            print(f"      Treatment: {disease['treatment'][:80]}...")
        
        # Get wheat weeds
        weeds = client.get_weed_library("wheat")
        print(f"\n\n🌿 Wheat Weeds ({len(weeds['weeds'])} total):")
        for weed in weeds['weeds'][:3]:
            print(f"\n   📋 {weed['name']}")
            print(f"      Type: {weed['characteristics'].get('type', 'N/A')}")
            methods = list(weed['control_methods'].keys())
            print(f"      Control Methods: {', '.join(methods)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("\n" + "🌾" * 30)
    print("AgriSense VLM API - Python Examples")
    print("🌾" * 30)
    
    # Example 1: Health check
    example_health_check()
    
    # Example 2: List crops
    example_list_crops()
    
    # Example 6: Libraries
    example_libraries()
    
    # For image-based examples, uncomment and provide image paths:
    # example_disease_analysis("path/to/diseased_plant.jpg")
    # example_weed_analysis("path/to/weedy_field.jpg")
    # example_comprehensive_analysis("path/to/plant.jpg", "path/to/field.jpg")
    
    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)
    print("\n💡 To run image analysis examples:")
    print("   1. Take photos of plants/fields")
    print("   2. Uncomment the image example calls above")
    print("   3. Provide correct image paths")
    print("   4. Run this script again")
    print("\n")
