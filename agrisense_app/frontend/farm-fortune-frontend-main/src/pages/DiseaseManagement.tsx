import { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, Camera, AlertTriangle, CheckCircle, Info, Brain, BookOpen, Eye, Loader2, Target, TrendingUp } from "lucide-react";
import { toast } from "sonner";

interface DiseaseDetectionResult {
  primary_disease: string;
  confidence: number;
  severity: string;
  affected_area_percentage: number;
  recommended_treatments: Array<{
    treatment_type: string;
    product_name: string;
    application_rate: string;
    frequency: string;
    cost_per_acre: number;
  }>;
  prevention_tips: string[];
  economic_impact: {
    potential_yield_loss: number;
    treatment_cost_estimate: number;
    cost_benefit_ratio: number;
  };
  vlm_analysis?: {
    knowledge_matches: number;
    confidence_score: number;
    analysis_timestamp: string;
  };
}

interface SCOLDDetection {
  disease_name: string;
  confidence: number;
  severity: string;
  affected_area?: number;
}

interface SCOLDAnalysisResult {
  success: boolean;
  analysis_method: string;
  detections: SCOLDDetection[];
  recommendations: string[];
  overall_health: string;
  confidence: number;
}

const DiseaseManagement = () => {
  const { t } = useTranslation();
  
  // Standard detection state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<DiseaseDetectionResult | null>(null);
  const [cropType, setCropType] = useState("");
  const [growthStage, setGrowthStage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // SCOLD VLM detection state
  const [scoldImage, setScoldImage] = useState<string | null>(null);
  const [scoldCropType, setScoldCropType] = useState('tomato');
  const [isScoldAnalyzing, setIsScoldAnalyzing] = useState(false);
  const [scoldResult, setScoldResult] = useState<SCOLDAnalysisResult | null>(null);
  const [scoldError, setScoldError] = useState<string | null>(null);

  const cropOptions = [
    "tomato", "potato", "corn", "wheat", "rice", "soybean", "bean",
    "cotton", "apple", "grape", "citrus", "pepper", "cucumber"
  ];

  const growthStages = [
    "seedling", "vegetative", "flowering", "fruiting", "mature"
  ];

  // SCOLD VLM handlers
  const handleScoldImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setScoldImage(reader.result as string);
        setScoldResult(null);
        setScoldError(null);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleScoldAnalyze = async () => {
    if (!scoldImage) return;

    setIsScoldAnalyzing(true);
    setScoldError(null);

    try {
      const base64Data = scoldImage.split(',')[1];

      const response = await fetch('http://localhost:8004/api/disease/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_data: base64Data,
          crop_type: scoldCropType,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      setScoldResult(data);
      toast.success(t('scold_analysis_complete', 'SCOLD analysis completed!'));
    } catch (err) {
      setScoldError(err instanceof Error ? err.message : 'Analysis failed');
      toast.error(t('scold_error', 'Error analyzing image'));
      console.error('SCOLD detection error:', err);
    } finally {
      setIsScoldAnalyzing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'high':
      case 'severe':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
      case 'moderate':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
      case 'mild':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast.error("Image size must be less than 10MB");
        return;
      }
      
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage || !cropType) {
      toast.error("Please select an image and crop type");
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      // Convert image to base64
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64 = reader.result as string;
          const imageData = base64.split(',')[1]; // Remove data URL prefix

          // 🆕 Try SCOLD VLM first for advanced disease detection
          let detectionSuccess = false;
          try {
            const { detectDiseaseWithScold } = await import('../services/aiModels');
            toast.info("🔍 Using SCOLD VLM for advanced detection...");
            
            const scoldResponse = await detectDiseaseWithScold(imageData, cropType);
            
            if (scoldResponse.success && scoldResponse.detections.length > 0) {
              // Transform SCOLD response to match expected format
              const primaryDetection = scoldResponse.detections[0];
              const transformedData: DiseaseDetectionResult = {
                primary_disease: primaryDetection.disease,
                confidence: primaryDetection.confidence,
                severity: primaryDetection.severity || "medium",
                affected_area_percentage: primaryDetection.affected_area_percent || 0,
                recommended_treatments: primaryDetection.treatment ? [
                  {
                    treatment_type: "Immediate Action",
                    product_name: primaryDetection.treatment.immediate_actions.join(", "),
                    application_rate: "As directed",
                    frequency: "Once",
                    cost_per_acre: 0
                  },
                  {
                    treatment_type: "Organic Methods",
                    product_name: primaryDetection.treatment.organic_methods.join(", "),
                    application_rate: "As needed",
                    frequency: "Weekly",
                    cost_per_acre: 0
                  }
                ] : [],
                prevention_tips: primaryDetection.treatment?.preventive_measures || [],
                economic_impact: {
                  potential_yield_loss: primaryDetection.affected_area_percent || 0,
                  treatment_cost_estimate: 0,
                  cost_benefit_ratio: 0
                },
                vlm_analysis: {
                  knowledge_matches: scoldResponse.detections.length,
                  confidence_score: primaryDetection.confidence,
                  analysis_timestamp: scoldResponse.timestamp
                }
              };
              
              setResult(transformedData);
              toast.success("✅ SCOLD VLM analysis completed!");
              detectionSuccess = true;
            }
          } catch (scoldError) {
            console.info("SCOLD VLM unavailable, using fallback detection:", scoldError);
          }

          // Fallback to standard detection if SCOLD VLM fails
          if (!detectionSuccess) {
            toast.info("Using standard disease detection...");
            const response = await fetch(`${window.location.origin}/api/disease/detect`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                image_data: imageData,
                crop_type: cropType,
                field_info: {
                  growth_stage: growthStage || "unknown"
                }
              }),
            });

            if (!response.ok) {
              throw new Error(`Analysis failed: ${response.statusText}`);
            }

            const data = await response.json();
            setResult(data);
            toast.success("Disease analysis completed!");
          }
        } catch (error) {
          console.error("Analysis error:", error);
          toast.error("Failed to analyze image. Please try again.");
        } finally {
          setIsAnalyzing(false);
        }
      };
      
      reader.onerror = () => {
        console.error("File reading error");
        toast.error("Failed to read image file. Please try again.");
        setIsAnalyzing(false);
      };
      
      reader.readAsDataURL(selectedImage);
    } catch (error) {
      console.error("Upload error:", error);
      toast.error("Failed to process image. Please try again.");
      setIsAnalyzing(false);
    }
  };

  const getSeverityColorLegacy = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "low": return "bg-green-100 text-green-800 border-green-200";
      case "medium": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "high": return "bg-red-100 text-red-800 border-red-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "low": return <CheckCircle className="w-4 h-4" />;
      case "medium": return <Info className="w-4 h-4" />;
      case "high": return <AlertTriangle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          {t('nav_disease', 'Disease Management')}
        </h1>
        <p className="text-muted-foreground">
          Advanced AI-powered disease detection with multiple analysis methods
        </p>
      </div>

      <Tabs defaultValue="scold" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="scold" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            SCOLD VLM Detection
          </TabsTrigger>
          <TabsTrigger value="standard" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Standard Detection
          </TabsTrigger>
        </TabsList>

        {/* SCOLD VLM Tab */}
        <TabsContent value="scold" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* SCOLD Upload Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Camera className="w-5 h-5" />
                  {t('scold_upload_image', 'Upload Plant Image')}
                </CardTitle>
                <CardDescription>
                  {t('scold_disease_subtitle', 'AI-powered plant disease identification using vision models')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Image Preview */}
                <div className="mb-4">
                  {scoldImage ? (
                    <img
                      src={scoldImage}
                      alt="Selected plant"
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
                    onChange={handleScoldImageUpload}
                    className="hidden"
                  />
                  <div className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer text-center transition-colors">
                    {t('scold_choose_file', 'Choose Image File')}
                  </div>
                </label>

                {/* Crop Type Selection */}
                <div>
                  <Label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('scold_crop_type', 'Crop Type')}
                  </Label>
                  <Select value={scoldCropType} onValueChange={setScoldCropType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tomato">{t('crop_tomato', 'Tomato')}</SelectItem>
                      <SelectItem value="potato">{t('crop_potato', 'Potato')}</SelectItem>
                      <SelectItem value="rice">{t('crop_rice', 'Rice')}</SelectItem>
                      <SelectItem value="wheat">{t('crop_wheat', 'Wheat')}</SelectItem>
                      <SelectItem value="corn">{t('crop_corn', 'Corn')}</SelectItem>
                      <SelectItem value="cotton">{t('crop_cotton', 'Cotton')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Analyze Button */}
                <Button
                  onClick={handleScoldAnalyze}
                  disabled={!scoldImage || isScoldAnalyzing}
                  className="w-full"
                  size="lg"
                >
                  {isScoldAnalyzing ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {t('scold_analyzing', 'Analyzing...')}
                    </>
                  ) : (
                    t('scold_analyze_button', 'Analyze Disease')
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* SCOLD Results Section */}
            <div className="space-y-4">
              {scoldError && (
                <Alert variant="destructive">
                  <AlertTriangle className="w-5 h-5" />
                  <AlertDescription>{scoldError}</AlertDescription>
                </Alert>
              )}

              {scoldResult && (
                <div className="space-y-4">
                  {/* Analysis Method */}
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{t('scold_analysis_method', 'Analysis Method')}</span>
                        <Badge variant="outline" className="bg-blue-100 text-blue-800">
                          {scoldResult.analysis_method === 'scold_vlm' ? 'SCOLD VLM' : scoldResult.analysis_method}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Overall Health */}
                  <Card>
                    <CardContent className="pt-6 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{t('scold_overall_health', 'Overall Health')}</span>
                        <div className="flex items-center">
                          {scoldResult.overall_health === 'healthy' ? (
                            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                          ) : (
                            <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                          )}
                          <span className="font-semibold capitalize">{scoldResult.overall_health}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>{t('scold_confidence', 'Confidence')}</span>
                          <span>{(scoldResult.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full transition-all"
                            style={{ width: `${scoldResult.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Detections */}
                  {scoldResult.detections && scoldResult.detections.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center text-lg">
                          <TrendingUp className="w-5 h-5 mr-2" />
                          {t('scold_detected_diseases', 'Detected Diseases')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {scoldResult.detections.map((detection, index) => (
                          <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                            <div className="flex justify-between items-start mb-1">
                              <span className="font-medium text-gray-900">{detection.disease_name}</span>
                              <Badge className={getSeverityColor(detection.severity)}>
                                {detection.severity}
                              </Badge>
                            </div>
                            <div className="flex items-center text-sm text-gray-600">
                              <span>{t('scold_confidence', 'Confidence')}: {(detection.confidence * 100).toFixed(1)}%</span>
                              {detection.affected_area && (
                                <span className="ml-4">
                                  {t('scold_affected_area', 'Affected')}: {detection.affected_area.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {/* Recommendations */}
                  {scoldResult.recommendations && scoldResult.recommendations.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">{t('scold_recommendations', 'Treatment Recommendations')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {scoldResult.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                              <span className="text-sm text-gray-700">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}

                  {scoldResult.detections.length === 0 && (
                    <Alert>
                      <CheckCircle className="w-5 h-5" />
                      <AlertDescription>
                        {t('scold_no_diseases', 'No diseases detected - Plant appears healthy!')}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {!scoldResult && !scoldError && !isScoldAnalyzing && (
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-center h-64 text-center">
                    <div className="space-y-2">
                      <Camera className="w-16 h-16 mx-auto text-gray-400" />
                      <p className="text-gray-600">
                        {t('scold_upload_prompt', 'Upload a plant image and click analyze to detect diseases')}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Standard Detection Tab */}
        <TabsContent value="standard" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Image Upload Section */}
            <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Image Upload & Analysis
            </CardTitle>
            <CardDescription>
              Upload a clear image of the affected crop for disease detection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="crop-type">Crop Type *</Label>
              <Select value={cropType} onValueChange={setCropType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select crop type" />
                </SelectTrigger>
                <SelectContent>
                  {cropOptions.map((crop) => (
                    <SelectItem key={crop} value={crop}>
                      {crop.charAt(0).toUpperCase() + crop.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="growth-stage">Growth Stage</Label>
              <Select value={growthStage} onValueChange={setGrowthStage}>
                <SelectTrigger>
                  <SelectValue placeholder="Select growth stage (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {growthStages.map((stage) => (
                    <SelectItem key={stage} value={stage}>
                      {stage.charAt(0).toUpperCase() + stage.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Image Upload</Label>
              <div 
                className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center cursor-pointer hover:border-muted-foreground/50 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                {imagePreview ? (
                  <div className="space-y-2">
                    <img 
                      src={imagePreview} 
                      alt="Preview" 
                      className="max-w-full max-h-48 mx-auto rounded-lg"
                    />
                    <p className="text-sm text-muted-foreground">
                      Click to change image
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-8 h-8 mx-auto text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Supports JPG, PNG (max 10MB)
                    </p>
                  </div>
                )}
              </div>
              <Input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />
            </div>

            <Button 
              onClick={handleAnalyze}
              disabled={!selectedImage || !cropType || isAnalyzing}
              className="w-full"
              size="lg"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze for Diseases"}
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Disease Detection Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">
                    {result.primary_disease.replace(/_/g, ' ').toUpperCase()}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Confidence: {(result.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <Badge className={getSeverityColorLegacy(result.severity)}>
                  {getSeverityIcon(result.severity)}
                  {result.severity} Severity
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Affected Area</p>
                  <p className="font-semibold">{result.affected_area_percentage}%</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Potential Yield Loss</p>
                  <p className="font-semibold text-red-600">
                    {result.economic_impact.potential_yield_loss}%
                  </p>
                </div>
              </div>

              {result.recommended_treatments.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Recommended Treatments</h4>
                  <div className="space-y-2">
                    {result.recommended_treatments.slice(0, 2).map((treatment, index) => (
                      <div key={index} className="bg-muted/50 p-3 rounded-lg text-sm">
                        <div className="font-medium">{treatment.product_name}</div>
                        <div className="text-muted-foreground">
                          {treatment.application_rate} • {treatment.frequency}
                        </div>
                        <div className="text-green-600">
                          ${treatment.cost_per_acre}/acre
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-1">Economic Impact</h4>
                <div className="text-sm text-blue-700">
                  <p>Treatment Cost: ${result.economic_impact.treatment_cost_estimate}</p>
                  <p>Cost-Benefit Ratio: {result.economic_impact.cost_benefit_ratio}:1</p>
                </div>
              </div>

              {/* VLM Analysis Indicator */}
              {result.vlm_analysis && (
                <div className="bg-purple-50 border border-purple-200 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-purple-600" />
                    <h4 className="font-semibold text-purple-800">VLM Enhanced Analysis</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-purple-600">Knowledge Matches</p>
                      <p className="font-semibold">{result.vlm_analysis.knowledge_matches}</p>
                    </div>
                    <div>
                      <p className="text-purple-600">AI Confidence</p>
                      <p className="font-semibold">{(result.vlm_analysis.confidence_score * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-1 text-xs text-purple-700">
                    <BookOpen className="w-3 h-3" />
                    <span>Enhanced with agricultural knowledge base</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {!result && (
          <Card className="border-dashed">
            <CardContent className="flex items-center justify-center h-64 text-center">
              <div className="space-y-2">
                <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
                  <Camera className="w-8 h-8 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">
                  Upload an image to see disease analysis results
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Prevention Tips */}
      {result?.prevention_tips && result.prevention_tips.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Prevention Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {result.prevention_tips.map((tip, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{tip}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DiseaseManagement;