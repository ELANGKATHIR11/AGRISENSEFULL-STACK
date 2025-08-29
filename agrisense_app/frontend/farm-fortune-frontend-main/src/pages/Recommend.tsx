import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Zap, Droplets, Thermometer, Gauge, Beaker, AlertCircle, CheckCircle, TrendingUp } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

import { api, type SensorReading, type BackendRecommendation, type PlantListItem } from "@/lib/api";

interface SensorDataUI {
  temperature: string;
  humidity: string;
  soilMoisture: string;
  ph: string;
  nitrogen: string;
  phosphorus: string;
  potassium: string;
  cropType: string;
}

const Recommend = () => {
  const [sensorData, setSensorData] = useState<SensorDataUI>({
    temperature: "",
    humidity: "",
    soilMoisture: "",
    ph: "",
    nitrogen: "",
    phosphorus: "",
    potassium: "",
    cropType: "",
  });
  const [recommendation, setRecommendation] = useState<BackendRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [plants, setPlants] = useState<PlantListItem[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.plants();
        if (!cancelled) setPlants(res.items);
      } catch {
        // ignore
      }
    })();
    return () => { cancelled = true };
  }, []);

  const handleInputChange = (field: keyof SensorDataUI, value: string) => {
    setSensorData(prev => ({ ...prev, [field]: value }));
  };

  const generateRecommendations = async () => {
    setLoading(true);
    try {
      const payload: SensorReading = {
        plant: sensorData.cropType || "generic",
        soil_type: "loam",
        area_m2: 100,
        ph: parseFloat(sensorData.ph || "6.5"),
        moisture_pct: parseFloat(sensorData.soilMoisture || "40"),
        temperature_c: parseFloat(sensorData.temperature || "28"),
        ec_dS_m: 1.0,
        n_ppm: sensorData.nitrogen ? parseFloat(sensorData.nitrogen) : undefined,
        p_ppm: sensorData.phosphorus ? parseFloat(sensorData.phosphorus) : undefined,
        k_ppm: sensorData.potassium ? parseFloat(sensorData.potassium) : undefined,
      };
      const res = await api.recommend(payload);
      setRecommendation(res);
      toast({ title: "Analysis Complete", description: "Smart recommendations generated." });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      toast({ title: "Request failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
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
                    {plants.map((p) => (
                      <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                    ))}
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
              {!recommendation ? (
                <div className="text-center py-12">
                  <Zap className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Enter sensor data to receive personalized recommendations</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="border-l-4 p-4 rounded-lg bg-primary/5 border-l-primary">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-foreground flex items-center space-x-2">
                        {getPriorityIcon("high")}
                        <span>Irrigation & Fertilizer Plan</span>
                      </h4>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Water (liters total)</div>
                        <div className="text-foreground font-medium">{recommendation.water_liters}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Irrigation cycles</div>
                        <div className="text-foreground font-medium">{recommendation.irrigation_cycles ?? '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">N (g)</div>
                        <div className="text-foreground font-medium">{recommendation.fert_n_g}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">P (g)</div>
                        <div className="text-foreground font-medium">{recommendation.fert_p_g}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">K (g)</div>
                        <div className="text-foreground font-medium">{recommendation.fert_k_g}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Runtime (min)</div>
                        <div className="text-foreground font-medium">{recommendation.suggested_runtime_min ?? '-'}</div>
                      </div>
                    </div>
                  </div>
                  {recommendation.notes && recommendation.notes.length > 0 && (
                    <div className="border-l-4 p-4 rounded-lg bg-accent border-l-accent-foreground">
                      <div className="text-sm text-accent-foreground font-semibold mb-2">Notes</div>
                      <ul className="list-disc ml-5 space-y-1 text-sm">
                        {recommendation.notes.map((n, i) => (<li key={i}>{n}</li>))}
                      </ul>
                    </div>
                  )}
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