import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Upload, Camera, AlertTriangle, CheckCircle, Info, Brain, BookOpen } from "lucide-react";
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

const DiseaseManagement = () => {
  const { t } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<DiseaseDetectionResult | null>(null);
  const [cropType, setCropType] = useState("");
  const [growthStage, setGrowthStage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const cropOptions = [
    "tomato", "potato", "corn", "wheat", "rice", "soybean", "bean",
    "cotton", "apple", "grape", "citrus", "pepper", "cucumber"
  ];

  const growthStages = [
    "seedling", "vegetative", "flowering", "fruiting", "mature"
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
        try {
          const base64 = reader.result as string;
          const imageData = base64.split(',')[1]; // Remove data URL prefix

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

  const getSeverityColor = (severity: string) => {
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
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Crop Disease Management
        </h1>
        <p className="text-muted-foreground">
          Upload crop images to detect diseases and get treatment recommendations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Image Upload Section */}
        <div>

        </div>
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
                <Badge className={getSeverityColor(result.severity)}>
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
    </div>
  );
};

export default DiseaseManagement;