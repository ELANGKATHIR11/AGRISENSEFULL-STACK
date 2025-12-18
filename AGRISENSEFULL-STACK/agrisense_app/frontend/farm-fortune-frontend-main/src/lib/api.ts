export type SensorReading = {
  plant?: string;
  soil_type?: string;
  area_m2?: number;
  ph?: number;
  moisture_pct?: number;
  temperature_c?: number;
  ec_dS_m?: number;
  n_ppm?: number;
  p_ppm?: number;
  k_ppm?: number;
};

export type BackendRecommendation = {
  water_liters: number;
  fert_n_g: number;
  fert_p_g: number;
  fert_k_g: number;
  water_source?: string; // "tank" | "groundwater"
  notes?: string[];
  tips?: string[];
  expected_savings_liters?: number;
  expected_cost_saving_rs?: number;
  expected_co2e_kg?: number;
  water_per_m2_l?: number;
  water_buckets_15l?: number;
  irrigation_cycles?: number;
  suggested_runtime_min?: number;
  assumed_flow_lpm?: number;
  best_time?: string;
  fertilizer_equivalents?: Record<string, number>;
  target_moisture_pct?: number;
};

// Determine API base URL
// Priority: explicit VITE_API_URL -> Vite dev proxy (any dev port) -> same-origin
type EnvShape = { VITE_API_URL?: string; DEV?: boolean };
const getViteEnv = (): EnvShape => {
  try {
    const meta = (import.meta as unknown) as { env?: EnvShape };
    return meta?.env ?? {};
  } catch {
    return {};
  }
};

const determineApiBase = (): string => {
  const env = getViteEnv();
  const fromEnv = env.VITE_API_URL;
  
  // In production or if explicit URL is set
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.trim();
  }
  
  // In development, use relative path (proxy will handle it)
  if (env.DEV) {
    return ""; // Empty string means use relative paths, which Vite proxy will handle
  }
  
  // Fallback to same-origin for production builds
  return "";
};

