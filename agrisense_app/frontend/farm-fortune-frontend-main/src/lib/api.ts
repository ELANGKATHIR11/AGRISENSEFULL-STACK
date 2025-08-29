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

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ""; // "" means same-origin

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

export const api = {
  health: () => http<{ status: string }>(`/health`),
  plants: () => http<{ items: PlantListItem[] }>(`/plants`),
  crops: () => http<{ items: CropCard[] }>(`/crops`),
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
};
