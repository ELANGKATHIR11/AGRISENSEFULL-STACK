import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type TankStatus, type AlertItem, type WeatherCacheRow, type ValveEvent, type RainwaterSummary, type RainwaterEntry, type DashboardSummary } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { Droplets, Thermometer, AlertTriangle, CloudSun, Check } from "lucide-react";
import { useToast } from "../hooks/use-toast";
import TankGauge from "../components/TankGauge";
import { useI18n } from "../i18n";

export default function Dashboard() {
  const { toast } = useToast();
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
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

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch aggregated summary and rainwater bits in parallel
      const [summary, rw, rwRecent] = await Promise.all([
        api.dashboardSummary("Z1", "T1", 5, 5).catch(() => null),
        api.rainwaterSummary("T1").catch(() => null),
        api.rainwaterRecent("T1", 5).then(x => x.items).catch(() => []),
      ]);

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
          const lvl = Math.max(0, Math.min(100, (summary.tank as TankStatus).level_pct as number));
          setTankHistory((h) => {
            const next = [...h, lvl].slice(-20);
            try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next)); } catch { /* ignore quota errors */ }
            return next;
          });
        }
      }
      setRain(rw);
      setRainRecent(rwRecent);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Dashboard refresh failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Load data on mount
  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startQuickIrrigation = useCallback(async (seconds: number) => {
    try {
      const r = await api.irrigationStart("Z1", seconds, false);
      toast({ title: r.ok ? "Irrigation queued" : "Blocked", description: r.status });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
    }
  }, [toast]);

  const stopIrrigation = useCallback(async () => {
    try {
      const r = await api.irrigationStop("Z1");
      toast({ title: r.ok ? "Stop sent" : "Stop queued", description: r.status });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
    }
  }, [toast]);

  

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold" id="dashboard-title">{t("dashboard")}</h2>
        <div className="flex gap-2">
          <Button variant="secondary" aria-label="Refresh dashboard (R)" onClick={refreshAll}>
            {t("refresh")}
          </Button>
          <Button aria-label="Start irrigation (I)" onClick={() => startQuickIrrigation(600)}>{t("start_irrigation_10m")}</Button>
          <Button aria-label="Stop irrigation (X)" variant="destructive" onClick={stopIrrigation}>{t("stop_irrigation")}</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Weather Now */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><CloudSun className="w-5 h-5" /> {t("weather")}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-32" />
              </div>
            ) : latestWeather ? (
              <div className="space-y-1 text-sm">
                <div><span className="text-muted-foreground">ET0:</span> {Number(latestWeather.et0_mm_day).toFixed?.(2) ?? latestWeather.et0_mm_day} mm</div>
                <div><span className="text-muted-foreground">Tmin:</span> {Number(latestWeather.tmin_c).toFixed?.(1) ?? latestWeather.tmin_c} °C</div>
                <div><span className="text-muted-foreground">Tmax:</span> {Number(latestWeather.tmax_c).toFixed?.(1) ?? latestWeather.tmax_c} °C</div>
                <div className="text-xs text-muted-foreground">{latestWeather.date} @ {lat.toFixed(2)},{lon.toFixed(2)}</div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">{t("no_weather")}</div>
            )}
          </CardContent>
        </Card>

        {/* Tank Level */}
        <Card role="region" aria-labelledby="tank-card-title">
          <CardHeader>
            <CardTitle id="tank-card-title" className="flex items-center gap-2"><Droplets className="w-5 h-5" /> {t("tank")}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-4 w-24" />
              </div>
            ) : tank ? (
              <div className="flex items-center gap-4">
                <TankGauge percent={tank.level_pct ?? 0} liters={tank.volume_l ?? undefined} />
                <div className="space-y-1 text-sm">
                  <div><span className="text-muted-foreground">{t("tank_level")}:</span> {tank.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : "—"}</div>
                  <div><span className="text-muted-foreground">{t("tank_volume")}:</span> {tank.volume_l != null ? `${Math.round(tank.volume_l)} L` : "—"}</div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">{t("updated")}:</span>
                    <span ref={lastUpdateRef} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border" title={tank.last_update || ''}>
                      {tank.last_update ? new Date(tank.last_update).toLocaleTimeString() : "—"}
                    </span>
                  </div>
                  {/* Valve status chip based on last event */}
                  <div className="mt-2">
                    {valveEvents[0] ? (
                      <span className={`px-2 py-0.5 text-xs rounded ${valveEvents[0].action === "start" && (valveEvents[0].status === "sent" || valveEvents[0].status === "queued") ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                        {t("status")}: {valveEvents[0].action === "start" ? t("running") : t("idle")} • {new Date(valveEvents[0].ts).toLocaleTimeString()}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-xs rounded bg-slate-100 text-slate-700">{t("status")}: {t("idle")}</span>
                    )}
                  </div>
                  {/* Sparkline */}
                  {tankHistory.length > 1 && (
                    <svg width="120" height="24" viewBox="0 0 120 24" className="mt-2" role="img" aria-label={(() => {
                      const pts = tankHistory;
                      const n = pts.length;
                      const last = pts[n-1]?.toFixed(0);
                      const min = Math.min(...pts).toFixed(0);
                      const max = Math.max(...pts).toFixed(0);
                      const avg = (pts.reduce((a,b)=>a+b,0)/n).toFixed(0);
                      return `Tank level trend: last ${last}%, min ${min}%, max ${max}%, avg ${avg}%`;
                    })()}>
                      <title>{(() => {
                        const pts = tankHistory;
                        const n = pts.length;
                        const last = pts[n-1]?.toFixed(0);
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
                          </>
                        );
                      })()}
                    </svg>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">{t("no_data")}</div>
            )}
          </CardContent>
        </Card>

        {/* Soil Moisture */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Thermometer className="w-5 h-5" /> {t("soil_moisture")}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-6 w-24" />
            ) : soilMoisture != null ? (
              <div className="flex items-center gap-4">
                <div className="text-2xl font-semibold">{soilMoisture.toFixed(0)}%</div>
                <MoistureTrafficLight value={soilMoisture} t={t} />
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">{t("no_data")}</div>
            )}
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card role="region" aria-labelledby="alerts-card-title">
          <CardHeader>
            <CardTitle id="alerts-card-title" className="flex items-center gap-2 justify-between">
              <span className="flex items-center gap-2"><AlertTriangle className="w-5 h-5" /> {t("alerts")}</span>
              <label className="flex items-center gap-2 text-xs text-muted-foreground">
                <input type="checkbox" checked={showAck} onChange={(e) => setShowAck(e.target.checked)} />
                {t("show_acknowledged")}
              </label>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-40" />
              </div>
            ) : alerts.filter(a => showAck || !a.sent).length > 0 ? (
              <ul className="text-sm space-y-2" role="list" aria-label="Alerts">
                {alerts.filter(a => showAck || !a.sent).slice(0, 5).map((a, i) => (
                  <li key={i} role="listitem" className={`flex items-center justify-between gap-2 ${a.sent ? "opacity-60" : ""}`}>
                    <div className="min-w-0">
                      <div className="truncate font-medium">{a.category}{a.sent ? ` • ${t("acknowledged")}` : ""}</div>
                      <div className="truncate text-xs text-muted-foreground">{a.message}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">{a.ts ? new Date(a.ts).toLocaleTimeString() : ""}</span>
                      {!a.sent && (
                        <Button size="sm" aria-label="Acknowledge alert" variant="outline" onClick={async () => { if (a.ts) { await api.alertAck(a.ts); refreshAll(); } }}>
                          <Check className="w-3 h-3 mr-1" /> {t("acknowledge")}
                        </Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-muted-foreground">{t("all_clear")}</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Impact metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("impact_metrics")}</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">{t("saved_water_l")}</div>
              <div className="text-xl font-semibold">{impact ? Math.round(impact.saved_l) : 0}</div>
            </div>
            <div>
              <div className="text-muted-foreground">{t("cost_saving_rs")}</div>
              <div className="text-xl font-semibold">{impact ? Math.round(impact.cost_rs) : 0}</div>
            </div>
            <div>
              <div className="text-muted-foreground">{t("co2e_kg")}</div>
              <div className="text-xl font-semibold">{impact ? (impact.co2e_kg).toFixed(2) : "0.00"}</div>
            </div>
          </CardContent>
        </Card>
        {/* Rainwater summary and quick log */}
    <Card role="region" aria-labelledby="rainwater-card-title">
          <CardHeader>
      <CardTitle id="rainwater-card-title">{t("rainwater")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {rain ? (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-muted-foreground">{t("collected_total")}</div>
                  <div className="text-xl font-semibold">{Math.round(rain.collected_total_l)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">{t("used_total")}</div>
                  <div className="text-xl font-semibold">{Math.round(rain.used_total_l)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">{t("net_balance")}</div>
                  <div className={`text-xl font-semibold ${rain.net_l >= 0 ? "text-emerald-600" : "text-red-600"}`}>{Math.round(rain.net_l)}</div>
                </div>
              </div>
            ) : (
              <div className="text-muted-foreground">{t("no_data")}</div>
            )}
            <div className="flex items-end gap-2">
              <div className="flex flex-col">
                <label className="text-xs text-muted-foreground" htmlFor="rw_col">{t("collected_liters")}</label>
                <input id="rw_col" type="number" className="border rounded px-2 py-1 w-24" placeholder="0" aria-label="Collected liters" min={0} />
              </div>
              <div className="flex flex-col">
                <label className="text-xs text-muted-foreground" htmlFor="rw_used">{t("used_liters")}</label>
                <input id="rw_used" type="number" className="border rounded px-2 py-1 w-24" placeholder="0" aria-label="Used liters" min={0} />
              </div>
              <Button size="sm" aria-label="Add rainwater entry" onClick={async () => {
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
              }}>{t("add")}</Button>
            </div>
            {rainRecent.length > 0 && (
              <div className="pt-2 border-t">
                <div className="text-xs text-muted-foreground mb-1">{t("recent_entries") ?? "Recent entries"}</div>
                <ul className="space-y-1 text-xs">
                  {rainRecent.map((e, i) => (
                    <li key={i} className="flex items-center justify-between">
                      <span className="text-muted-foreground">{new Date(e.ts).toLocaleTimeString()}</span>
                      <span className="text-foreground">+{Math.round(e.collected_liters)} / -{Math.round(e.used_liters)} L</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
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
