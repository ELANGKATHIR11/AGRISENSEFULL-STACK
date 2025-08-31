import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Zap, Droplets, Thermometer, Gauge, Beaker, AlertCircle, CheckCircle, TrendingUp, Play, Square } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n";

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
  soilType: string;
  areaM2: string;
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
    soilType: "loam",
    areaM2: "100",
  });
  const [recommendation, setRecommendation] = useState<BackendRecommendation | null>(null);
  const [loading, setLoading] = useState(false);
  const [plants, setPlants] = useState<PlantListItem[]>([]);
  const [soilTypes, setSoilTypes] = useState<string[]>(["sand","loam","clay"]);
  const [warnings, setWarnings] = useState<Record<string, string>>({});
  const { toast } = useToast();
  const { t } = useI18n();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await api.plants();
        if (!cancelled) setPlants(res.items);
        const soil = await api.soilTypes();
        if (!cancelled && soil.items?.length) setSoilTypes(soil.items);
      } catch {
        // ignore
      }
    })();
    return () => { cancelled = true };
  }, []);

  const handleInputChange = (field: keyof SensorDataUI, value: string) => {
    setSensorData(prev => ({ ...prev, [field]: value }));
    // Basic inline validation warnings
    const w: Record<string, string> = {};
    const ph = field === 'ph' ? parseFloat(value || 'NaN') : parseFloat(sensorData.ph || 'NaN');
    if (!Number.isNaN(ph) && (ph < 3.5 || ph > 9.5)) w.ph = t('warn_ph_range');
    const moisture = field === 'soilMoisture' ? parseFloat(value || 'NaN') : parseFloat(sensorData.soilMoisture || 'NaN');
    if (!Number.isNaN(moisture) && (moisture < 0 || moisture > 100)) w.soilMoisture = t('warn_moisture_range');
    const temp = field === 'temperature' ? parseFloat(value || 'NaN') : parseFloat(sensorData.temperature || 'NaN');
    if (!Number.isNaN(temp) && (temp < -10 || temp > 60)) w.temperature = t('warn_temp_range');
    const area = field === 'areaM2' ? parseFloat(value || 'NaN') : parseFloat(sensorData.areaM2 || 'NaN');
    if (!Number.isNaN(area) && area <= 0) w.areaM2 = t('warn_area_positive');
    setWarnings(w);
  };

  const generateRecommendations = async () => {
    setLoading(true);
    try {
      const payload: SensorReading = {
        plant: sensorData.cropType || "generic",
        soil_type: (sensorData.soilType || "loam").toLowerCase(),
        area_m2: Math.max(1, parseFloat(sensorData.areaM2 || "100")),
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

  const startIrrigation = async () => {
    try {
      // Use suggested runtime if provided; else a simple heuristic based on water_liters and assumed flow
      const seconds = recommendation?.suggested_runtime_min
        ? Math.max(1, Math.round(recommendation.suggested_runtime_min * 60))
        : Math.max(60, Math.round((recommendation?.water_liters || 0) / Math.max(1, recommendation?.assumed_flow_lpm || 20) * 60));
      const r = await api.irrigationStart("Z1", seconds);
      toast({ title: r.ok ? "Irrigation start sent" : "Queued", description: r.status });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed to start", description: msg, variant: "destructive" });
    }
  };

  const stopIrrigation = async () => {
    try {
      const r = await api.irrigationStop("Z1");
      toast({ title: r.ok ? "Stop sent" : "Stop queued", description: r.status });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed to stop", description: msg, variant: "destructive" });
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
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("smart_recommendations")}</h1>
          <p className="text-muted-foreground">{t("enter_sensor_prompt")}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sensor Input Form */}
          <Card className="shadow-medium">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-primary" />
                <span>{t("sensor_data_input")}</span>
              </CardTitle>
              <CardDescription>
                {t("enter_readings")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Environmental Sensors */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground">{t("environmental_conditions")}</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="temperature" className="flex items-center space-x-2">
                      <Thermometer className="w-4 h-4" />
                      <span>{t("temperature_c_label")}</span>
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
                      <span>{t("humidity_pct")}</span>
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
                <h3 className="text-sm font-semibold text-foreground">{t("soil_analysis")}</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="soilMoisture">{t("soil_moisture_pct")}</Label>
                    <Input
                      id="soilMoisture"
                      placeholder="45"
                      value={sensorData.soilMoisture}
                      onChange={(e) => handleInputChange("soilMoisture", e.target.value)}
                    />
                    {warnings.soilMoisture && (<div className="text-xs text-destructive mt-1">{warnings.soilMoisture}</div>)}
                  </div>
                  <div>
                    <Label htmlFor="ph">{t("ph_level")}</Label>
                    <Input
                      id="ph"
                      placeholder="6.5"
                      value={sensorData.ph}
                      onChange={(e) => handleInputChange("ph", e.target.value)}
                    />
                    {warnings.ph && (<div className="text-xs text-destructive mt-1">{warnings.ph}</div>)}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="soilType">{t("soil_type")}</Label>
                    <Select value={sensorData.soilType} onValueChange={(v)=>handleInputChange("soilType", v)}>
                      <SelectTrigger>
                        <SelectValue placeholder={t("select_soil_type")} />
                      </SelectTrigger>
                      <SelectContent>
                        {soilTypes.map(s => (<SelectItem key={s} value={s}>{s}</SelectItem>))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="areaM2">{t("area_m2")}</Label>
                    <Input
                      id="areaM2"
                      placeholder="100"
                      value={sensorData.areaM2}
                      onChange={(e) => handleInputChange("areaM2", e.target.value)}
                    />
                    {warnings.areaM2 && (<div className="text-xs text-destructive mt-1">{warnings.areaM2}</div>)}
                  </div>
                </div>
              </div>

              {/* Nutrient Levels */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground flex items-center space-x-2">
                  <Beaker className="w-4 h-4" />
                  <span>{t("nutrient_levels_ppm")}</span>
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="nitrogen">{t("nitrogen_n")}</Label>
                    <Input
                      id="nitrogen"
                      placeholder="120"
                      value={sensorData.nitrogen}
                      onChange={(e) => handleInputChange("nitrogen", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phosphorus">{t("phosphorus_p")}</Label>
                    <Input
                      id="phosphorus"
                      placeholder="45"
                      value={sensorData.phosphorus}
                      onChange={(e) => handleInputChange("phosphorus", e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="potassium">{t("potassium_k")}</Label>
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
                <Label htmlFor="cropType">{t("crop_type")}</Label>
                <Select value={sensorData.cropType} onValueChange={(value) => handleInputChange("cropType", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("select_crop_type")} />
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
                disabled={loading || !sensorData.cropType || !sensorData.soilType || !(parseFloat(sensorData.areaM2||'0')>0)}
              >
                <Zap className="w-4 h-4 mr-2" />
                {loading ? t("analyzing") : t("generate_recommendations")}
              </Button>
            </CardContent>
          </Card>

          {/* Recommendations Display */}
          <Card className="shadow-medium">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <span>{t("smart_recommendations")}</span>
              </CardTitle>
              <CardDescription>
                {t("ai_insights")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!recommendation ? (
                <div className="text-center py-12">
                  <Zap className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">{t("enter_sensor_prompt")}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="border-l-4 p-4 rounded-lg bg-primary/5 border-l-primary">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-foreground flex items-center space-x-2">
                        {getPriorityIcon("high")}
                        <span>{t("irrigation_fertilizer_plan")}</span>
                      </h4>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={startIrrigation}>
                          <Play className="w-4 h-4 mr-1" /> {t("start")}
                        </Button>
                        <Button size="sm" variant="destructive" onClick={stopIrrigation}>
                          <Square className="w-4 h-4 mr-1" /> {t("stop")}
                        </Button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">{t("water_liters_total")}</div>
                        <div className="text-foreground font-medium">{recommendation.water_liters}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">{t("water_source")}</div>
                        <div className="text-foreground font-medium">{recommendation.water_source ?? '-'}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">{t("irrigation_cycles")}</div>
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
                        <div className="text-muted-foreground">{t("runtime_min")}</div>
                        <div className="text-foreground font-medium">{recommendation.suggested_runtime_min ?? '-'}</div>
                      </div>
                      {recommendation.best_time && (
                        <div>
                          <div className="text-muted-foreground">{t("best_time")}</div>
                          <div className="text-foreground font-medium">{recommendation.best_time}</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Impact Metrics */}
                  {(recommendation.expected_savings_liters != null || recommendation.expected_cost_saving_rs != null || recommendation.expected_co2e_kg != null) && (
                    <div className="border rounded-lg p-4 bg-card">
                      <div className="text-sm font-semibold mb-2">{t("impact")}</div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">{t("water_saved_l")}</div>
                          <div className="text-foreground font-medium">{Math.round(recommendation.expected_savings_liters || 0)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">{t("cost_saved_rs2")}</div>
                          <div className="text-foreground font-medium">{Math.round(recommendation.expected_cost_saving_rs || 0)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">{t("co2e_kg2")}</div>
                          <div className="text-foreground font-medium">{(recommendation.expected_co2e_kg || 0).toFixed(2)}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Fertilizer equivalents */}
                  {recommendation.fertilizer_equivalents && (
                    <div className="border rounded-lg p-4 bg-card">
                      <div className="text-sm font-semibold mb-2">{t("fertilizer_equivalents")}</div>
                      <ul className="text-sm grid grid-cols-2 gap-2">
                        {Object.entries(recommendation.fertilizer_equivalents).map(([k, v]) => (
                          <li key={k} className="flex justify-between">
                            <span className="text-muted-foreground">{k}</span>
                            <span className="font-medium">{v}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {/* Detailed Tips */}
                  {recommendation.tips && recommendation.tips.length > 0 && (
                    <div className="border rounded-lg p-4 bg-card">
                      <div className="text-sm font-semibold mb-2">{t("detailed_tips")}</div>
                      <ul className="list-disc ml-5 space-y-1 text-sm">
                        {recommendation.tips.map((tip, i) => (
                          <li key={i}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {recommendation.notes && recommendation.notes.length > 0 && (
                    <div className="border-l-4 p-4 rounded-lg bg-accent border-l-accent-foreground">
                      <div className="text-sm text-accent-foreground font-semibold mb-2">{t("notes")}</div>
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