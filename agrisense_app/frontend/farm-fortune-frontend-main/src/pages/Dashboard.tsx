import { useCallback, useEffect, useMemo, useRef, useState, Suspense } from "react";
import { api, type TankStatus, type AlertItem, type WeatherCacheRow, type ValveEvent, type RainwaterSummary, type RainwaterEntry, type DashboardSummary, type LiveSensorData, type DeviceStatus, type ArduinoStatus } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { AgriSenseLogo, AgriSenseIcon } from "../components/AgriSenseLogo";
import { motion, AnimatePresence } from "framer-motion";
import FarmScene from "../components/3d/FarmScene";
import { 
  Droplets, 
  Thermometer, 
  AlertTriangle, 
  CloudSun, 
  Check, 
  RefreshCw, 
  Activity, 
  TrendingUp, 
  Zap,
  Brain,
  Wifi,
  Cpu,
  Leaf,
  BarChart3,
  Sprout,
  Gauge,
  Smartphone,
  Cloud,
  TreePine,
  Beaker
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import TankGauge from "../components/TankGauge";
import { LoadingSpinner, LoadingOverlay } from "../components/ui/loading-spinner";
import { useTranslation } from "react-i18next";

export default function Dashboard() {
  const { toast } = useToast();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [showAck, setShowAck] = useState(false);
  const [latestWeather, setLatestWeather] = useState<WeatherCacheRow | null>(null);
  const [soilMoisture, setSoilMoisture] = useState<number | null>(null);
  const [impact, setImpact] = useState<{ saved_l: number; cost_rs: number; co2e_kg: number } | null>(null);
  const [valveEvents, setValveEvents] = useState<ValveEvent[]>([]);
  const [rain, setRain] = useState<RainwaterSummary | null>(null);
  const [rainRecent, setRainRecent] = useState<RainwaterEntry[]>([]);
  const [tankHistory, setTankHistory] = useState<number[]>([]);
  const lastUpdateRef = useRef<HTMLSpanElement | null>(null);
  const HISTORY_KEY = "dashboard.tankHistory";
  
  // Live sensor data state
  const [liveSensorData, setLiveSensorData] = useState<LiveSensorData | null>(null);
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus[]>([]);
  const [arduinoStatus, setArduinoStatus] = useState<ArduinoStatus | null>(null);
  const [sensorHistory, setSensorHistory] = useState<{
    timestamp: string;
    temperature: number;
    humidity: number;
    soilMoisture: number;
    ph: number;
    lightIntensity: number;
  }[]>([]);
  
  // Load persisted history on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) {
        const arr = JSON.parse(raw);
        if (Array.isArray(arr)) {
          const sanitized = arr
            .map((v) => Number(v))
            .filter((v) => Number.isFinite(v))
            .map((v) => Math.max(0, Math.min(100, v)));
          setTankHistory(sanitized.slice(-20));
        }
      }
    } catch {
      // ignore localStorage/JSON errors
    }
  }, [HISTORY_KEY]);

  const lat = useMemo(() => Number(localStorage.getItem("lat") || "27.3"), []);
  const lon = useMemo(() => Number(localStorage.getItem("lon") || "88.6"), []);

  // Helper function to get current Arduino temperature
  const getCurrentArduinoTemperature = useCallback(() => {
    if (arduinoStatus?.recent_readings && arduinoStatus.recent_readings.length > 0) {
      return arduinoStatus.recent_readings[0].temperature;
    }
    return liveSensorData?.air_temperature || null;
  }, [arduinoStatus, liveSensorData]);

  // Helper function to get temperature status text
  const getTemperatureStatus = useCallback((temp: number | null) => {
    if (!temp) return 'No Data Available';
    if (temp > 30) return '🔥 High Temperature';
    if (temp < 15) return '❄️ Cool Temperature';
    if (temp > 25) return '🌡️ Warm Temperature';
    return '🌿 Optimal Temperature';
  }, []);

  const refreshAll = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    setLoading(true);
    try {
      // Fetch aggregated summary, rainwater data, live sensor data, and Arduino status in parallel
      const [summary, rw, rwRecent, sensorResponse, deviceResponse, arduinoResponse] = await Promise.all([
        api.dashboardSummary("Z1", "T1", 5, 5).catch(() => null),
        api.rainwaterSummary("T1").catch(() => null),
        api.rainwaterRecent("T1", 5).then(x => x.items).catch(() => []),
        api.sensorsLive().catch(() => null),
        api.sensorsDeviceStatus().catch(() => null),
        api.arduinoStatus().catch(() => null),
      ]);

      // Update live sensor data
      const sensorData = sensorResponse?.data as LiveSensorData | null;
      const devices = deviceResponse?.devices || [];
      setLiveSensorData(sensorData);
      setDeviceStatus(devices);
      setArduinoStatus(arduinoResponse);
      
      // Priority: Use Arduino temperature if available, fallback to general sensor data
      let currentTemperature = sensorData?.air_temperature || 0;
      if (arduinoResponse?.recent_readings && arduinoResponse.recent_readings.length > 0) {
        currentTemperature = arduinoResponse.recent_readings[0].temperature;
      }
      
      // Add to sensor history for charting
      if (sensorData || (arduinoResponse?.recent_readings && arduinoResponse.recent_readings.length > 0)) {
        const newDataPoint = {
          timestamp: new Date().toISOString(),
          temperature: currentTemperature,
          humidity: sensorData?.humidity || 0,
          soilMoisture: sensorData?.soil_moisture_percentage || 0,
          ph: sensorData?.ph_level || 0,
          lightIntensity: sensorData?.light_intensity_percentage || 0,
        };
        
        setSensorHistory(prev => {
          const updated = [...prev, newDataPoint].slice(-50); // Keep last 50 readings
          return updated;
        });
      }

      if (summary) {
        setTank((summary.tank as TankStatus) || null);
        setAlerts(summary.alerts || []);
        setValveEvents(summary.valve_events || []);
        setSoilMoisture(summary.soil_moisture_pct ?? null);
        setLatestWeather(summary.weather_latest ?? null);
        setImpact(summary.impact ?? null);
        // Use backend history if present, else append current level locally
        const hist = Array.isArray(summary.tank_history) ? summary.tank_history : [];
        if (hist.length > 0) {
          // Backend returns DESC; convert to chronological order and clamp to last 20
          const pct = hist
            .slice(0, 20)
            .reverse()
            .map((row) => Math.max(0, Math.min(100, Number(row.level_pct) || 0)));
          setTankHistory(pct);
          try { localStorage.setItem(HISTORY_KEY, JSON.stringify(pct)); } catch { /* ignore quota errors */ }
        } else if (summary.tank && typeof (summary.tank as TankStatus).level_pct === 'number') {
          // Append the current level to local history
          const currentLevel = Math.max(0, Math.min(100, (summary.tank as TankStatus).level_pct!));
          setTankHistory(prev => {
            const updated = [...prev, currentLevel].slice(-20);
            try { localStorage.setItem(HISTORY_KEY, JSON.stringify(updated)); } catch { /* ignore */ }
            return updated;
          });
        }
      }
      setRain(rw);
      setRainRecent(rwRecent);
    } catch (error) {
      console.error("Dashboard refresh error:", error);
    } finally {
      setLoading(false);
      if (showSpinner) setRefreshing(false);
    }
  }, [HISTORY_KEY]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const handleAckAlerts = useCallback(async (alertTs: string) => {
    setShowAck(true);
    try {
      await api.alertAck(alertTs);
      await refreshAll();
      toast({
        title: t("success"),
        description: t("alerts_acknowledged"),
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: t("error"),
        description: t("failed_to_acknowledge_alerts"),
      });
    } finally {
      setShowAck(false);
    }
  }, [t, toast, refreshAll]);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-8 p-4 md:p-6 lg:p-8 bg-gradient-to-br from-green-50 via-white to-emerald-50 min-h-screen"
    >
      {/* 3D Farm Visualization */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-sky-100 to-green-100 shadow-2xl h-96 mb-8"
      >
        <Suspense fallback={
          <div className="flex items-center justify-center h-full bg-gradient-to-br from-sky-100 to-green-100">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p className="text-green-700 font-medium">Loading 3D Farm Scene...</p>
            </div>
          </div>
        }>
          <FarmScene 
            sensorData={{
              temperature: getCurrentArduinoTemperature() || liveSensorData?.air_temperature || 25,
              humidity: liveSensorData?.humidity || 65,
              soilMoisture: liveSensorData?.soil_moisture_percentage || soilMoisture || 45,
              lightIntensity: liveSensorData?.light_intensity_percentage || 80
            }}
            irrigationActive={valveEvents[0]?.action === "start" && (valveEvents[0]?.status === "sent" || valveEvents[0]?.status === "queued")}
            className="w-full h-full"
          />
        </Suspense>
      </motion.div>

      {/* Modern AgriSense Header */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 p-8 text-white shadow-2xl"
      >
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full transform translate-x-32 -translate-y-32"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="p-4 bg-white/20 rounded-2xl backdrop-blur-sm">
                <AgriSenseIcon size="sm" className="text-white" />
              </div>
              <div>
                <div className="mb-4">
                  <AgriSenseLogo variant="dark" size="lg" />
                </div>
                <div className="flex items-center gap-4 text-green-100">
                  <span className="flex items-center gap-2">
                    <Brain className="w-5 h-5" />
                    AI-Powered Analytics
                  </span>
                  <span className="flex items-center gap-2">
                    <Wifi className="w-5 h-5" />
                    IoT Connected
                  </span>
                  <span className="flex items-center gap-2">
                    <Leaf className="w-5 h-5" />
                    Smart Agriculture
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-green-100 text-sm">System Status</div>
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <div className="w-3 h-3 bg-green-300 rounded-full animate-pulse"></div>
                  All Systems Online
                </div>
              </div>
              <Button
                onClick={() => refreshAll(true)}
                disabled={refreshing}
                className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm"
                size="lg"
              >
                {refreshing ? (
                  <LoadingSpinner className="w-5 h-5 mr-2" />
                ) : (
                  <RefreshCw className="w-5 h-5 mr-2" />
                )}
                {refreshing ? t("refreshing") : t("refresh")}
              </Button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Primary Metrics Row */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8"
      >
        
        {/* Enhanced Tank Level Card */}
        <motion.div
          whileHover={{ scale: 1.02, y: -5 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-3 text-green-700">
                <div className="p-2 bg-gradient-to-br from-blue-100 to-teal-100 rounded-lg">
                  <Droplets className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <span className="text-lg">{t("tank_level")}</span>
                  <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                    <Gauge className="w-3 h-3" />
                    Real-time Monitoring
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-8 w-32" />
                  <Skeleton className="h-6 w-24" />
                </div>
              ) : tank ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gradient-to-r from-blue-50 to-teal-50 p-3 rounded-lg">
                      <div className="text-teal-600 font-semibold">{t("level")}</div>
                      <div className="text-2xl font-bold text-teal-800">
                        {tank.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : "—"}
                      </div>
                    </div>
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg">
                      <div className="text-emerald-600 font-semibold">{t("tank_volume")}</div>
                      <div className="text-2xl font-bold text-emerald-800">
                        {tank.volume_l != null ? `${Math.round(tank.volume_l)} L` : "—"}
                      </div>
                    </div>
                  </div>
                  
                  {/* Smart Status Indicators */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">{t("updated")}:</span>
                    <span 
                      ref={lastUpdateRef} 
                      className="text-xs px-3 py-1 rounded-full bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200" 
                      title={tank.last_update || ''}
                    >
                      {tank.last_update ? new Date(tank.last_update).toLocaleTimeString() : "—"}
                    </span>
                  </div>
                  
                  {/* Valve Status with Enhanced Design */}
                  <div className="flex items-center gap-2">
                    {valveEvents[0] ? (
                      <span className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg ${
                        valveEvents[0].action === "start" && (valveEvents[0].status === "sent" || valveEvents[0].status === "queued") 
                          ? "bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200" 
                          : "bg-gradient-to-r from-gray-100 to-slate-100 text-gray-700 border border-gray-200"
                      }`}>
                        <Activity className="w-4 h-4" />
                        {valveEvents[0].action === "start" && (valveEvents[0].status === "sent" || valveEvents[0].status === "queued") 
                          ? "🌊 Irrigation Active" 
                          : "💧 Standby"}
                      </span>
                    ) : null}
                  </div>

                  {/* Tank History Chart */}
                  {tankHistory.length > 1 && (
                    <div className="mt-3 bg-gradient-to-br from-blue-50 to-teal-50 p-2 rounded-lg">
                      <div className="text-xs text-teal-600 font-semibold mb-1">Tank Level History</div>
                      <svg width="120" height="24" viewBox="0 0 120 24" className="w-full h-6">
                        <title>{(() => {
                          const pts = tankHistory;
                          const n = pts.length;
                          const last = (pts[n - 1] ?? 0).toFixed(0);
                          const min = Math.min(...pts).toFixed(0);
                          const max = Math.max(...pts).toFixed(0);
                          const avg = (pts.reduce((a,b)=>a+b,0)/n).toFixed(0);
                          return `Last ${n}: ${last}% • min ${min}% • max ${max}% • avg ${avg}%`;
                        })()}</title>
                        {(() => {
                          const pts = tankHistory;
                          const n = pts.length;
                          const maxX = 119;
                          const maxY = 23;
                          const path = pts
                            .map((v, i) => {
                              const x = Math.round((i / (n - 1)) * maxX);
                              const y = Math.round(maxY - (v / 100) * maxY);
                              return `${i === 0 ? 'M' : 'L'}${x},${y}`;
                            })
                            .join(' ');
                          return (
                            <>
                              <path d={path} stroke="#0ea5e9" strokeWidth="2" fill="none" />
                              <path d={`${path} L120,24 L0,24 Z`} fill="url(#gradient)" opacity="0.2" />
                              <defs>
                                <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                  <stop offset="0%" stopColor="#0ea5e9" />
                                  <stop offset="100%" stopColor="#14b8a6" />
                                </linearGradient>
                              </defs>
                            </>
                          );
                        })()}
                      </svg>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  {t("no_data")}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* AI Insights Card */}
        <motion.div
          whileHover={{ scale: 1.02, y: -5 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-3 text-green-700">
                <div className="p-2 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-lg">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <span className="text-lg">AI Insights</span>
                  <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                    <BarChart3 className="w-3 h-3" />
                    Smart Analysis
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : soilMoisture !== null ? (
                <div className="space-y-3">
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg">
                    <div className="text-emerald-600 font-semibold text-sm">Soil Moisture</div>
                    <div className="text-2xl font-bold text-emerald-800">{soilMoisture.toFixed(0)}%</div>
                    <MoistureTrafficLight value={soilMoisture} t={t} />
                  </div>
                  {impact && (
                    <div className="grid grid-cols-1 gap-2 text-xs">
                      <div className="bg-blue-50 p-2 rounded-lg flex items-center justify-between">
                        <span className="text-blue-600">Water Saved</span>
                        <span className="font-bold text-blue-800">{impact.saved_l.toFixed(0)}L</span>
                      </div>
                      <div className="bg-green-50 p-2 rounded-lg flex items-center justify-between">
                        <span className="text-green-600">Cost Saved</span>
                        <span className="font-bold text-green-800">₹{impact.cost_rs.toFixed(0)}</span>
                      </div>
                      <div className="bg-emerald-50 p-2 rounded-lg flex items-center justify-between">
                        <span className="text-emerald-600">CO2 Reduced</span>
                        <span className="font-bold text-emerald-800">{impact.co2e_kg.toFixed(1)}kg</span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-500 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  {t("no_data")}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Arduino Live Temperature Section */}
      <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl transition-all duration-300 mb-8">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-green-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg">
                <Cpu className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <span className="text-lg">Arduino Live Temperature</span>
                <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  Direct Hardware Reading
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${arduinoStatus?.status === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {arduinoStatus?.status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {(arduinoStatus && (arduinoStatus.recent_readings?.length > 0 || liveSensorData)) ? (
            <div className="space-y-6">
              {/* Large Temperature Display */}
              <div className="bg-gradient-to-br from-red-50 via-orange-50 to-red-100 p-6 rounded-xl border-2 border-red-200 text-center">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <Thermometer className="w-8 h-8 text-red-600" />
                  <span className="text-xl font-semibold text-red-800">Arduino Temperature</span>
                </div>
                <div className="text-6xl font-bold text-red-900 mb-2">
                  {getCurrentArduinoTemperature()?.toFixed(1) || 'N/A'}
                  <span className="text-3xl">°C</span>
                </div>
                <div className="text-lg text-red-700 mb-4">
                  {getTemperatureStatus(getCurrentArduinoTemperature())}
                </div>
                <div className="text-sm text-red-600 bg-white/50 px-3 py-1 rounded-full inline-block">
                  Last Update: {arduinoStatus?.last_reading_time ? new Date(arduinoStatus.last_reading_time).toLocaleString() : 'Never'}
                </div>
                {arduinoStatus?.recent_readings && arduinoStatus.recent_readings.length > 0 && (
                  <div className="text-xs text-red-500 mt-2">
                    📡 Direct from Arduino Nano • Zone: {arduinoStatus.recent_readings[0].zone_id}
                  </div>
                )}
              </div>

              {/* Arduino Status Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Wifi className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">Connection Status</span>
                  </div>
                  <div className="text-lg font-bold text-blue-900">
                    {arduinoStatus?.status === 'active' ? '✅ Active' : 
                     arduinoStatus?.status === 'inactive' ? '⚠️ Inactive' : '❌ Error'}
                  </div>
                  <div className="text-xs text-blue-600 mt-1">
                    Devices: {arduinoStatus?.total_devices || 0}
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <BarChart3 className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Data Quality</span>
                  </div>
                  <div className="text-lg font-bold text-green-900">
                    {getCurrentArduinoTemperature() ? '📊 Live Data' : '⚠️ No Data'}
                  </div>
                  <div className="text-xs text-green-600 mt-1">
                    Arduino temperature sensor
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Gauge className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-800">Temperature Range</span>
                  </div>
                  <div className="text-lg font-bold text-purple-900">
                    {getCurrentArduinoTemperature() ? 
                      `${(getCurrentArduinoTemperature()! - 2).toFixed(1)}° - ${(getCurrentArduinoTemperature()! + 2).toFixed(1)}°C` : 
                      'N/A'
                    }
                  </div>
                  <div className="text-xs text-purple-600 mt-1">
                    ±2°C variation
                  </div>
                </div>
              </div>

              {/* Temperature History Trend */}
              {sensorHistory.length > 0 && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-3 flex items-center space-x-2 text-gray-700">
                    <TrendingUp className="w-4 h-4" />
                    <span>Recent Temperature Readings</span>
                  </h4>
                  <div className="flex space-x-2 overflow-x-auto">
                    {sensorHistory.slice(-10).map((reading, index) => (
                      <div key={index} className="flex-shrink-0 bg-white p-2 rounded border text-center min-w-[80px]">
                        <div className="text-sm font-bold text-red-600">
                          {reading.temperature.toFixed(1)}°C
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(reading.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-500 mb-4">
                <Cpu className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-lg">Arduino Not Connected</p>
                <p className="text-sm">Connect your Arduino temperature sensor to see live readings</p>
              </div>
              <Button
                onClick={() => refreshAll(true)}
                disabled={refreshing}
                variant="outline"
                className="text-green-600 border-green-200 hover:bg-green-50"
              >
                {refreshing ? (
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Check Connection
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Live Sensor Data Visualization */}
      <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl transition-all duration-300 mb-8">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-green-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <span className="text-lg">Live Sensor Monitoring</span>
                <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  Real-time IoT Data
                </div>
              </div>
            </div>
            <Button
              onClick={() => refreshAll(true)}
              disabled={refreshing}
              variant="outline"
              size="sm"
              className="text-green-600 border-green-200 hover:bg-green-50"
            >
              {refreshing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {liveSensorData ? (
            <div className="space-y-6">
              {/* Current Sensor Readings */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-lg border border-red-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Thermometer className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-800">Temperature</span>
                  </div>
                  <div className="text-2xl font-bold text-red-900">
                    {liveSensorData.air_temperature?.toFixed(1) || 'N/A'}°C
                  </div>
                  <div className="text-xs text-red-600 mt-1">
                    {liveSensorData.air_temperature && liveSensorData.air_temperature > 30 ? 'High' : 
                     liveSensorData.air_temperature && liveSensorData.air_temperature < 15 ? 'Low' : 'Normal'}
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Cloud className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">Humidity</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-900">
                    {liveSensorData.humidity?.toFixed(1) || 'N/A'}%
                  </div>
                  <div className="text-xs text-blue-600 mt-1">
                    {liveSensorData.humidity && liveSensorData.humidity > 70 ? 'High' : 
                     liveSensorData.humidity && liveSensorData.humidity < 30 ? 'Low' : 'Normal'}
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg border border-green-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Droplets className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Soil Moisture</span>
                  </div>
                  <div className="text-2xl font-bold text-green-900">
                    {liveSensorData.soil_moisture_percentage?.toFixed(1) || 'N/A'}%
                  </div>
                  <div className="text-xs text-green-600 mt-1">
                    {liveSensorData.soil_moisture_percentage && liveSensorData.soil_moisture_percentage > 60 ? 'Wet' : 
                     liveSensorData.soil_moisture_percentage && liveSensorData.soil_moisture_percentage < 30 ? 'Dry' : 'Optimal'}
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg border border-purple-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <Beaker className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-800">pH Level</span>
                  </div>
                  <div className="text-2xl font-bold text-purple-900">
                    {liveSensorData.ph_level?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-xs text-purple-600 mt-1">
                    {liveSensorData.ph_level && liveSensorData.ph_level > 7.5 ? 'Alkaline' : 
                     liveSensorData.ph_level && liveSensorData.ph_level < 6.5 ? 'Acidic' : 'Neutral'}
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 p-4 rounded-lg border border-yellow-200">
                  <div className="flex items-center space-x-2 mb-2">
                    <CloudSun className="w-4 h-4 text-yellow-600" />
                    <span className="text-sm font-medium text-yellow-800">Light</span>
                  </div>
                  <div className="text-2xl font-bold text-yellow-900">
                    {liveSensorData.light_intensity_percentage ? liveSensorData.light_intensity_percentage.toFixed(1) : 'N/A'}%
                  </div>
                  <div className="text-xs text-yellow-600 mt-1">
                    {liveSensorData.light_intensity_percentage && liveSensorData.light_intensity_percentage > 80 ? 'Bright' : 
                     liveSensorData.light_intensity_percentage && liveSensorData.light_intensity_percentage < 20 ? 'Low' : 'Normal'} light
                  </div>
                </div>
              </div>

              {/* Device Status */}
              {deviceStatus.length > 0 && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3 flex items-center space-x-2 text-gray-700">
                    <Cpu className="w-4 h-4" />
                    <span>Device Status</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {deviceStatus.map((device, index) => (
                      <div key={index} className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${
                        device.status === 'online' 
                          ? 'bg-green-50 border-green-200 text-green-800' 
                          : 'bg-red-50 border-red-200 text-red-800'
                      }`}>
                        {device.status === 'online' ? <Wifi className="w-3 h-3" /> : <Smartphone className="w-3 h-3" />}
                        <span className="text-sm font-medium">{device.device_id}</span>
                        <span className="text-xs opacity-75">
                          {device.last_seen ? new Date(device.last_seen).toLocaleTimeString() : 'Never'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Simple Chart for Sensor History */}
              {sensorHistory.length > 5 && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3 flex items-center space-x-2 text-gray-700">
                    <TrendingUp className="w-4 h-4" />
                    <span>Sensor Trends (Last Hour)</span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Temperature Chart */}
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <div className="text-sm font-medium text-red-800 mb-2">Temperature Trend</div>
                      <div className="h-20 relative">
                        <svg className="w-full h-full" viewBox="0 0 300 60">
                          <polyline
                            fill="none"
                            stroke="#dc2626"
                            strokeWidth="2"
                            points={sensorHistory.slice(-20).map((point, i) => 
                              `${(i / 19) * 300},${60 - ((point.temperature - 15) / 20) * 60}`
                            ).join(' ')}
                          />
                        </svg>
                      </div>
                      <div className="text-xs text-red-600 mt-1">
                        Min: {Math.min(...sensorHistory.slice(-20).map(p => p.temperature)).toFixed(1)}°C • 
                        Max: {Math.max(...sensorHistory.slice(-20).map(p => p.temperature)).toFixed(1)}°C
                      </div>
                    </div>

                    {/* Soil Moisture Chart */}
                    <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                      <div className="text-sm font-medium text-green-800 mb-2">Soil Moisture Trend</div>
                      <div className="h-20 relative">
                        <svg className="w-full h-full" viewBox="0 0 300 60">
                          <polyline
                            fill="none"
                            stroke="#16a34a"
                            strokeWidth="2"
                            points={sensorHistory.slice(-20).map((point, i) => 
                              `${(i / 19) * 300},${60 - (point.soilMoisture / 100) * 60}`
                            ).join(' ')}
                          />
                        </svg>
                      </div>
                      <div className="text-xs text-green-600 mt-1">
                        Min: {Math.min(...sensorHistory.slice(-20).map(p => p.soilMoisture)).toFixed(1)}% • 
                        Max: {Math.max(...sensorHistory.slice(-20).map(p => p.soilMoisture)).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="mb-4">
                <Smartphone className="w-12 h-12 text-gray-400 mx-auto" />
              </div>
              <p className="text-gray-600 mb-4">No live sensor data available</p>
              <p className="text-sm text-gray-500 mb-4">Connect your ESP32 sensors to see real-time data</p>
              <Button onClick={() => refreshAll(true)} disabled={refreshing} variant="outline">
                {refreshing ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Wifi className="w-4 h-4 mr-2" />
                )}
                Try Connect
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Arduino Nano Temperature Sensors */}
      <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl transition-all duration-300 mb-8">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-green-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg">
                <Cpu className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <span className="text-lg">Arduino Nano Sensors</span>
                <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  Wired Temperature Monitoring
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                arduinoStatus?.status === 'active' ? 'bg-green-500' : 
                arduinoStatus?.status === 'inactive' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-xs text-gray-600">
                {arduinoStatus?.total_devices || 0} device(s)
              </span>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {arduinoStatus && arduinoStatus.recent_readings.length > 0 ? (
            <div className="space-y-4">
              {/* Arduino Status Summary */}
              <div className="bg-gradient-to-br from-orange-50 to-red-50 p-4 rounded-lg border border-orange-200">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-5 h-5 text-orange-600" />
                    <span className="font-medium text-orange-800">Arduino Temperature Sensors</span>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    arduinoStatus.status === 'active' ? 'bg-green-100 text-green-800' :
                    arduinoStatus.status === 'inactive' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {arduinoStatus.status}
                  </span>
                </div>
                
                {/* Recent Readings */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {arduinoStatus.recent_readings.slice(0, 6).map((reading, idx) => (
                    <div key={idx} className="bg-white p-3 rounded-md border border-orange-100">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-lg font-bold text-orange-900">
                            {reading.temperature.toFixed(1)}°C
                          </div>
                          <div className="text-xs text-orange-600">
                            {reading.zone_id}
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(reading.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {arduinoStatus.last_reading_time && (
                  <div className="mt-3 text-xs text-gray-600">
                    Last update: {new Date(arduinoStatus.last_reading_time).toLocaleString()}
                  </div>
                )}
              </div>
              
              {/* Arduino Connection Instructions */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="flex items-start gap-3">
                  <div className="p-1 bg-blue-100 rounded">
                    <Cpu className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-800 mb-2">Arduino Setup Guide</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Upload the AgriSense firmware to your Arduino Nano</li>
                      <li>• Connect DS18B20 or DHT22 temperature sensors</li>
                      <li>• Run the Python serial bridge script</li>
                      <li>• Data will appear here automatically</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="mb-4">
                <Cpu className="w-12 h-12 text-gray-400 mx-auto" />
              </div>
              <p className="text-gray-600 mb-4">No Arduino sensors connected</p>
              <p className="text-sm text-gray-500 mb-4">
                Connect your Arduino Nano with temperature sensors to see real-time data
              </p>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 text-left max-w-md mx-auto">
                <h4 className="font-medium text-gray-800 mb-2">Quick Setup:</h4>
                <ol className="text-sm text-gray-600 space-y-1">
                  <li>1. Flash Arduino firmware</li>
                  <li>2. Connect sensors (DS18B20/DHT22)</li>
                  <li>3. Run Python bridge script</li>
                  <li>4. Monitor temperature data here</li>
                </ol>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Secondary Metrics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        
        {/* Enhanced Alerts Card */}
        <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-3 text-green-700">
              <div className="p-2 bg-gradient-to-br from-red-100 to-orange-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <span className="text-lg">{t("alerts")}</span>
                <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  System Monitoring
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-32" />
              </div>
            ) : alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.slice(0, 3).map((alert, i) => (
                  <div 
                    key={i} 
                    className={`p-3 rounded-lg border-l-4 ${
                      alert.category === "error" 
                        ? "bg-red-50 border-red-500 text-red-800" 
                        : alert.category === "warning"
                        ? "bg-orange-50 border-orange-500 text-orange-800"
                        : "bg-blue-50 border-blue-500 text-blue-800"
                    }`}
                  >
                    <div className="font-semibold text-sm">{alert.category.toUpperCase()}</div>
                    <div className="text-sm">{alert.message}</div>
                    <div className="text-xs opacity-75 mt-1">
                      {alert.ts ? new Date(alert.ts).toLocaleString() : "No timestamp"}
                    </div>
                  </div>
                ))}
                {alerts.length > 3 && (
                  <div className="text-center">
                    <Button variant="outline" size="sm" className="text-green-600 border-green-200 hover:bg-green-50">
                      View All {alerts.length} Alerts
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-500 flex items-center gap-2 bg-green-50 p-4 rounded-lg">
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-green-600">All systems operational</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Enhanced Rainwater Card */}
        <Card className="smart-card glass-card border-0 shadow-xl hover:shadow-2xl">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-3 text-green-700">
              <div className="p-2 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-lg">
                <CloudSun className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <span className="text-lg">{t("rainwater")}</span>
                <div className="text-xs text-green-600 font-normal flex items-center gap-1">
                  <Droplets className="w-3 h-3" />
                  Water Conservation
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-4">
            {rain ? (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 p-3 rounded-lg text-center">
                  <div className="text-blue-600 font-semibold text-sm">{t("collected_total")}</div>
                  <div className="text-xl font-bold text-blue-800">{Math.round(rain.collected_total_l)}L</div>
                </div>
                <div className="bg-gradient-to-r from-orange-50 to-red-50 p-3 rounded-lg text-center">
                  <div className="text-orange-600 font-semibold text-sm">{t("used_total")}</div>
                  <div className="text-xl font-bold text-orange-800">{Math.round(rain.used_total_l)}L</div>
                </div>
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg text-center">
                  <div className="text-emerald-600 font-semibold text-sm">{t("net_balance")}</div>
                  <div className={`text-xl font-bold ${rain.net_l >= 0 ? "text-emerald-800" : "text-red-800"}`}>
                    {Math.round(rain.net_l)}L
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-4">{t("no_data")}</div>
            )}
            
            {/* Quick Entry Form */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm font-semibold text-gray-700 mb-3">Quick Entry</div>
              <div className="flex items-end gap-2">
                <div className="flex flex-col flex-1">
                  <label className="text-xs text-gray-600 mb-1" htmlFor="rw_col">{t("collected_liters")}</label>
                  <input 
                    id="rw_col" 
                    type="number" 
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500" 
                    placeholder="0" 
                    min={0} 
                  />
                </div>
                <div className="flex flex-col flex-1">
                  <label className="text-xs text-gray-600 mb-1" htmlFor="rw_used">{t("used_liters")}</label>
                  <input 
                    id="rw_used" 
                    type="number" 
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500" 
                    placeholder="0" 
                    min={0} 
                  />
                </div>
                <Button 
                  size="sm" 
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2"
                  onClick={async () => {
                    const colEl = document.getElementById("rw_col") as HTMLInputElement | null;
                    const usedEl = document.getElementById("rw_used") as HTMLInputElement | null;
                    const col = Number(colEl?.value || "0");
                    const used = Number(usedEl?.value || "0");
                    if (!(Number.isFinite(col) && col >= 0)) {
                      colEl?.focus();
                      return;
                    }
                    if (!(Number.isFinite(used) && used >= 0)) {
                      usedEl?.focus();
                      return;
                    }
                    await api.rainwaterLog("T1", col, used);
                    await refreshAll();
                    if (colEl) colEl.value = "";
                    if (usedEl) usedEl.value = "";
                  }}
                >
                  {t("add")}
                </Button>
              </div>
            </div>

            {/* Recent Entries */}
            {rainRecent.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm font-semibold text-gray-700 mb-2">{t("recent_entries") ?? "Recent entries"}</div>
                <div className="space-y-2 max-h-24 overflow-y-auto">
                  {rainRecent.map((e, i) => (
                    <div key={i} className="flex items-center justify-between text-sm bg-white p-2 rounded border">
                      <span className="text-gray-600">{new Date(e.ts).toLocaleTimeString()}</span>
                      <span className="font-medium">+{Math.round(e.collected_liters)}L / -{Math.round(e.used_liters)}L</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Loading Overlay */}
      {refreshing && (
        <LoadingOverlay isLoading={true} text="Syncing smart farm data...">
          <div />
        </LoadingOverlay>
      )}
    </motion.div>
  );
}

function MoistureTrafficLight({ value, t }: { value: number; t: (k: string) => string }) {
  // Thresholds: <20 low (red), 20-60 moderate (amber), >60 healthy (green)
  const status = value < 20 ? "low" : value < 60 ? "moderate" : "healthy";
  const color = status === "low" ? "bg-red-500" : status === "moderate" ? "bg-amber-500" : "bg-emerald-500";
  const label = status === "low" ? t("low_level") : status === "moderate" ? t("moderate") : t("healthy");
  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block w-3 h-3 rounded-full ${color}`} />
      <span className="text-sm text-muted-foreground">{label}</span>
    </div>
  );
}