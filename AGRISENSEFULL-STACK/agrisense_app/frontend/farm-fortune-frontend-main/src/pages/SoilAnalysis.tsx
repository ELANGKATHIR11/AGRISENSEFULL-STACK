import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Mountain, 
  Droplets, 
  Beaker, 
  TrendingUp, 
  Sprout, 
  Star,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Info,
  Wifi,
  WifiOff,
  RefreshCw,
  Thermometer,
  Gauge
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { api, type LiveSensorData, type DeviceStatus } from "@/lib/api";
import farmingHero from "@/assets/farming-hero.jpg";

interface SoilData {
  soilType: string;
  ph: string;
  nitrogen: string;
  phosphorus: string;
  potassium: string;
  organicMatter: string;
  moisture: string;
}

interface CropRecommendation {
  id: string;
  name: string;
  scientificName: string;
  suitabilityScore: number;
  expectedYield: string;
  reasons: string[];
  challenges: string[];
  tips: string[];
  season: string;
  waterRequirement: string;
  category: string;
}

const SoilAnalysis = () => {
  const [soilData, setSoilData] = useState<SoilData>({
    soilType: "",
    ph: "",
    nitrogen: "",
    phosphorus: "",
    potassium: "",
    organicMatter: "",
  moisture: ""
  });

  const [recommendations, setRecommendations] = useState<CropRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  
  // Live sensor data state
  const [liveSensorData, setLiveSensorData] = useState<LiveSensorData | null>(null);
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus[]>([]);
  const [sensorLoading, setSensorLoading] = useState(false);
  const [lastSensorUpdate, setLastSensorUpdate] = useState<string>("");
  
  const { toast } = useToast();

  const soilTypes = [
    "Clay", "Sandy", "Loam", "Silt", "Sandy Loam", "Clay Loam", "Silty Loam", "Sandy Clay", "Silty Clay", "Sandy Clay Loam"
  ];

  // Live sensor data functions
  const fetchLiveSensorData = async () => {
    try {
      setSensorLoading(true);
      const [sensorResponse, deviceResponse] = await Promise.all([
        api.sensorsLive(),
        api.sensorsDeviceStatus()
      ]);
      
      const sensorData = sensorResponse?.data as LiveSensorData | null;
      const devices = deviceResponse?.devices || [];
      setLiveSensorData(sensorData);
      setDeviceStatus(devices);
      setLastSensorUpdate(new Date().toLocaleTimeString());
      
      toast({
        title: "Sensor Data Updated",
        description: "Live sensor readings refreshed successfully",
      });
    } catch (error) {
      console.error('Failed to fetch sensor data:', error);
      toast({
        title: "Sensor Error",
        description: "Failed to fetch live sensor data",
        variant: "destructive",
      });
    } finally {
      setSensorLoading(false);
    }
  };

  const fillFromSensorData = () => {
    if (!liveSensorData) {
      toast({
        title: "No Sensor Data",
        description: "Please fetch live sensor data first",
        variant: "destructive",
      });
      return;
    }

    setSoilData(prev => ({
      ...prev,
      ph: liveSensorData.ph_level?.toFixed(1) || prev.ph,
      moisture: liveSensorData.soil_moisture_percentage?.toFixed(1) || prev.moisture,
      nitrogen: (Math.random() * 50 + 20).toFixed(1), // Simulated values
      phosphorus: (Math.random() * 30 + 10).toFixed(1),
      potassium: (Math.random() * 40 + 15).toFixed(1),
      organicMatter: (Math.random() * 5 + 2).toFixed(1),
    }));

    toast({
      title: "Data Filled",
      description: "Soil analysis form filled with live sensor data",
    });
  };

  // Removed location/region and climate inputs per request

  const handleInputChange = (field: keyof SoilData, value: string) => {
    setSoilData(prev => ({ ...prev, [field]: value }));
  };

  const generateRecommendations = async () => {
    setLoading(true);
    
    // Simulate AI analysis delay
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    // Mock intelligent recommendations based on soil data
    const mockRecommendations: CropRecommendation[] = [
      {
        id: "1",
        name: "Wheat",
        scientificName: "Triticum aestivum",
        suitabilityScore: 94,
        expectedYield: "4.5-6.2 tons/hectare",
  reasons: [
          `Excellent pH match (${soilData.ph}) for wheat cultivation`,
          `${soilData.soilType} soil provides good drainage and root penetration`,
          "Optimal nitrogen levels support strong vegetative growth"
        ],
        challenges: [
          "Monitor for potential waterlogging during heavy rains",
          "May require phosphorus supplementation mid-season"
        ],
        tips: [
          "Plant during optimal temperature window (15-25°C)",
          "Apply organic matter to improve soil structure",
          "Consider crop rotation with legumes"
        ],
        season: "Winter",
        waterRequirement: "Medium",
        category: "Cereal"
      },
      {
        id: "2",
        name: "Corn",
        scientificName: "Zea mays",
        suitabilityScore: 87,
        expectedYield: "8.5-12 tons/hectare",
        reasons: [
          "High organic matter content supports corn's nutrient demands",
          "Good potassium levels promote strong stalks and ears",
          "Suitable environmental conditions for corn production"
        ],
        challenges: [
          "Requires consistent water supply during tasseling",
          "May need additional nitrogen during rapid growth phase"
        ],
        tips: [
          "Ensure adequate spacing for maximum sunlight exposure",
          "Deep tillage recommended for root development",
          "Monitor for corn borer and apply IPM strategies"
        ],
        season: "Summer",
        waterRequirement: "High", 
        category: "Cereal"
      },
      {
        id: "3",
        name: "Soybean",
        scientificName: "Glycine max",
        suitabilityScore: 91,
        expectedYield: "2.8-4.2 tons/hectare",
        reasons: [
          "Nitrogen-fixing capability reduces fertilizer requirements",
          "pH levels ideal for nodule formation and nitrogen fixation",
          "Excellent rotation crop for soil health improvement"
        ],
        challenges: [
          "Sensitive to waterlogged conditions",
          "May face competition from weeds in early growth"
        ],
        tips: [
          "Inoculate seeds with rhizobia bacteria",
          "Maintain consistent moisture without waterlogging",
          "Harvest at optimal moisture content (13-15%)"
        ],
        season: "Summer",
        waterRequirement: "Medium",
        category: "Legume"
      }
    ];

    setRecommendations(mockRecommendations);
    setAnalyzed(true);
    setLoading(false);
    
    toast({
      title: "Soil Analysis Complete! 🌱",
      description: "Smart crop recommendations generated based on your soil profile.",
    });
  };

  const getSuitabilityColor = (score: number) => {
    if (score >= 90) return "bg-primary text-primary-foreground";
    if (score >= 80) return "bg-accent text-accent-foreground";
    if (score >= 70) return "bg-secondary text-secondary-foreground";
    return "bg-muted text-muted-foreground";
  };

  const getSuitabilityIcon = (score: number) => {
    if (score >= 90) return <CheckCircle2 className="w-4 h-4" />;
    if (score >= 80) return <TrendingUp className="w-4 h-4" />;
    return <AlertTriangle className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-secondary">
      {/* Hero Section */}
      <div 
        className="relative h-64 bg-cover bg-center flex items-center justify-center"
        style={{ backgroundImage: `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url(${farmingHero})` }}
      >
        <div className="text-center text-white animate-fade-in">
          <h1 className="text-4xl md:text-5xl font-bold font-serif mb-4">Soil Analysis & Crop Selection</h1>
          <p className="text-xl md:text-2xl font-light">Discover the perfect crops for your soil conditions</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Live Sensor Data Card */}
        <Card className="mb-6 shadow-strong animate-fade-in">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-green-500 rounded-t-lg">
            <CardTitle className="flex items-center justify-between text-xl text-white">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <Wifi className="w-6 h-6 text-white" />
                </div>
                <span className="font-serif">Live Sensor Data</span>
              </div>
              <Button
                onClick={fetchLiveSensorData}
                disabled={sensorLoading}
                variant="secondary"
                size="sm"
                className="bg-white/20 hover:bg-white/30 text-white border-white/30"
              >
                {sensorLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Refresh
              </Button>
            </CardTitle>
            <CardDescription className="text-white/90">
              Real-time sensor readings from your field
              {lastSensorUpdate && ` • Last updated: ${lastSensorUpdate}`}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="pt-6">
            {liveSensorData ? (
              <div className="space-y-4">
                {/* Sensor Data Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Thermometer className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">Temperature</span>
                    </div>
                    <div className="text-lg font-bold text-blue-900">
                      {liveSensorData.air_temperature?.toFixed(1) || 'N/A'}°C
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Droplets className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">Soil Moisture</span>
                    </div>
                    <div className="text-lg font-bold text-green-900">
                      {liveSensorData.soil_moisture_percentage?.toFixed(1) || 'N/A'}%
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Beaker className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-purple-800">pH Level</span>
                    </div>
                    <div className="text-lg font-bold text-purple-900">
                      {liveSensorData.ph_level?.toFixed(1) || 'N/A'}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg border border-yellow-200">
                    <div className="flex items-center space-x-2 mb-2">
                      <Gauge className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm font-medium text-yellow-800">Light</span>
                    </div>
                    <div className="text-lg font-bold text-yellow-900">
                      {liveSensorData.light_intensity_percentage?.toFixed(0) || 'N/A'} %
                    </div>
                  </div>
                </div>

                {/* Device Status */}
                {deviceStatus.length > 0 && (
                  <div className="border-t pt-4">
                    <h4 className="font-medium mb-2 flex items-center space-x-2">
                      <span>Device Status</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {deviceStatus.map((device, index) => (
                        <Badge key={index} variant={device.status === 'online' ? 'default' : 'destructive'} className="flex items-center space-x-1">
                          {device.status === 'online' ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                          <span>{device.device_id}</span>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Auto-fill Button */}
                <Button 
                  onClick={fillFromSensorData}
                  className="w-full bg-gradient-to-r from-blue-500 to-green-500 hover:from-blue-600 hover:to-green-600"
                >
                  <Droplets className="w-4 h-4 mr-2" />
                  Fill Form with Live Sensor Data
                </Button>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="mb-4">
                  <WifiOff className="w-12 h-12 text-gray-400 mx-auto" />
                </div>
                <p className="text-gray-600 mb-4">No live sensor data available</p>
                <Button onClick={fetchLiveSensorData} disabled={sensorLoading}>
                  {sensorLoading ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Wifi className="w-4 h-4 mr-2" />
                  )}
                  Connect to Sensors
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Soil Analysis Form */}
          <Card className="shadow-strong animate-scale-in">
            <CardHeader className="bg-gradient-accent rounded-t-lg">
              <CardTitle className="flex items-center space-x-3 text-xl">
                <div className="p-2 bg-primary rounded-lg animate-pulse-glow">
                  <Mountain className="w-6 h-6 text-primary-foreground" />
                </div>
                <span className="font-serif">Soil Profile Analysis</span>
              </CardTitle>
              <CardDescription className="text-base">
                Provide detailed information about your soil conditions for precise crop recommendations
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6 pt-6">
              {/* Basic Soil Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center space-x-2">
                  <Mountain className="w-5 h-5 text-primary" />
                  <span>Soil Characteristics</span>
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="soilType">Soil Type</Label>
                    <Select value={soilData.soilType} onValueChange={(value) => handleInputChange("soilType", value)}>
                      <SelectTrigger className="transition-all duration-200 focus:shadow-glow">
                        <SelectValue placeholder="Select soil type" />
                      </SelectTrigger>
                      <SelectContent className="bg-card border shadow-strong z-50">
                        {soilTypes.map(type => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ph" className="flex items-center space-x-2">
                      <Beaker className="w-4 h-4" />
                      <span>pH Level</span>
                    </Label>
                    <Input
                      id="ph"
                      placeholder="6.5"
                      value={soilData.ph}
                      onChange={(e) => handleInputChange("ph", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                </div>
              </div>

              {/* Nutrient Analysis */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center space-x-2">
                  <Beaker className="w-5 h-5 text-primary" />
                  <span>Nutrient Content (ppm)</span>
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="nitrogen">Nitrogen (N)</Label>
                    <Input
                      id="nitrogen"
                      placeholder="120"
                      value={soilData.nitrogen}
                      onChange={(e) => handleInputChange("nitrogen", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phosphorus">Phosphorus (P)</Label>
                    <Input
                      id="phosphorus"
                      placeholder="45"
                      value={soilData.phosphorus}
                      onChange={(e) => handleInputChange("phosphorus", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="potassium">Potassium (K)</Label>
                    <Input
                      id="potassium"
                      placeholder="80"
                      value={soilData.potassium}
                      onChange={(e) => handleInputChange("potassium", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                </div>
              </div>

              {/* Additional Parameters */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-foreground flex items-center space-x-2">
                  <Droplets className="w-5 h-5 text-primary" />
                  <span>Environmental Factors</span>
                </h3>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="organicMatter">Organic Matter (%)</Label>
                    <Input
                      id="organicMatter"
                      placeholder="3.2"
                      value={soilData.organicMatter}
                      onChange={(e) => handleInputChange("organicMatter", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="moisture">Moisture Content (%)</Label>
                    <Input
                      id="moisture"
                      placeholder="25"
                      value={soilData.moisture}
                      onChange={(e) => handleInputChange("moisture", e.target.value)}
                      className="transition-all duration-200 focus:shadow-glow"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Location/Region and Climate Zone removed */}
                </div>
              </div>

              <Button 
                onClick={generateRecommendations}
                className="w-full bg-gradient-primary hover:shadow-glow transition-all duration-300 transform hover:scale-105 text-lg py-6"
                disabled={loading || !soilData.soilType || !soilData.ph}
              >
                <Sprout className="w-5 h-5 mr-3" />
                {loading ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-foreground mr-2" />
                    Analyzing Soil Profile...
                  </span>
                ) : (
                  "Generate Crop Recommendations"
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Recommendations Display */}
          <div className="space-y-6">
            <Card className="shadow-strong animate-scale-in">
              <CardHeader className="bg-gradient-primary text-primary-foreground rounded-t-lg">
                <CardTitle className="flex items-center space-x-3 text-xl">
                  <TrendingUp className="w-6 h-6" />
                  <span className="font-serif">Smart Crop Recommendations</span>
                </CardTitle>
                <CardDescription className="text-primary-foreground/80 text-base">
                  AI-powered crop selection based on your soil analysis
                </CardDescription>
              </CardHeader>
              
              <CardContent className="pt-6">
                {!analyzed ? (
                  <div className="text-center py-16 animate-bounce-gentle">
                    <Sprout className="w-16 h-16 text-muted-foreground mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">Ready for Analysis</h3>
                    <p className="text-muted-foreground">Complete the soil profile form to receive personalized crop recommendations</p>
                  </div>
                ) : recommendations.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-6" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">Analyzing Your Soil</h3>
                    <p className="text-muted-foreground">Our AI is processing your soil data to find the perfect crops...</p>
                  </div>
                ) : (
                  <div className="space-y-6 animate-fade-in">
                    {recommendations.map((crop, index) => (
                      <Card key={crop.id} className="border-l-4 border-l-primary hover:shadow-medium transition-all duration-300 transform hover:scale-105">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <h4 className="text-xl font-bold text-foreground flex items-center space-x-2">
                                <Sprout className="w-5 h-5 text-primary" />
                                <span>{crop.name}</span>
                              </h4>
                              <p className="text-sm text-muted-foreground italic">{crop.scientificName}</p>
                            </div>
                            <Badge className={`flex items-center space-x-2 ${getSuitabilityColor(crop.suitabilityScore)}`}>
                              {getSuitabilityIcon(crop.suitabilityScore)}
                              <span>{crop.suitabilityScore}% Match</span>
                            </Badge>
                          </div>

                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-muted-foreground">Soil Compatibility</span>
                              <span className="text-sm font-medium text-foreground">{crop.suitabilityScore}%</span>
                            </div>
                            <Progress value={crop.suitabilityScore} className="h-3" />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                            <div className="flex items-center space-x-2 text-sm">
                              <Calendar className="w-4 h-4 text-primary" />
                              <span className="text-muted-foreground">Season:</span>
                              <Badge variant="outline">{crop.season}</Badge>
                            </div>
                            <div className="flex items-center space-x-2 text-sm">
                              <Droplets className="w-4 h-4 text-primary" />
                              <span className="text-muted-foreground">Water:</span>
                              <Badge variant="outline">{crop.waterRequirement}</Badge>
                            </div>
                            <div className="flex items-center space-x-2 text-sm">
                              <TrendingUp className="w-4 h-4 text-primary" />
                              <span className="text-muted-foreground">Yield:</span>
                              <span className="font-medium text-foreground">{crop.expectedYield}</span>
                            </div>
                          </div>

                          <div className="space-y-4">
                            <div>
                              <h5 className="font-semibold text-foreground flex items-center space-x-2 mb-2">
                                <CheckCircle2 className="w-4 h-4 text-primary" />
                                <span>Why This Crop Works</span>
                              </h5>
                              <ul className="space-y-1">
                                {crop.reasons.map((reason, i) => (
                                  <li key={i} className="text-sm text-muted-foreground flex items-start space-x-2">
                                    <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                                    <span>{reason}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            <div>
                              <h5 className="font-semibold text-foreground flex items-center space-x-2 mb-2">
                                <AlertTriangle className="w-4 h-4 text-destructive" />
                                <span>Challenges to Consider</span>
                              </h5>
                              <ul className="space-y-1">
                                {crop.challenges.map((challenge, i) => (
                                  <li key={i} className="text-sm text-muted-foreground flex items-start space-x-2">
                                    <div className="w-1.5 h-1.5 bg-destructive rounded-full mt-2 flex-shrink-0" />
                                    <span>{challenge}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            <div>
                              <h5 className="font-semibold text-foreground flex items-center space-x-2 mb-2">
                                <Info className="w-4 h-4 text-accent-foreground" />
                                <span>Growing Tips</span>
                              </h5>
                              <ul className="space-y-1">
                                {crop.tips.map((tip, i) => (
                                  <li key={i} className="text-sm text-muted-foreground flex items-start space-x-2">
                                    <Star className="w-3 h-3 text-accent-foreground mt-1.5 flex-shrink-0" />
                                    <span>{tip}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SoilAnalysis;