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
  notes?: string[];
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
// Priority: explicit VITE_API_URL -> Vite dev proxy (when on port 8080) -> same-origin
const determineApiBase = (): string => {
  const fromEnv = import.meta.env.VITE_API_URL as string | undefined;
  if (fromEnv && fromEnv.trim().length > 0) return fromEnv.trim();
  // In Vite dev, the UI runs on port 8080. Default backend is uvicorn on 8004.
  if (typeof window !== "undefined") {
    const port = window.location.port;
    if (port === "8080") {
      // Use Vite dev proxy; see vite.config.{ts,mjs}
      return "/api";
    }
  }
  // Same-origin (works when UI is served by FastAPI under /ui in production)
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

export type TankStatus = { tank_id: string; level_pct?: number | null; volume_l?: number | null; last_update?: string | null };
export type IrrigationAck = { ok: boolean; status: string; note?: string };
export type AlertItem = { ts?: string; zone_id: string; category: string; message: string; sent: boolean };
export type ValveEvent = { ts: string; zone_id: string; action: "start" | "stop"; duration_s: number; status: string };

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

export const api = {
  health: () => http<{ status: string }>(`/health`),
  edgeHealth: () => http<{ status: string; edge_module?: boolean }>(`/edge/health`),
  plants: () => http<{ items: PlantListItem[] }>(`/plants`),
  crops: () => http<{ items: CropCard[] }>(`/crops`),
  adminWeatherRefresh: (lat: number, lon: number, days = 7) =>
    http<{ ok: boolean; cache_path: string; latest?: WeatherCacheRow }>(`/admin/weather/refresh`, {
      method: "POST",
      body: JSON.stringify({ lat, lon, days }),
    }),
  edgeCapture: (zone_id?: string) =>
    http<EdgeCaptureResponse>(`/edge/capture`, {
      method: "POST",
      body: JSON.stringify({ zone_id }),
    }),
  recommend: (payload: SensorReading) =>
    http<BackendRecommendation>(`/recommend`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  recent: (zone = "Z1", limit = 100) =>
    http<{ items: Array<{ ts: string; zone_id: string; plant: string; soil_type: string; area_m2: number; ph: number; moisture_pct: number; temperature_c: number; ec_dS_m: number; n_ppm: number | null; p_ppm: number | null; k_ppm: number | null }> }>(
      `/recent?zone_id=${encodeURIComponent(zone)}&limit=${limit}`
    ),
  recoRecent: (zone = "Z1", limit = 200) =>
    http<{ items: Array<{ ts: string; zone_id: string; plant: string; water_liters: number; expected_savings_liters: number; fert_n_g: number; fert_p_g: number; fert_k_g: number; yield_potential: number | null }> }>(
      `/reco/recent?zone_id=${encodeURIComponent(zone)}&limit=${limit}`
    ),
  recoLog: (zone_id: string, plant: string, rec: Partial<BackendRecommendation> & { water_liters?: number; expected_savings_liters?: number; fert_n_g?: number; fert_p_g?: number; fert_k_g?: number }, yield_potential?: number) =>
    http<{ ok: boolean }>(`/reco/log`, {
      method: "POST",
      body: JSON.stringify({ zone_id, plant, rec, yield_potential }),
    }),
  tankStatus: (tank_id = "T1") => http<TankStatus>(`/tank/status?tank_id=${encodeURIComponent(tank_id)}`),
  tankLevel: (tank_id: string, level_pct: number, volume_l: number, rainfall_mm?: number) =>
    http<{ ok: boolean }>(`/tank/level`, { method: "POST", body: JSON.stringify({ tank_id, level_pct, volume_l, rainfall_mm }) }),
  irrigationStart: (zone_id: string, duration_s?: number, force = false) =>
    http<IrrigationAck>(`/irrigation/start`, { method: "POST", body: JSON.stringify({ zone_id, duration_s, force }) }),
  irrigationStop: (zone_id: string) => http<IrrigationAck>(`/irrigation/stop`, { method: "POST", body: JSON.stringify({ zone_id }) }),
  valveEvents: (zone_id?: string, limit = 20) => http<{ items: ValveEvent[] }>(`/valves/events${zone_id ? `?zone_id=${encodeURIComponent(zone_id)}&limit=${limit}` : `?limit=${limit}`}`),
  alerts: (zone_id?: string, limit = 50) => http<{ items: AlertItem[] }>(`/alerts${zone_id ? `?zone_id=${encodeURIComponent(zone_id)}&limit=${limit}` : `?limit=${limit}`}`),
  alertCreate: (zone_id: string, category: string, message: string, sent = false) =>
    http<{ ok: boolean }>(`/alerts`, { method: "POST", body: JSON.stringify({ zone_id, category, message, sent }) }),
  adminReset: () => http<{ ok: boolean }>(`/admin/reset`, { method: "POST" }),
};
