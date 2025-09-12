const API_BASE = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '') || '';

export type TankStatus = { tank_id: string; level_pct?: number | null; volume_l?: number | null; last_update?: string | null };
export type BackendRecommendation = { water_liters?: number; water_source?: string; suggested_runtime_min?: number };

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as T;
}

export const api = {
  tankStatus: (tank_id = 'T1') => http<TankStatus>(`/tank/status?tank_id=${encodeURIComponent(tank_id)}`),
  irrigationStart: (zone_id: string, duration_s?: number) => http<{ ok: boolean; status: string }>(`/irrigation/start`, { method: 'POST', body: JSON.stringify({ zone_id, duration_s }) }),
  irrigationStop: (zone_id: string) => http<{ ok: boolean; status: string }>(`/irrigation/stop`, { method: 'POST', body: JSON.stringify({ zone_id }) }),
  recoRecent: (zone = 'Z1', limit = 1) => http<{ items: any[] }>(`/reco/recent?zone_id=${encodeURIComponent(zone)}&limit=${limit}`),
};
