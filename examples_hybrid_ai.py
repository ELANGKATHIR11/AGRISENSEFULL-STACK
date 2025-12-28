"""
Hybrid Agricultural AI - Usage Examples

Demonstrates how to use the offline-capable hybrid LLM+VLM system
for agricultural analysis and advice.
"""

import base64
import json
from pathlib import Path

# Direct Python import (when backend is running)
try:
    from agrisense_app.backend.hybrid_agri_ai import (
        HybridAgriAI,
        AnalysisType,
        analyze_farm_image,
        ask_agricultural_question,
        get_hybrid_ai
    )
    DIRECT_IMPORT = True
except ImportError:
    DIRECT_IMPORT = False
    print("⚠️  Running in API-only mode (backend not in PYTHONPATH)")

# HTTP API access (always works when backend running)
import requests


# ============================================================================
# Example 1: Direct Python Usage (when imported)
# ============================================================================

def example_1_direct_python():
    """Example 1: Using Python API directly"""
    print("\n" + "="*70)
    print("Example 1: Direct Python API")
    print("="*70)
    
    if not DIRECT_IMPORT:
        print("⏭️  Skipped (requires backend in PYTHONPATH)")
        return
    
    # Initialize hybrid AI
    ai = HybridAgriAI()
    
    # Get status
    status = ai.get_status()
    print(f"🤖 Hybrid AI Available: {status['hybrid_ai_available']}")
    print(f"🧠 Phi LLM: {status['phi_llm_available']}")
    print(f"👁️  SCOLD VLM: {status['scold_vlm_available']}")
    
    # Ask a question
    print("\n📝 Asking: 'What fertilizer is best for tomatoes?'")
    result = ai.analyze_text(
        query="What fertilizer is best for tomatoes?",
        context={"crop": "tomato", "soil_type": "clay"}
    )
    print(f"✅ Response: {result.response[:200]}...")
    
    # Multimodal analysis (requires image)
    # result = ai.analyze_multimodal(
    #     image_data="path/to/diseased_leaf.jpg",
    #     text_query="What disease is this?",
    #     context={"crop": "tomato"}
    # )


# ============================================================================
# Example 2: HTTP API Usage (always works)
# ============================================================================

