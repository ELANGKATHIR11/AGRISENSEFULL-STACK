import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Zap, Droplets, Thermometer, Gauge, Beaker, AlertCircle, CheckCircle, TrendingUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface SensorData {
  temperature: string;
  humidity: string;
  soilMoisture: string;
  ph: string;
  nitrogen: string;
  phosphorus: string;
  potassium: string;
  cropType: string;
}

interface Recommendation {
  type: "irrigation" | "fertilizer" | "general";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  action: string;
}

const Recommend = () => {
  const [sensorData, setSensorData] = useState<SensorData>({
    temperature: "",
    humidity: "",
    soilMoisture: "",
    ph: "",
    nitrogen: "",
    phosphorus: "",
    potassium: "",
    cropType: "",
  });
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleInputChange = (field: keyof SensorData, value: string) => {
    setSensorData(prev => ({ ...prev, [field]: value }));
  };

  const generateRecommendations = async () => {
    setLoading(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock recommendations based on sensor data
    const mockRecommendations: Recommendation[] = [
      {
        type: "irrigation",
        priority: "high",
        title: "Increase Irrigation",
        description: `Soil moisture at ${sensorData.soilMoisture}% is below optimal range for ${sensorData.cropType}`,
        action: "Apply 15-20mm irrigation within next 6 hours"
      },
      {
        type: "fertilizer",
        priority: "medium",
        title: "Nitrogen Supplementation",
        description: `Nitrogen levels (${sensorData.nitrogen}ppm) require adjustment for optimal growth`,
        action: "Apply 50kg/ha nitrogen fertilizer in next application"
      },
      {
        type: "general",
        priority: "low",
        title: "Monitor pH Levels",
        description: `Current pH of ${sensorData.ph} is within acceptable range but trending toward acidic`,
        action: "Schedule soil amendment in 2 weeks if trend continues"
      }
    ];

    setRecommendations(mockRecommendations);
    setLoading(false);
    
    toast({
      title: "Analysis Complete",
      description: "Smart recommendations generated based on your sensor data.",
    });
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "high": return <AlertCircle className="w-4 h-4 text-destructive" />;
      case "medium": return <TrendingUp className="w-4 h-4 text-accent-foreground" />;
      default: return <CheckCircle className="w-4 h-4 text-primary" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "border-l-destructive bg-destructive/5";
      case "medium": return "border-l-accent-foreground bg-accent";
      default: return "border-l-primary bg-primary/5";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Smart Recommendations</h1>
          <p className="text-muted-foreground">Input your sensor data to receive AI-powered farming recommendations</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sensor Input Form */}
          <Card className="shadow-medium">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-primary" />
                <span>Sensor Data Input</span>
              </CardTitle>
              <CardDescription>
                Enter current readings from your field sensors
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Environmental Sensors */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Environmental Conditions</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="temperature" className="flex items-center space-x-2">
                      <Thermometer className="w-4 h-4" />
                      <span>Temperature (°C)</span>
                    </Label>
                    <Input
                      id="temperature"
                      placeholder="25.5"
                      value={sensorData.temperature}
                      onChange={(e) => handleInputChange("temperature", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="humidity" className="flex items-center space-x-2">
                      <Droplets className="w-4 h-4" />
                      <span>Humidity (%)</span>
                    </Label>
                    <Input
                      id="humidity"
                      placeholder="65"
                      value={sensorData.humidity}
                      onChange={(e) => handleInputChange("humidity", e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Soil Sensors */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">Soil Analysis</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="soilMoisture">Soil Moisture (%)</Label>
                    <Input
                      id="soilMoisture"
                      placeholder="45"
                      value={sensorData.soilMoisture}
                      onChange={(e) => handleInputChange("soilMoisture", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="ph">pH Level</Label>
                    <Input
                      id="ph"
                      placeholder="6.5"
                      value={sensorData.ph}
                      onChange={(e) => handleInputChange("ph", e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Nutrient Levels */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center space-x-2">
                  <Beaker className="w-4 h-4" />
                  <span>Nutrient Levels (ppm)</span>
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="nitrogen">Nitrogen (N)</Label>
                    <Input
                      id="nitrogen"
                      placeholder="120"
                      value={sensorData.nitrogen}
                      onChange={(e) => handleInputChange("nitrogen", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phosphorus">Phosphorus (P)</Label>
                    <Input
                      id="phosphorus"
                      placeholder="45"
                      value={sensorData.phosphorus}
                      onChange={(e) => handleInputChange("phosphorus", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="potassium">Potassium (K)</Label>
                    <Input
                      id="potassium"
                      placeholder="80"
                      value={sensorData.potassium}
                      onChange={(e) => handleInputChange("potassium", e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Crop Selection */}
              <div>
                <Label htmlFor="cropType">Crop Type</Label>
                <Select value={sensorData.cropType} onValueChange={(value) => handleInputChange("cropType", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select crop type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="wheat">Wheat</SelectItem>
                    <SelectItem value="corn">Corn</SelectItem>
                    <SelectItem value="rice">Rice</SelectItem>
                    <SelectItem value="soybean">Soybean</SelectItem>
                    <SelectItem value="tomato">Tomato</SelectItem>
                    <SelectItem value="potato">Potato</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button 
                onClick={generateRecommendations} 
                className="w-full bg-gradient-primary hover:shadow-glow transition-spring"
                disabled={loading || !sensorData.cropType}
              >
                <Zap className="w-4 h-4 mr-2" />
                {loading ? "Analyzing..." : "Generate Recommendations"}
              </Button>
            </CardContent>
          </Card>

          {/* Recommendations Display */}
          <Card className="shadow-medium">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <span>Smart Recommendations</span>
              </CardTitle>
              <CardDescription>
                AI-powered insights for optimal crop management
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recommendations.length === 0 ? (
                <div className="text-center py-12">
                  <Zap className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Enter sensor data to receive personalized recommendations</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recommendations.map((rec, index) => (
                    <div 
                      key={index} 
                      className={`border-l-4 p-4 rounded-lg ${getPriorityColor(rec.priority)}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-foreground flex items-center space-x-2">
                          {getPriorityIcon(rec.priority)}
                          <span>{rec.title}</span>
                        </h4>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          rec.priority === 'high' ? 'bg-destructive/20 text-destructive' :
                          rec.priority === 'medium' ? 'bg-accent text-accent-foreground' :
                          'bg-primary/20 text-primary'
                        }`}>
                          {rec.priority} priority
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{rec.description}</p>
                      <div className="bg-card p-3 rounded-md">
                        <strong className="text-xs text-primary">Recommended Action:</strong>
                        <p className="text-sm text-foreground mt-1">{rec.action}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Recommend;