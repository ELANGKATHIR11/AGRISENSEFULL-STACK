import React, { useState, useRef } from 'react';
import { Camera, Upload, Leaf, Bug, AlertCircle, CheckCircle, Info, Sprout } from 'lucide-react';

const TOP_48_CROPS = [
  'Rice', 'Wheat', 'Maize', 'Jowar', 'Bajra', 'Ragi', 'Barley', 'Chickpea', 'Pigeon Pea',
  'Green Gram', 'Black Gram', 'Lentil', 'Kidney Bean', 'Soybean', 'Groundnut', 'Sesame',
  'Mustard', 'Sunflower', 'Safflower', 'Cotton', 'Jute', 'Sugarcane', 'Potato', 'Onion',
  'Tomato', 'Brinjal', 'Cabbage', 'Cauliflower', 'Okra', 'Chili', 'Garlic', 'Ginger',
  'Turmeric', 'Coriander', 'Cumin', 'Tea', 'Coffee', 'Rubber', 'Coconut', 'Arecanut',
  'Cashew', 'Mango', 'Banana', 'Citrus', 'Apple', 'Grapes', 'Papaya', 'Guava'
];

export default function CropDiseaseWeedDetector() {
  const [selectedCrop, setSelectedCrop] = useState('');
  const [imagePreview, setImagePreview] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(file);
      setAnalysis(null);
      setError(null);
    }
  };

  const analyzeImage = async () => {
    if (!imageFile || !selectedCrop) {
      setError('Please select a crop and upload an image');
      return;
    }

    setAnalyzing(true);
    setError(null);

    try {
      const base64Image = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        };
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsDataURL(imageFile);
      });

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 4000,
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'image',
                  source: {
                    type: 'base64',
                    media_type: imageFile.type,
                    data: base64Image,
                  }
                },
                {
                  type: 'text',
                  text: `You are an expert agricultural pathologist and agronomist specializing in Indian crops. Analyze this image of a ${selectedCrop} plant/field.

IMPORTANT: Respond ONLY with a valid JSON object. DO NOT include any text outside the JSON structure, including backticks or markdown formatting.

Provide a comprehensive analysis in the following JSON format:
{
  "cropHealth": "healthy|diseased|infested|multiple_issues",
  "confidence": "high|medium|low",
  "diseases": [
    {
      "name": "Disease name",
      "severity": "mild|moderate|severe",
      "symptoms": "Visible symptoms",
      "cause": "Pathogen/cause",
      "spread": "How it spreads",
      "treatment": "Treatment recommendations"
    }
  ],
  "weeds": [
    {
      "name": "Weed species name",
      "type": "broadleaf|grass|sedge",
      "coverage": "light|moderate|heavy",
      "impact": "Competition impact",
      "control": "Control methods"
    }
  ],
  "pests": [
    {
      "name": "Pest name if visible",
      "damage": "Type of damage",
      "control": "Control measures"
    }
  ],
  "nutritionalDeficiency": {
    "present": true/false,
    "details": "Description if present"
  },
  "recommendations": [
    "Immediate action recommendation 1",
    "Immediate action recommendation 2",
    "Prevention recommendation"
  ],
  "preventiveMeasures": [
    "Long-term prevention measure 1",
    "Long-term prevention measure 2"
  ],
  "additionalNotes": "Any other relevant observations"
}

If no diseases or weeds are detected, use empty arrays. Be specific to Indian agricultural context and ${selectedCrop} cultivation practices. Include both organic and chemical treatment options where applicable.`
                }
              ]
            }
          ]
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      let responseText = data.content[0].text;
      
      // Strip markdown code blocks if present
      responseText = responseText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const analysisResult = JSON.parse(responseText);
      setAnalysis(analysisResult);
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to analyze image. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'diseased': return 'text-red-600';
      case 'infested': return 'text-orange-600';
      case 'multiple_issues': return 'text-red-700';
      default: return 'text-gray-600';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'mild': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'moderate': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'severe': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Leaf className="w-12 h-12 text-green-600" />
            <h1 className="text-4xl font-bold text-green-800">Crop Disease & Weed Detector</h1>
          </div>
          <p className="text-lg text-green-700">AI-Powered Agricultural Diagnostics for 48 Major Indian Crops</p>
        </div>

        {/* Main Container */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Upload & Controls */}
          <div className="space-y-6">
            {/* Crop Selection */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <Sprout className="inline w-5 h-5 mr-2" />
                Select Crop Type
              </label>
              <select
                value={selectedCrop}
                onChange={(e) => setSelectedCrop(e.target.value)}
                className="w-full px-4 py-3 border-2 border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Choose a crop...</option>
                {TOP_48_CROPS.map((crop) => (
                  <option key={crop} value={crop}>{crop}</option>
                ))}
              </select>
            </div>

            {/* Image Upload */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                <Camera className="inline w-5 h-5 mr-2" />
                Upload Plant/Field Image
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all flex items-center justify-center gap-2 font-semibold"
              >
                <Upload className="w-5 h-5" />
                Choose Image
              </button>

              {imagePreview && (
                <div className="mt-4">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="w-full h-64 object-cover rounded-lg border-4 border-green-200"
                  />
                </div>
              )}
            </div>

            {/* Analyze Button */}
            {imagePreview && selectedCrop && (
              <button
                onClick={analyzeImage}
                disabled={analyzing}
                className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-bold text-lg shadow-lg"
              >
                {analyzing ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Analyzing Image...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Bug className="w-6 h-6" />
                    Analyze for Diseases & Weeds
                  </span>
                )}
              </button>
            )}

            {error && (
              <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-800">{error}</p>
              </div>
            )}
          </div>

          {/* Right Panel - Analysis Results */}
          <div className="space-y-6">
            {analysis && (
              <>
                {/* Overall Health Status */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                    <CheckCircle className="w-7 h-7" />
                    Health Status
                  </h2>
                  <div className="space-y-2">
                    <p className={`text-xl font-semibold ${getHealthColor(analysis.cropHealth)}`}>
                      Status: {analysis.cropHealth.replace('_', ' ').toUpperCase()}
                    </p>
                    <p className="text-gray-600">
                      Confidence: <span className="font-semibold">{analysis.confidence}</span>
                    </p>
                  </div>
                </div>

                {/* Diseases */}
                {analysis.diseases && analysis.diseases.length > 0 && (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-4 text-red-700 flex items-center gap-2">
                      <Bug className="w-7 h-7" />
                      Detected Diseases ({analysis.diseases.length})
                    </h2>
                    <div className="space-y-4">
                      {analysis.diseases.map((disease, idx) => (
                        <div key={idx} className={`border-2 rounded-lg p-4 ${getSeverityColor(disease.severity)}`}>
                          <h3 className="font-bold text-lg mb-2">{disease.name}</h3>
                          <div className="space-y-2 text-sm">
                            <p><strong>Severity:</strong> {disease.severity}</p>
                            <p><strong>Symptoms:</strong> {disease.symptoms}</p>
                            <p><strong>Cause:</strong> {disease.cause}</p>
                            <p><strong>Spread:</strong> {disease.spread}</p>
                            <div className="mt-3 pt-3 border-t">
                              <p className="font-semibold mb-1">Treatment:</p>
                              <p>{disease.treatment}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Weeds */}
                {analysis.weeds && analysis.weeds.length > 0 && (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-4 text-orange-700 flex items-center gap-2">
                      <Leaf className="w-7 h-7" />
                      Detected Weeds ({analysis.weeds.length})
                    </h2>
                    <div className="space-y-4">
                      {analysis.weeds.map((weed, idx) => (
                        <div key={idx} className="border-2 border-orange-300 rounded-lg p-4 bg-orange-50">
                          <h3 className="font-bold text-lg mb-2 text-orange-900">{weed.name}</h3>
                          <div className="space-y-2 text-sm text-orange-900">
                            <p><strong>Type:</strong> {weed.type}</p>
                            <p><strong>Coverage:</strong> {weed.coverage}</p>
                            <p><strong>Impact:</strong> {weed.impact}</p>
                            <div className="mt-3 pt-3 border-t border-orange-300">
                              <p className="font-semibold mb-1">Control Methods:</p>
                              <p>{weed.control}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Pests */}
                {analysis.pests && analysis.pests.length > 0 && (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-4 text-purple-700 flex items-center gap-2">
                      <Bug className="w-7 h-7" />
                      Detected Pests ({analysis.pests.length})
                    </h2>
                    <div className="space-y-4">
                      {analysis.pests.map((pest, idx) => (
                        <div key={idx} className="border-2 border-purple-300 rounded-lg p-4 bg-purple-50">
                          <h3 className="font-bold text-lg mb-2 text-purple-900">{pest.name}</h3>
                          <div className="space-y-2 text-sm text-purple-900">
                            <p><strong>Damage:</strong> {pest.damage}</p>
                            <div className="mt-3 pt-3 border-t border-purple-300">
                              <p className="font-semibold mb-1">Control:</p>
                              <p>{pest.control}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Nutritional Deficiency */}
                {analysis.nutritionalDeficiency?.present && (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-4 text-yellow-700 flex items-center gap-2">
                      <Info className="w-7 h-7" />
                      Nutritional Deficiency
                    </h2>
                    <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-4">
                      <p className="text-yellow-900">{analysis.nutritionalDeficiency.details}</p>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-2xl font-bold mb-4 text-blue-700 flex items-center gap-2">
                    <CheckCircle className="w-7 h-7" />
                    Immediate Recommendations
                  </h2>
                  <ul className="space-y-2">
                    {analysis.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex gap-3 items-start">
                        <span className="text-blue-600 font-bold mt-1">•</span>
                        <span className="text-gray-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Preventive Measures */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-2xl font-bold mb-4 text-green-700 flex items-center gap-2">
                    <Leaf className="w-7 h-7" />
                    Preventive Measures
                  </h2>
                  <ul className="space-y-2">
                    {analysis.preventiveMeasures.map((measure, idx) => (
                      <li key={idx} className="flex gap-3 items-start">
                        <span className="text-green-600 font-bold mt-1">•</span>
                        <span className="text-gray-700">{measure}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Additional Notes */}
                {analysis.additionalNotes && (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-4 text-gray-700 flex items-center gap-2">
                      <Info className="w-7 h-7" />
                      Additional Observations
                    </h2>
                    <p className="text-gray-700">{analysis.additionalNotes}</p>
                  </div>
                )}
              </>
            )}

            {!analysis && !analyzing && (
              <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                <Leaf className="w-16 h-16 text-green-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">
                  Select a crop and upload an image to begin analysis
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <Info className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <p className="font-semibold mb-2">Tips for Best Results:</p>
              <ul className="space-y-1 ml-4">
                <li>• Capture clear, well-lit images of affected plant parts</li>
                <li>• Include close-ups of symptoms (spots, discoloration, wilting)</li>
                <li>• For weeds, capture the entire plant including leaves and stems</li>
                <li>• Multiple angles help improve diagnosis accuracy</li>
                <li>• This AI analysis is for guidance only - consult agricultural experts for severe cases</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}