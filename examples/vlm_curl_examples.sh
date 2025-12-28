#!/bin/bash
# AgriSense VLM API - cURL Examples
# Complete working examples for disease detection and weed management

# Configuration
API_BASE="http://localhost:8004/api/vlm"

echo "=================================================="
echo "AgriSense VLM API - cURL Examples"
echo "=================================================="

# ============================================================================
# Example 1: Health Check
# ============================================================================

echo ""
echo "=========================================="
echo "Example 1: Health Check"
echo "=========================================="
echo ""

curl -s "${API_BASE}/health" | jq '.'

# ============================================================================
# Example 2: List All Crops
# ============================================================================

echo ""
echo "=========================================="
echo "Example 2: List All Crops"
echo "=========================================="
echo ""

curl -s "${API_BASE}/crops" | jq '{
  total_crops: .total_crops,
  categories: .categories,
  first_5_crops: .crops[:5]
}'

# ============================================================================
# Example 3: List Crops by Category
# ============================================================================

echo ""
echo "=========================================="
echo "Example 3: List Cereal Crops"
echo "=========================================="
echo ""

curl -s "${API_BASE}/crops?category=cereal" | jq '.crops'

# ============================================================================
# Example 4: Get Crop Information
# ============================================================================

echo ""
echo "=========================================="
echo "Example 4: Get Rice Information"
echo "=========================================="
echo ""

curl -s "${API_BASE}/crops/rice" | jq '{
  name: .name,
  scientific_name: .scientific_name,
  category: .category,
  growth_stages: .growth_stages,
  optimal_conditions: .optimal_conditions,
  common_diseases: .common_diseases,
  common_weeds: .common_weeds
}'

# ============================================================================
# Example 5: Get Disease Library
# ============================================================================

echo ""
echo "=========================================="
echo "Example 5: Get Rice Disease Library"
echo "=========================================="
echo ""

curl -s "${API_BASE}/crops/rice/diseases" | jq '{
  crop_name: .crop_name,
  total_diseases: (.diseases | length),
  diseases: [.diseases[] | {
    name: .name,
    symptoms: .symptoms[:2],
    causes: .causes
  }][:2]
}'

# ============================================================================
# Example 6: Get Weed Library
# ============================================================================

echo ""
echo "=========================================="
echo "Example 6: Get Wheat Weed Library"
echo "=========================================="
echo ""

curl -s "${API_BASE}/crops/wheat/weeds" | jq '{
  crop_name: .crop_name,
  total_weeds: (.weeds | length),
  weeds: [.weeds[] | {
    name: .name,
    type: .characteristics.type,
    control_methods: (.control_methods | keys)
  }][:2]
}'

# ============================================================================
# Example 7: Analyze Disease (requires image file)
# ============================================================================

echo ""
echo "=========================================="
echo "Example 7: Analyze Plant Disease"
echo "=========================================="
echo ""
echo "To run this example, provide an image file:"
echo ""
echo "curl -X POST '${API_BASE}/analyze/disease' \\"
echo "  -F 'image=@/path/to/plant_image.jpg' \\"
echo "  -F 'crop_name=rice' \\"
echo "  -F 'include_cost=true' | jq '.'"
echo ""

# If you have a test image, uncomment and modify:
# IMAGE_PATH="./test_images/diseased_plant.jpg"
# if [ -f "$IMAGE_PATH" ]; then
#   curl -X POST "${API_BASE}/analyze/disease" \
#     -F "image=@${IMAGE_PATH}" \
#     -F "crop_name=rice" \
#     -F "include_cost=true" | jq '{
#       crop_name: .crop_name,
#       disease_name: .disease_name,
#       confidence: .confidence,
#       severity: .severity,
#       affected_area_percentage: .affected_area_percentage,
#       treatment_recommendations: .treatment_recommendations[:2],
#       cost_estimate: .cost_estimate
#     }'
# fi

# ============================================================================
# Example 8: Analyze Disease with Expected Diseases
# ============================================================================

echo ""
echo "=========================================="
echo "Example 8: Analyze with Expected Diseases"
echo "=========================================="
echo ""
echo "To run this example:"
echo ""
echo "curl -X POST '${API_BASE}/analyze/disease' \\"
echo "  -F 'image=@/path/to/plant_image.jpg' \\"
echo "  -F 'crop_name=rice' \\"
echo "  -F 'expected_diseases=Blast Disease,Bacterial Leaf Blight' \\"
echo "  -F 'include_cost=true' | jq '.'"
echo ""

# ============================================================================
# Example 9: Analyze Weeds (requires image file)
# ============================================================================

echo ""
echo "=========================================="
echo "Example 9: Analyze Field Weeds"
echo "=========================================="
echo ""
echo "To run this example:"
echo ""
echo "curl -X POST '${API_BASE}/analyze/weed' \\"
echo "  -F 'image=@/path/to/field_image.jpg' \\"
echo "  -F 'crop_name=wheat' \\"
echo "  -F 'growth_stage=tillering' \\"
echo "  -F 'include_cost=true' | jq '.'"
echo ""

# If you have a test image, uncomment and modify:
# FIELD_IMAGE="./test_images/weedy_field.jpg"
# if [ -f "$FIELD_IMAGE" ]; then
#   curl -X POST "${API_BASE}/analyze/weed" \
#     -F "image=@${FIELD_IMAGE}" \
#     -F "crop_name=wheat" \
#     -F "growth_stage=tillering" \
#     -F "include_cost=true" | jq '{
#       crop_name: .crop_name,
#       weeds_identified: .weeds_identified,
#       infestation_level: .infestation_level,
#       weed_coverage_percentage: .weed_coverage_percentage,
#       control_recommendations: .control_recommendations,
#       cost_estimate: .cost_estimate
#     }'
# fi

