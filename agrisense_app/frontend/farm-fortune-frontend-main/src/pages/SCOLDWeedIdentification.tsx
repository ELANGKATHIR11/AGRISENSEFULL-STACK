import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, Camera, Loader2, AlertCircle, CheckCircle2, Leaf, Target } from 'lucide-react';

interface WeedDetection {
  weed_name: string;
  confidence: number;
  coverage_percentage: number;
  location_description?: string;
}

interface AnalysisResult {
  success: boolean;
  analysis_method: string;
  detections: WeedDetection[];
  recommendations: string[];
  overall_infestation: string;
  total_coverage: number;
  confidence: number;
}

export default function SCOLDWeedIdentification() {
  const { t } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [cropType, setCropType] = useState('wheat');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSelectedImage(reader.result as string);
        setResult(null);
        setError(null);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      // Extract base64 data from data URL
      const base64Data = selectedImage.split(',')[1];

      const response = await fetch('http://localhost:8004/api/weed/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          crop_type: cropType,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
      console.error('Weed identification error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getInfestationColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'high':
      case 'severe':
        return 'text-red-600 bg-red-50';
      case 'medium':
      case 'moderate':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
      case 'minimal':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('scold_weed_title', 'SCOLD Weed Identification')}
        </h1>
        <p className="text-gray-600">
          {t('scold_weed_subtitle', 'AI-powered weed detection and crop field analysis')}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Image Upload */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Camera className="w-5 h-5 mr-2" />
              {t('scold_upload_field', 'Upload Field Image')}
            </h2>

            {/* Image Preview */}
            <div className="mb-4">
              {selectedImage ? (
                <img
                  src={selectedImage}
                  alt="Selected field"
                  className="w-full h-64 object-cover rounded-lg border-2 border-gray-200"
                />
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                  <div className="text-center">
                    <Upload className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                    <p className="text-gray-500">{t('scold_no_image', 'No image selected')}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Upload Button */}
            <label className="block">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <div className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer text-center transition-colors">
                {t('scold_choose_file', 'Choose Image File')}
              </div>
            </label>

            {/* Crop Type Selection */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('scold_crop_type', 'Crop Type')}
              </label>
              <select
                value={cropType}
                onChange={(e) => setCropType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="wheat">{t('crop_wheat', 'Wheat')}</option>
                <option value="rice">{t('crop_rice', 'Rice')}</option>
                <option value="corn">{t('crop_corn', 'Corn')}</option>
                <option value="soybean">{t('crop_soybean', 'Soybean')}</option>
                <option value="cotton">{t('crop_cotton', 'Cotton')}</option>
                <option value="sugarcane">{t('crop_sugarcane', 'Sugarcane')}</option>
              </select>
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={!selectedImage || isAnalyzing}
              className="w-full mt-4 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center font-semibold transition-colors"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  {t('scold_analyzing', 'Analyzing...')}
                </>
              ) : (
                t('scold_identify_button', 'Identify Weeds')
              )}
            </button>
          </div>
        </div>

        {/* Right Panel - Results */}
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800">{t('scold_error', 'Error')}</h3>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Analysis Method Badge */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{t('scold_analysis_method', 'Analysis Method')}</span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {result.analysis_method === 'scold_vlm' ? 'SCOLD VLM' : result.analysis_method}
                  </span>
                </div>
              </div>

              {/* Infestation Overview */}
              <div className="bg-white rounded-lg shadow-md p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{t('scold_infestation_level', 'Infestation Level')}</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getInfestationColor(result.overall_infestation)}`}>
                      {result.overall_infestation}
                    </span>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{t('scold_total_coverage', 'Total Weed Coverage')}</span>
                      <span>{result.total_coverage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          result.total_coverage > 30 ? 'bg-red-600' : 
                          result.total_coverage > 15 ? 'bg-yellow-600' : 
                          'bg-green-600'
                        }`}
                        style={{ width: `${Math.min(result.total_coverage, 100)}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{t('scold_confidence', 'Confidence')}</span>
                      <span>{(result.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${result.confidence * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Detected Weeds */}
              {result.detections && result.detections.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-4">
                  <h3 className="font-semibold mb-3 flex items-center">
                    <Leaf className="w-5 h-5 mr-2" />
                    {t('scold_detected_weeds', 'Detected Weed Species')}
                  </h3>
                  <div className="space-y-3">
                    {result.detections.map((detection, index) => (
                      <div key={index} className="border-l-4 border-orange-500 pl-4 py-2">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-gray-900">{detection.weed_name}</span>
                          <span className="text-sm text-gray-600">
                            {(detection.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                          <Target className="w-3 h-3 mr-1" />
                          <span>{t('scold_coverage', 'Coverage')}: {detection.coverage_percentage.toFixed(1)}%</span>
                        </div>
                        {detection.location_description && (
                          <p className="text-xs text-gray-500 mt-1">{detection.location_description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-4">
                  <h3 className="font-semibold mb-3">{t('scold_control_recommendations', 'Control Recommendations')}</h3>
                  <ul className="space-y-2">
                    {result.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start">
                        <CheckCircle2 className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.detections.length === 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <CheckCircle2 className="w-5 h-5 text-green-600 mr-3" />
                    <p className="text-green-800 font-medium">
                      {t('scold_no_weeds', 'No weeds detected - Field appears clean!')}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {!result && !error && !isAnalyzing && (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <Leaf className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">
                {t('scold_upload_field_prompt', 'Upload a field image and click identify to detect weeds')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
