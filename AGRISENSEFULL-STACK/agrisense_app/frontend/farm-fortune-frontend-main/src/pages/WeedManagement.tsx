import { useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, Camera, Target, AlertCircle, Calendar, Brain, BookOpen, Eye, Leaf, Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

// SCOLD-specific interfaces
interface SCOLDWeedDetection {
  weed_name: string;
  confidence: number;
  coverage_percentage: number;
  location_description?: string;
}

interface SCOLDAnalysisResult {
  success: boolean;
  analysis_method: string;
  detections: SCOLDWeedDetection[];
  recommendations: string[];
  overall_infestation: string;
  total_coverage: number;
  confidence: number;
}

interface WeedAnalysisResult {
  weed_coverage_percentage: number;
  weed_pressure: string;
  dominant_weed_types: string[];
  weed_regions: Array<{
    region_id: string;
    weed_type: string;
    coverage_percentage: number;
    density: string;
    coordinates: number[];
  }>;
  management_plan: {
    recommended_actions: Array<{
      action_type: string;
      priority: string;
      method: string;
      timing: string;
      cost_estimate: number;
    }>;
    herbicide_recommendations: Array<{
      product_name: string;
      active_ingredient: string;
      application_rate: string;
      target_weeds: string[];
      cost_per_acre: number;
    }>;
    cultural_practices: string[];
  };
  economic_analysis: {
    potential_yield_loss: number;
    control_cost_estimate: number;
    roi_estimate: number;
  };
  vlm_analysis?: {
    knowledge_matches: number;
    confidence_score: number;
    analysis_timestamp: string;
    visual_features?: {
      contour_count: number;
      edge_density: number;
      dominant_colors?: number[][];
      size?: number[];
    };
  };
}

const WeedManagement = () => {
  const { t } = useTranslation();
  
  // Standard detection state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<WeedAnalysisResult | null>(null);
  const [cropType, setCropType] = useState("");
  const [fieldSize, setFieldSize] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // SCOLD detection state
  const [scoldImage, setScoldImage] = useState<string | null>(null);
  const [scoldCropType, setScoldCropType] = useState('wheat');
  const [isScoldAnalyzing, setIsScoldAnalyzing] = useState(false);
  const [scoldResult, setScoldResult] = useState<SCOLDAnalysisResult | null>(null);
  const [scoldError, setScoldError] = useState<string | null>(null);

  const cropOptions = [
    "corn", "soybean", "wheat", "cotton", "rice", "tomato", 
    "potato", "sugar_beet", "sunflower", "canola"
  ];

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
        const base64 = reader.result as string;
        const imageData = base64.split(',')[1]; // Remove data URL prefix

        // 🆕 Try SCOLD VLM first for advanced weed detection
        let detectionSuccess = false;
        try {
          const { detectWeedsWithScold } = await import('../services/aiModels');
          toast.info("🔍 Using SCOLD VLM for advanced weed detection...");
          
          const scoldResponse = await detectWeedsWithScold(imageData, cropType);
          
          if (scoldResponse.success && scoldResponse.detections.length > 0) {
            // Transform SCOLD response to match expected format
            const transformedData: WeedAnalysisResult = {
              weed_coverage_percentage: scoldResponse.total_weed_coverage,
              weed_pressure: scoldResponse.total_weed_coverage > 30 ? "high" : 
                             scoldResponse.total_weed_coverage > 15 ? "moderate" : "low",
              dominant_weed_types: scoldResponse.detections.map(d => d.weed_type),
              weed_regions: scoldResponse.detections.map((d, idx) => ({
                region_id: `region-${idx}`,
                weed_type: d.weed_type,
                coverage_percentage: d.coverage_percent || 0,
                density: d.coverage_percent && d.coverage_percent > 20 ? "high" : "moderate",
                coordinates: d.bbox || []
              })),
              management_plan: {
                recommended_actions: scoldResponse.detections.slice(0, 3).map((d, idx) => ({
                  action_type: d.treatment?.manual_removal[0] || "Manual removal",
                  priority: idx === 0 ? "high" : "medium",
                  method: d.treatment?.mulching[0] || "Mulching",
                  timing: "Immediate",
                  cost_estimate: 50 * (idx + 1)
                })),
                herbicide_recommendations: scoldResponse.detections.slice(0, 2).map(d => ({
                  product_name: d.treatment?.organic_herbicides[0] || "Organic herbicide",
                  active_ingredient: "Natural compounds",
                  application_rate: "As directed",
                  target_weeds: [d.weed_type],
                  cost_per_acre: 75
                })),
                cultural_practices: scoldResponse.detections[0]?.treatment?.prevention_tips || []
              },
              economic_analysis: {
                potential_yield_loss: scoldResponse.total_weed_coverage * 0.5,
                control_cost_estimate: scoldResponse.detections.length * 100,
                roi_estimate: 2.5
              },
              vlm_analysis: {
                knowledge_matches: scoldResponse.detections.length,
                confidence_score: scoldResponse.detections[0]?.confidence || 0,
                analysis_timestamp: scoldResponse.timestamp
              }
            };
            
            setResult(transformedData);
            toast.success("✅ SCOLD VLM weed analysis completed!");
            detectionSuccess = true;
          }
        } catch (scoldError) {
          console.info("SCOLD VLM unavailable, using fallback detection:", scoldError);
        }

        // Fallback to standard detection if SCOLD VLM fails
        if (!detectionSuccess) {
          toast.info("Using standard weed detection...");
          const response = await fetch("/api/weed/analyze", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              image_data: imageData,
              crop_type: cropType,
              field_info: {
                crop_type: cropType,
                field_size_acres: fieldSize ? parseFloat(fieldSize) : 1.0
              }
            }),
          });

          if (!response.ok) {
            throw new Error(`Analysis failed: ${response.statusText}`);
          }

          const data = await response.json();
          setResult(data);
          toast.success("Weed analysis completed!");
        }
      };
      reader.readAsDataURL(selectedImage);
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error("Failed to analyze image. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getPressureColor = (pressure: string) => {
    switch (pressure?.toLowerCase()) {
      case "low": return "bg-green-100 text-green-800 border-green-200";
      case "moderate": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "high": return "bg-orange-100 text-orange-800 border-orange-200";
      case "severe": return "bg-red-100 text-red-800 border-red-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case "low": return "bg-blue-100 text-blue-800";
      case "medium": return "bg-yellow-100 text-yellow-800";
      case "high": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  // SCOLD-specific handlers
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

      const response = await fetch('http://localhost:8004/api/weed/analyze', {
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
      toast.success("SCOLD weed analysis completed!");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed';
      setScoldError(errorMsg);
      toast.error(errorMsg);
      console.error('SCOLD weed identification error:', err);
    } finally {
      setIsScoldAnalyzing(false);
    }
  };

  const getInfestationColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'high':
      case 'severe':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
      case 'moderate':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
      case 'minimal':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Weed Management System
        </h1>
        <p className="text-muted-foreground">
          Advanced AI-powered weed detection with multiple analysis methods
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
                  {t('scold_upload_field', 'Upload Field Image')}
                </CardTitle>
                <CardDescription>
                  {t('scold_weed_subtitle', 'AI-powered weed detection and crop field analysis')}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Image Preview */}
                <div className="mb-4">
                  {scoldImage ? (
                    <img
                      src={scoldImage}
                      alt="Selected field"
                      className="w-full h-64 object-cover rounded-lg border-2 border-gray-200"
                    />
                  ) : (
                    <div className="w-full h-64 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                      <div className="text-center">
                        <Upload className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                        <p className="text-gray-600">{t('scold_no_image', 'No image selected')}</p>
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
                  <Label htmlFor="scold-crop-type">{t('scold_crop_type', 'Crop Type')}</Label>
                  <Select value={scoldCropType} onValueChange={setScoldCropType}>
                    <SelectTrigger id="scold-crop-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="wheat">{t('crop_wheat', 'Wheat')}</SelectItem>
                      <SelectItem value="rice">{t('crop_rice', 'Rice')}</SelectItem>
                      <SelectItem value="corn">{t('crop_corn', 'Corn')}</SelectItem>
                      <SelectItem value="soybean">{t('crop_soybean', 'Soybean')}</SelectItem>
                      <SelectItem value="cotton">{t('crop_cotton', 'Cotton')}</SelectItem>
                      <SelectItem value="sugarcane">{t('crop_sugarcane', 'Sugarcane')}</SelectItem>
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
                    t('scold_identify_button', 'Identify Weeds')
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

                  {/* Overall Infestation */}
                  <Card>
                    <CardContent className="pt-6 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{t('scold_infestation_level', 'Infestation Level')}</span>
                        <Badge className={getInfestationColor(scoldResult.overall_infestation)}>
                          {scoldResult.overall_infestation}
                        </Badge>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>{t('scold_total_coverage', 'Total Weed Coverage')}</span>
                          <span>{scoldResult.total_coverage.toFixed(1)}%</span>
                        </div>
                        <Progress value={scoldResult.total_coverage} className="h-2" />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Detected Weeds */}
                  {scoldResult.detections.length > 0 ? (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">{t('scold_detected_weeds', 'Detected Weed Species')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {scoldResult.detections.map((weed, index) => (
                            <div key={index} className="border rounded-lg p-3">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <Leaf className="w-4 h-4 text-green-600" />
                                  <h4 className="font-medium capitalize">{weed.weed_name.replace(/_/g, ' ')}</h4>
                                </div>
                                <Badge variant="outline">
                                  {(weed.confidence * 100).toFixed(0)}%
                                </Badge>
                              </div>
                              <div className="text-sm text-gray-600">
                                <span>{t('scold_coverage', 'Coverage')}: </span>
                                <span className="font-semibold">{weed.coverage_percentage.toFixed(1)}%</span>
                              </div>
                              {weed.location_description && (
                                <p className="text-xs text-gray-500 mt-1">{weed.location_description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ) : (
                    <Card>
                      <CardContent className="flex items-center justify-center h-32 text-center">
                        <div className="space-y-2">
                          <CheckCircle2 className="w-12 h-12 mx-auto text-green-600" />
                          <p className="text-green-600 font-medium">
                            {t('scold_no_weeds', 'No weeds detected - field looks clean!')}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Recommendations */}
                  {scoldResult.recommendations.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">{t('scold_control_recommendations', 'Control Recommendations')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {scoldResult.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <Target className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {!scoldResult && !scoldError && !isScoldAnalyzing && (
                <Card className="border-dashed">
                  <CardContent className="flex items-center justify-center h-64 text-center">
                    <div className="space-y-2">
                      <Camera className="w-16 h-16 mx-auto text-gray-400" />
                      <p className="text-gray-600">
                        {t('scold_upload_field_prompt', 'Upload a field image and click identify to detect weeds')}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Image Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Field Image Analysis
            </CardTitle>
            <CardDescription>
              Upload a field image to detect and analyze weed coverage
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
                      {crop.replace(/_/g, ' ').charAt(0).toUpperCase() + crop.replace(/_/g, ' ').slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="field-size">Field Size (acres)</Label>
              <Input
                id="field-size"
                type="number"
                step="0.1"
                min="0.1"
                value={fieldSize}
                onChange={(e) => setFieldSize(e.target.value)}
                placeholder="e.g., 5.2"
              />
            </div>

            <div className="space-y-2">
              <Label>Field Image Upload</Label>
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
                      Click to upload field image
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Best results with overhead or side-view field images
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
              {isAnalyzing ? "Analyzing..." : "Analyze Weed Coverage"}
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Weed Analysis Results
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">
                    {result.weed_coverage_percentage.toFixed(1)}% Weed Coverage
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {result.weed_regions.length} weed regions detected
                  </p>
                </div>
                <Badge className={getPressureColor(result.weed_pressure)}>
                  {result.weed_pressure} Pressure
                </Badge>
              </div>

              <div>
                <Label className="text-sm font-medium">Weed Coverage</Label>
                <Progress 
                  value={result.weed_coverage_percentage} 
                  className="h-3 mt-1"
                />
              </div>

              {result.dominant_weed_types.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Dominant Weed Types</h4>
                  <div className="flex flex-wrap gap-2">
                    {result.dominant_weed_types.map((weed, index) => (
                      <Badge key={index} variant="outline">
                        {weed.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Potential Yield Loss</p>
                  <p className="font-semibold text-red-600">
                    {result.economic_analysis.potential_yield_loss}%
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Control Cost</p>
                  <p className="font-semibold">
                    ${result.economic_analysis.control_cost_estimate}
                  </p>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 p-3 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-1">ROI Estimate</h4>
                <p className="text-sm text-green-700">
                  {result.economic_analysis.roi_estimate}% return on investment
                </p>
              </div>

              {/* VLM Analysis Indicator */}
              {result.vlm_analysis && (
                <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-blue-600" />
                    <h4 className="font-semibold text-blue-800">VLM Enhanced Analysis</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-blue-600">Knowledge Matches</p>
                      <p className="font-semibold">{result.vlm_analysis.knowledge_matches}</p>
                    </div>
                    <div>
                      <p className="text-blue-600">AI Confidence</p>
                      <p className="font-semibold">{(result.vlm_analysis.confidence_score * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  {result.vlm_analysis.visual_features && (
                    <div className="mt-2 text-xs text-blue-700">
                      <p>Visual Analysis: {result.vlm_analysis.visual_features.contour_count} features detected</p>
                    </div>
                  )}
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
                  <Target className="w-8 h-8 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">
                  Upload a field image to see weed analysis results
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Management Plan */}
      {result?.management_plan && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Recommended Actions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.management_plan.recommended_actions.map((action, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium">{action.method}</h4>
                      <Badge className={getPriorityColor(action.priority)} variant="outline">
                        {action.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-1">
                      {action.action_type}
                    </p>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {action.timing}
                      </span>
                      <span className="font-medium text-green-600">
                        ${action.cost_estimate}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Herbicide Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.management_plan.herbicide_recommendations.map((herbicide, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <h4 className="font-medium">{herbicide.product_name}</h4>
                    <p className="text-sm text-muted-foreground">
                      Active ingredient: {herbicide.active_ingredient}
                    </p>
                    <p className="text-sm">
                      Rate: {herbicide.application_rate}
                    </p>
                    <div className="flex justify-between items-center mt-2">
                      <div className="text-sm">
                        <span className="text-muted-foreground">Targets: </span>
                        {herbicide.target_weeds.slice(0, 2).join(", ")}
                        {herbicide.target_weeds.length > 2 && "..."}
                      </div>
                      <span className="font-medium text-green-600">
                        ${herbicide.cost_per_acre}/acre
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Cultural Practices */}
      {result?.management_plan.cultural_practices && result.management_plan.cultural_practices.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Cultural Control Practices</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {result.management_plan.cultural_practices.map((practice, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">{practice}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WeedManagement;