const API_BASE = determineApiBase();

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} ${text}`);
  }
  return (await res.json()) as T;
}

export type PlantListItem = { value: string; label: string; category?: string };

export type CropCard = {
  id: string;
  name: string;
  scientificName?: string | null;
  category?: string | null;
  season?: string | null;
  waterRequirement?: string | null; // Low|Medium|High
  tempRange?: string | null;
  phRange?: string | null;
  growthPeriod?: string | null;
  description?: string | null;
  tips: string[];
};

export type EdgeCaptureResponse = {
  reading: SensorReading & { zone_id: string };
  recommendation: BackendRecommendation;
};

export type TankStatus = { tank_id: string; level_pct?: number | null; volume_l?: number | null; last_update?: string | null; capacity_liters?: number | null };
export type IrrigationAck = { ok: boolean; status: string; note?: string };
export type AlertItem = { ts?: string; zone_id: string; category: string; message: string; sent: boolean };
export type ValveEvent = { ts: string; zone_id: string; action: "start" | "stop"; duration_s: number; status: string };
export type RainwaterSummary = { tank_id: string; collected_total_l: number; used_total_l: number; net_l: number };
export type RainwaterEntry = { ts: string; tank_id: string; collected_liters: number; used_liters: number };

// Dashboard summary & tank history
export type TankHistoryRow = { ts: string; tank_id: string; level_pct: number; volume_l: number; rainfall_mm: number };
export type DashboardSummary = {
  weather_latest?: WeatherCacheRow | null;
  soil_moisture_pct?: number | null;
  tank?: TankStatus | null;
  tank_history?: TankHistoryRow[];
  valve_events?: ValveEvent[];
  alerts?: AlertItem[];
  impact?: { saved_l: number; cost_rs: number; co2e_kg: number } | null;
};

// Weather cache latest record shape from backend
export type WeatherCacheRow = {
  date: string;
  doy: string;
  lat: string;
  lon: string;
  tmin_c: string;
  tmax_c: string;
  tmean_c: string;
  ra_mj_m2_day: string;
  et0_mm_day: string;
};

// Real-time sensor data types
export type LiveSensorData = {
  device_id: string;
  air_temperature: number;
  humidity: number;
  soil_moisture_percentage: number;
  soil_temperature: number;
  ph_level: number;
  light_intensity_percentage: number;
  timestamp: string;
};

export type DeviceStatus = {
  device_id: string;
  is_connected: boolean;
  last_seen: string;
  status: string;
};

export type LiveRecommendation = {
  status: string;
  timestamp: string;
  sensor_data: LiveSensorData;
  recommendations: BackendRecommendation;
  data_source: string;
  device_id: string;
};

export type LiveSoilAnalysis = {
  status: string;
  timestamp: string;
  sensor_data: LiveSensorData;
  soil_analysis: {
    moisture_status: string;
    moisture_percentage: number;
    temperature_status: string;
    temperature_celsius: number;
    ph_status: string;
    ph_level: number;
    recommendations: string[];
  };
  data_source: string;
  device_id: string;
};

// Arduino-specific types
export type ArduinoSensorData = {
  device_id: string;
  ds18b20_temp?: number | null;
  dht22_temp?: number | null;
  humidity?: number | null;
  sensor_status: {
    ds18b20: boolean;
    dht22: boolean;
  };
  zone_id: string;
  timestamp: string;
};

export type ArduinoStatus = {
  status: string;
  recent_readings: Array<{
    zone_id: string;
    temperature: number;
    timestamp: string;
  }>;
  last_reading_time?: string | null;
  total_devices: number;
  message?: string;
};

export const api = {
  health: () => http<{ status: string }>(`/api/health`),
  edgeHealth: () => http<{ status: string; edge_module?: boolean }>(`/api/edge/health`),
  plants: () => http<{ items: PlantListItem[] }>(`/api/plants`),
  crops: () => http<{ items: CropCard[] }>(`/api/crops`),
  soilTypes: () => http<{ items: string[] }>(`/api/soil/types`),
  adminWeatherRefresh: (lat: number, lon: number, days = 7) =>
    http<{ ok: boolean; cache_path: string; latest?: WeatherCacheRow }>(`/api/admin/weather/refresh`, {
      method: "POST",
      body: JSON.stringify({ lat, lon, days }),
    }),
  edgeCapture: (zone_id?: string) =>
    http<EdgeCaptureResponse>(`/api/edge/capture`, {
      method: "POST",
      body: JSON.stringify({ zone_id }),
    }),
  recommend: (payload: SensorReading) =>
    http<BackendRecommendation>(`/api/recommend`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recent: (zone = "Z1", limit = 100) =>
    http<{ items: Array<{ ts: string; zone_id: string; plant: string; soil_type: string; area_m2: number; ph: number; moisture_pct: number; temperature_c: number; ec_dS_m: number; n_ppm: number | null; p_ppm: number | null; k_ppm: number | null }> }>(
      `/api/recent?zone_id=${encodeURIComponent(zone)}&limit=${limit}`
    ),
  recoRecent: (zone = "Z1", limit = 200) =>
    http<{ items: Array<{ ts: string; zone_id: string; plant: string; water_liters?: number; expected_savings_liters?: number; fert_n_g?: number; fert_p_g?: number; fert_k_g?: number; yield_potential?: number | null; water_source?: string }> }>(
      `/api/reco/recent?zone_id=${encodeURIComponent(zone)}&limit=${limit}`
    ),
  recoLog: (zone_id: string, plant: string, rec: Partial<BackendRecommendation> & { water_liters?: number; expected_savings_liters?: number; fert_n_g?: number; fert_p_g?: number; fert_k_g?: number }, yield_potential?: number) =>
    http<{ ok: boolean }>(`/api/reco/log`, {
      method: "POST",
      body: JSON.stringify({ zone_id, plant, rec, yield_potential }),
    }),
  tankStatus: (tank_id = "T1") => http<TankStatus>(`/api/tank/status?tank_id=${encodeURIComponent(tank_id)}`),
  tankLevel: (tank_id: string, level_pct: number, volume_l: number, rainfall_mm?: number) =>
    http<{ ok: boolean }>(`/api/tank/level`, { method: "POST", body: JSON.stringify({ tank_id, level_pct, volume_l, rainfall_mm }) }),
  tankHistory: (tank_id = "T1", limit = 100, since?: string) =>
    http<{ items: TankHistoryRow[] }>(`/api/tank/history?tank_id=${encodeURIComponent(tank_id)}&limit=${limit}${since ? `&since=${encodeURIComponent(since)}` : ""}`),
  irrigationStart: (zone_id: string, duration_s?: number, force = false) =>
    http<IrrigationAck>(`/api/irrigation/start`, { method: "POST", body: JSON.stringify({ zone_id, duration_s, force }) }),
  irrigationStop: (zone_id: string) => http<IrrigationAck>(`/api/irrigation/stop`, { method: "POST", body: JSON.stringify({ zone_id }) }),
  valveEvents: (zone_id?: string, limit = 20) => http<{ items: ValveEvent[] }>(`/api/valves/events${zone_id ? `?zone_id=${encodeURIComponent(zone_id)}&limit=${limit}` : `?limit=${limit}`}`),
  alerts: (zone_id?: string, limit = 50) => http<{ items: AlertItem[] }>(`/api/alerts${zone_id ? `?zone_id=${encodeURIComponent(zone_id)}&limit=${limit}` : `?limit=${limit}`}`),
  alertCreate: (zone_id: string, category: string, message: string, sent = false) =>
    http<{ ok: boolean }>(`/api/alerts`, { method: "POST", body: JSON.stringify({ zone_id, category, message, sent }) }),
  alertAck: (ts: string) => http<{ ok: boolean }>(`/api/alerts/ack`, { method: "POST", body: JSON.stringify({ ts }) }),
  rainwaterSummary: (tank_id = "T1") => http<RainwaterSummary>(`/api/rainwater/summary?tank_id=${encodeURIComponent(tank_id)}`),
  rainwaterRecent: (tank_id = "T1", limit = 10) => http<{ items: RainwaterEntry[] }>(`/api/rainwater/recent?tank_id=${encodeURIComponent(tank_id)}&limit=${limit}`),
  rainwaterLog: (tank_id: string, collected_liters = 0, used_liters = 0) =>
    http<{ ok: boolean }>(`/api/rainwater/log`, { method: "POST", body: JSON.stringify({ tank_id, collected_liters, used_liters }) }),
  adminReset: () => http<{ ok: boolean }>(`/api/admin/reset`, { method: "POST" }),
  dashboardSummary: (zone_id = "Z1", tank_id = "T1", alerts_limit = 5, events_limit = 5) =>
    http<DashboardSummary>(`/api/dashboard/summary?zone_id=${encodeURIComponent(zone_id)}&tank_id=${encodeURIComponent(tank_id)}&alerts_limit=${alerts_limit}&events_limit=${events_limit}`),
  chatAsk: (message: string, zone_id = "Z1") =>
    http<{ answer: string; sources?: string[] }>(`/api/chat/ask`, {
      method: "POST",
      body: JSON.stringify({ message, zone_id }),
    }),
  
  // Real-time sensor data endpoints
  sensorsLive: (device_id?: string) => 
    http<{ status: string; timestamp: string; data: LiveSensorData | Record<string, LiveSensorData> }>(`/api/sensors/live${device_id ? `?device_id=${encodeURIComponent(device_id)}` : ""}`),
  sensorsDeviceStatus: () => 
    http<{ status: string; timestamp: string; devices: DeviceStatus[] }>(`/api/sensors/devices/status`),
  sensorsPumpControl: (device_id: string, action: "on" | "off") =>
    http<{ status: string; message: string; timestamp: string }>(`/api/sensors/pump/control`, {
      method: "POST", 
      body: JSON.stringify({ device_id, action })
    }),
  sensorsRecommendationsLive: (device_id?: string) =>
    http<LiveRecommendation>(`/api/sensors/recommendations/live${device_id ? `?device_id=${encodeURIComponent(device_id)}` : ""}`),
  sensorsSoilAnalysisLive: (device_id?: string) =>
    http<LiveSoilAnalysis>(`/api/sensors/soil-analysis/live${device_id ? `?device_id=${encodeURIComponent(device_id)}` : ""}`),
  
  // Arduino Nano API functions
  arduinoStatus: () => http<ArduinoStatus>(`/api/arduino/status`),
};