# ============================================================================
# Example 10: Analyze Weeds with Organic Preference
# ============================================================================

echo ""
echo "=========================================="
echo "Example 10: Analyze Weeds (Organic Only)"
echo "=========================================="
echo ""
echo "To run this example:"
echo ""
echo "curl -X POST '${API_BASE}/analyze/weed' \\"
echo "  -F 'image=@/path/to/field_image.jpg' \\"
echo "  -F 'crop_name=maize' \\"
echo "  -F 'preferred_control=organic' \\"
echo "  -F 'include_cost=true' | jq '.control_recommendations.organic'"
echo ""

# ============================================================================
# Example 11: Comprehensive Analysis (requires two images)
# ============================================================================

echo ""
echo "=========================================="
echo "Example 11: Comprehensive Analysis"
echo "=========================================="
echo ""
echo "To run this example:"
echo ""
echo "curl -X POST '${API_BASE}/analyze/comprehensive' \\"
echo "  -F 'plant_image=@/path/to/plant_closeup.jpg' \\"
echo "  -F 'field_image=@/path/to/field_view.jpg' \\"
echo "  -F 'crop_name=rice' \\"
echo "  -F 'growth_stage=vegetative' \\"
echo "  -F 'include_cost=true' | jq '.'"
echo ""

# If you have test images, uncomment and modify:
# PLANT_IMG="./test_images/plant.jpg"
# FIELD_IMG="./test_images/field.jpg"
# if [ -f "$PLANT_IMG" ] && [ -f "$FIELD_IMG" ]; then
#   curl -X POST "${API_BASE}/analyze/comprehensive" \
#     -F "plant_image=@${PLANT_IMG}" \
#     -F "field_image=@${FIELD_IMG}" \
#     -F "crop_name=rice" \
#     -F "growth_stage=vegetative" \
#     -F "include_cost=true" | jq '{
#       crop_name: .crop_name,
#       analysis_type: .analysis_type,
#       disease_analysis: {
#         disease_name: .disease_analysis.disease_name,
#         severity: .disease_analysis.severity
#       },
#       weed_analysis: {
#         infestation_level: .weed_analysis.infestation_level,
#         coverage: .weed_analysis.weed_coverage_percentage
#       },
#       priority_actions: .priority_actions,
#       cost_estimate: .cost_estimate,
#       success_probability: .success_probability
#     }'
# fi

# ============================================================================
# Example 12: System Status
# ============================================================================

echo ""
echo "=========================================="
echo "Example 12: System Status"
echo "=========================================="
echo ""

curl -s "${API_BASE}/status" | jq '.'

# ============================================================================
# Complete Example with Error Handling
# ============================================================================

echo ""
echo "=========================================="
echo "Example 13: Complete Workflow"
echo "=========================================="
echo ""

# Step 1: Check health
echo "Step 1: Checking system health..."
HEALTH=$(curl -s "${API_BASE}/health")
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" == "healthy" ]; then
    echo "✅ System is healthy"
    
    # Step 2: List crops
    echo ""
    echo "Step 2: Listing available crops..."
    CROPS=$(curl -s "${API_BASE}/crops" | jq -r '.crops[]' | head -5)
    echo "Available crops (first 5):"
    echo "$CROPS"
    
    # Step 3: Get crop details
    echo ""
    echo "Step 3: Getting rice details..."
    curl -s "${API_BASE}/crops/rice" | jq '{
      name: .name,
      diseases_count: (.common_diseases | length),
      weeds_count: (.common_weeds | length)
    }'
    
    # Step 4: Get disease library
    echo ""
    echo "Step 4: Getting disease library for rice..."
    curl -s "${API_BASE}/crops/rice/diseases" | jq '{
      total_diseases: (.diseases | length),
      disease_names: [.diseases[].name][:3]
    }'
    
    echo ""
    echo "✅ Workflow completed successfully!"
else
    echo "❌ System is not healthy: $STATUS"
fi

# ============================================================================
# PowerShell Alternative Commands
# ============================================================================

echo ""
echo "=================================================="
echo "PowerShell Alternative Commands"
echo "=================================================="
echo ""

cat << 'EOF'
# For PowerShell users, use these commands instead:

# Health check
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/health" | ConvertTo-Json

# List crops
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops" | ConvertTo-Json

# Get crop info
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/crops/rice" | ConvertTo-Json

# Analyze disease
$form = @{
    image = Get-Item -Path "C:\path\to\plant.jpg"
    crop_name = "rice"
    include_cost = "true"
}
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/disease" -Method Post -Form $form | ConvertTo-Json

# Analyze weeds
$form = @{
    image = Get-Item -Path "C:\path\to\field.jpg"
    crop_name = "wheat"
    growth_stage = "tillering"
    preferred_control = "organic"
    include_cost = "true"
}
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/weed" -Method Post -Form $form | ConvertTo-Json

# Comprehensive analysis
$form = @{
    plant_image = Get-Item -Path "C:\path\to\plant.jpg"
    field_image = Get-Item -Path "C:\path\to\field.jpg"
    crop_name = "rice"
    include_cost = "true"
}
Invoke-RestMethod -Uri "http://localhost:8004/api/vlm/analyze/comprehensive" -Method Post -Form $form | ConvertTo-Json
EOF

echo ""
echo "=================================================="
echo "✅ All examples completed!"
echo "=================================================="
echo ""
echo "📝 Notes:"
echo "  • Replace image paths with your actual files"
echo "  • Install jq for JSON formatting: apt-get install jq"
echo "  • For PowerShell, use the commands shown above"
echo "  • API must be running on http://localhost:8004"
echo ""
