import { useEffect, useMemo, useState } from "react";
import { api, type TankStatus, type AlertItem, type WeatherCacheRow } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Droplets, Thermometer, AlertTriangle, CloudSun } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Dashboard() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [latestWeather, setLatestWeather] = useState<WeatherCacheRow | null>(null);
  const [soilMoisture, setSoilMoisture] = useState<number | null>(null);

  const lat = useMemo(() => Number(localStorage.getItem("lat") || "27.3"), []);
  const lon = useMemo(() => Number(localStorage.getItem("lon") || "88.6"), []);

  const refreshAll = async () => {
    setLoading(true);
    try {
      const [t, a, r, w] = await Promise.all([
        api.tankStatus("T1").catch(() => null),
        api.alerts(undefined, 5).then((x) => x.items).catch(() => []),
        api.recent("Z1", 1).catch(() => ({ items: [] })),
        api.adminWeatherRefresh(lat, lon, 1).catch(() => ({ latest: null })) as Promise<{ latest?: WeatherCacheRow | null }>,
      ]);
      setTank(t);
      setAlerts(a);
      const last = r.items?.[0]?.moisture_pct as number | undefined;
      setSoilMoisture(last ?? null);
      setLatestWeather(w.latest ?? null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Dashboard refresh failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startQuickIrrigation = async (seconds: number) => {
    try {
      const r = await api.irrigationStart("Z1", seconds, false);
      toast({ title: r.ok ? "Irrigation queued" : "Blocked", description: r.status });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={refreshAll}>
            Refresh
          </Button>
          <Button onClick={() => startQuickIrrigation(600)}>Start irrigation 10 min</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Weather Now */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><CloudSun className="w-5 h-5" /> Weather</CardTitle>
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
              <div className="text-sm text-muted-foreground">No weather yet</div>
            )}
          </CardContent>
        </Card>

        {/* Tank Level */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Droplets className="w-5 h-5" /> Tank</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-20" />
                <Skeleton className="h-4 w-24" />
              </div>
            ) : tank ? (
              <div className="space-y-1 text-sm">
                <div><span className="text-muted-foreground">Level:</span> {tank.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : "—"}</div>
                <div><span className="text-muted-foreground">Volume:</span> {tank.volume_l != null ? `${Math.round(tank.volume_l)} L` : "—"}</div>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No tank data</div>
            )}
          </CardContent>
        </Card>

        {/* Soil Moisture */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Thermometer className="w-5 h-5" /> Soil Moisture</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-6 w-24" />
            ) : soilMoisture != null ? (
              <div className="text-2xl font-semibold">{soilMoisture.toFixed(0)}%</div>
            ) : (
              <div className="text-sm text-muted-foreground">No data</div>
            )}
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><AlertTriangle className="w-5 h-5" /> Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-40" />
              </div>
            ) : alerts.length > 0 ? (
              <ul className="text-sm space-y-1">
                {alerts.slice(0, 3).map((a, i) => (
                  <li key={i} className="flex justify-between gap-2">
                    <span className="truncate">{a.category}: {a.message}</span>
                    <span className="text-xs text-muted-foreground">{a.ts ? new Date(a.ts).toLocaleTimeString() : ""}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-muted-foreground">All clear</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