def example_2_http_api():
    """Example 2: Using HTTP API"""
    print("\n" + "="*70)
    print("Example 2: HTTP API")
    print("="*70)
    
    base_url = "http://localhost:8004/api/hybrid"
    
    # Check health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hybrid AI Status: {data['status']}")
            print(f"   Phi LLM: {data['components']['phi_llm']}")
            print(f"   SCOLD VLM: {data['components']['scold_vlm']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect - is backend running on port 8004?")
        return
    
    # Text query
    print("\n📝 Asking: 'How do I prevent blight in potatoes?'")
    response = requests.post(
        f"{base_url}/text",
        json={
            "query": "How do I prevent blight in potatoes?",
            "context": {"crop": "potato", "season": "monsoon"},
            "use_history": True
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            answer = data["response"]
            print(f"✅ Response: {answer[:300]}...")
            
            recommendations = data.get("recommendations", [])
            if recommendations:
                print(f"\n💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec}")


# ============================================================================
# Example 3: Image Upload Analysis
# ============================================================================

def example_3_image_upload():
    """Example 3: Upload image for analysis"""
    print("\n" + "="*70)
    print("Example 3: Image Upload Analysis")
    print("="*70)
    
    # Create a sample 1x1 pixel image (replace with real image)
    sample_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    print("📸 Analyzing sample image (replace with real agricultural image)...")
    
    response = requests.post(
        "http://localhost:8004/api/hybrid/analyze",
        json={
            "image_base64": sample_image_b64,
            "query": "What's wrong with this plant?",
            "context": {
                "crop": "tomato",
                "location": "greenhouse",
                "weather": "humid"
            }
        },
        timeout=45
    )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Analysis Type: {data['analysis_type']}")
            print(f"✅ Confidence: {data['confidence_score']:.2f}")
            
            synthesis = data.get("synthesis", "")
            if synthesis:
                print(f"\n📝 Synthesis: {synthesis[:250]}...")
            
            steps = data.get("actionable_steps", [])
            if steps:
                print(f"\n🎯 Actionable Steps ({len(steps)}):")
                for i, step in enumerate(steps[:5], 1):
                    print(f"   {i}. {step}")
            
            # Visual analysis details
            visual = data.get("visual_analysis")
            if visual:
                print(f"\n👁️  Visual Analysis:")
                print(f"   Detections: {len(visual.get('detections', []))}")
                print(f"   Confidence: {visual.get('confidence', 0):.2f}")
                print(f"   Severity: {visual.get('severity', 'N/A')}")


# ============================================================================
# Example 4: Conversation with History
# ============================================================================

def example_4_conversation():
    """Example 4: Multi-turn conversation"""
    print("\n" + "="*70)
    print("Example 4: Conversation with History")
    print("="*70)
    
    base_url = "http://localhost:8004/api/hybrid"
    
    questions = [
        "I want to grow organic vegetables",
        "Which crops are easiest for beginners?",
        "What soil preparation do I need?"
    ]
    
    print("💬 Starting conversation...\n")
    
    for i, question in enumerate(questions, 1):
        print(f"Q{i}: {question}")
        
        response = requests.post(
            f"{base_url}/text",
            json={
                "query": question,
                "use_history": True  # Maintains context
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                answer = data["response"][:200]
                print(f"A{i}: {answer}...\n")
    
    # Clear history when done
    print("🗑️  Clearing conversation history...")
    requests.post(f"{base_url}/history/clear", timeout=5)
    print("✅ History cleared")


# ============================================================================
# Example 5: Batch Analysis
# ============================================================================

def example_5_batch_analysis():
    """Example 5: Analyze multiple scenarios"""
    print("\n" + "="*70)
    print("Example 5: Batch Analysis")
    print("="*70)
    
    scenarios = [
        {
            "title": "Wheat Yellow Rust",
            "query": "My wheat has yellow spots on leaves",
            "context": {"crop": "wheat", "stage": "vegetative"}
        },
        {
            "title": "Rice Blast",
            "query": "Dark lesions appearing on rice leaves",
            "context": {"crop": "rice", "stage": "tillering"}
        },
        {
            "title": "Tomato Wilting",
            "query": "Tomato plants wilting despite watering",
            "context": {"crop": "tomato", "stage": "flowering"}
        }
    ]
    
    print(f"🔄 Analyzing {len(scenarios)} scenarios...\n")
    
    for scenario in scenarios:
        print(f"📋 {scenario['title']}")
        
        response = requests.post(
            "http://localhost:8004/api/hybrid/text",
            json={
                "query": scenario["query"],
                "context": scenario["context"],
                "use_history": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                # Extract key info
                answer = data["response"]
                recommendations = data.get("recommendations", [])
                
                # Simple diagnosis extraction (look for disease names)
                import re
                diseases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:disease|blight|rot|rust|wilt))', answer)
                
                if diseases:
                    print(f"   🦠 Likely: {', '.join(diseases[:2])}")
                
                if recommendations:
                    print(f"   💊 Treatment: {recommendations[0][:60]}...")
                
                print()


# ============================================================================
# Example 6: Real-time Field Monitoring Simulation
# ============================================================================

def example_6_field_monitoring():
    """Example 6: Simulate field monitoring system"""
    print("\n" + "="*70)
    print("Example 6: Field Monitoring Simulation")
    print("="*70)
    
    # Simulate sensor data + visual checks
    field_zones = [
        {
            "zone": "North Field",
            "sensor_data": {"soil_moisture": 35, "temperature": 28, "ph": 6.5},
            "observation": "Plants look healthy but some yellowing at edges"
        },
        {
            "zone": "South Field",
            "sensor_data": {"soil_moisture": 15, "temperature": 32, "ph": 7.2},
            "observation": "Significant wilting observed in afternoon"
        }
    ]
    
    print("🌾 Monitoring 2 field zones...\n")
    
    for zone_data in field_zones:
        print(f"📍 {zone_data['zone']}")
        print(f"   📊 Sensors: Moisture={zone_data['sensor_data']['soil_moisture']}%, Temp={zone_data['sensor_data']['temperature']}°C")
        
        # Query AI with sensor data and observation
        query = f"Observation: {zone_data['observation']}. Soil moisture is {zone_data['sensor_data']['soil_moisture']}%. What should I do?"
        
        response = requests.post(
            "http://localhost:8004/api/hybrid/text",
            json={
                "query": query,
                "context": {
                    "sensor_data": zone_data['sensor_data'],
                    "zone": zone_data['zone']
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                recommendations = data.get("recommendations", [])
                if recommendations:
                    print(f"   🎯 Action: {recommendations[0]}")
        
        print()


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("🌾 HYBRID AGRICULTURAL AI - USAGE EXAMPLES")
    print("="*70)
    print("\nThese examples demonstrate the offline-capable hybrid LLM+VLM system")
    print("combining Phi (language) and SCOLD (vision) for agricultural intelligence.")
    print("\n⚠️  Note: Replace sample images with real agricultural images for full testing")
    
    examples = [
        ("Direct Python API", example_1_direct_python),
        ("HTTP API", example_2_http_api),
        ("Image Upload", example_3_image_upload),
        ("Conversation History", example_4_conversation),
        ("Batch Analysis", example_5_batch_analysis),
        ("Field Monitoring", example_6_field_monitoring)
    ]
    
    for name, func in examples:
        try:
            func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Examples interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
    
    print("\n" + "="*70)
    print("✅ Examples completed!")
    print("="*70)
    print("\n💡 Tips:")
    print("   - Check API docs: http://localhost:8004/docs")
    print("   - Test with real images for better results")
    print("   - Monitor: Get-Job | Receive-Job (PowerShell)")
    print("   - Full test suite: python test_hybrid_ai.py")
    print()


if __name__ == "__main__":
    main()
