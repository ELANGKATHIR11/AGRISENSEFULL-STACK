import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Simple mini chart using inline SVG to avoid extra deps.
function Sparkline({ points, color = "#16a34a" }: { points: number[]; color?: string }) {
  if (!points.length) return <div className="h-12" />;
  const w = 240, h = 48, pad = 4;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = (w - pad * 2) / Math.max(1, points.length - 1);
  const d = points
    .map((v, i) => {
      const x = pad + i * step;
      const y = h - pad - ((v - min) / range) * (h - pad * 2);
      return `${i === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="overflow-visible">
      <path d={d} fill="none" stroke={color} strokeWidth={2} />
    </svg>
  );
}

type RecentItem = {
  ts: string;
  zone_id: string;
  plant: string;
  soil_type: string;
  area_m2: number;
  ph: number;
  moisture_pct: number;
  temperature_c: number;
  ec_dS_m: number;
  n_ppm: number | null;
  p_ppm: number | null;
  k_ppm: number | null;
};

export default function LiveStats() {
  const [zone, setZone] = useState("Z1");
  const [rows, setRows] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // poll recent readings every 5s
  useEffect(() => {
    let mounted = true;
    const fetchOnce = async () => {
      try {
        const data = await api.recent(zone, 200);
        if (!mounted) return;
        // backend returns newest first; reverse to chronological
        setRows((data.items || []).slice().reverse());
        setError(null);
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchOnce();
    const id = setInterval(fetchOnce, 5000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [zone]);

  const series = useMemo(() => {
    const ts = rows.map((r) => r.ts);
    const moisture = rows.map((r) => Number(r.moisture_pct ?? 0));
    const ph = rows.map((r) => Number(r.ph ?? 0));
    const temp = rows.map((r) => Number(r.temperature_c ?? 0));
    const ec = rows.map((r) => Number(r.ec_dS_m ?? 0));
    return { ts, moisture, ph, temp, ec };
  }, [rows]);

  return (
    <div className="container mx-auto p-4 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Live Farm Stats</h1>
        <Select value={zone} onValueChange={setZone}>
          <SelectTrigger className="w-32"><SelectValue placeholder="Zone" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Z1">Z1</SelectItem>
            <SelectItem value="Z2">Z2</SelectItem>
            <SelectItem value="Z3">Z3</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <Tabs defaultValue="moisture" className="w-full">
        <TabsList>
          <TabsTrigger value="moisture">Moisture %</TabsTrigger>
          <TabsTrigger value="ph">Soil pH</TabsTrigger>
          <TabsTrigger value="temp">Temperature °C</TabsTrigger>
          <TabsTrigger value="ec">EC dS/m</TabsTrigger>
        </TabsList>
        <TabsContent value="moisture">
          <Card className="p-4">
            <Sparkline points={series.moisture} color="#0ea5e9" />
          </Card>
        </TabsContent>
        <TabsContent value="ph">
          <Card className="p-4">
            <Sparkline points={series.ph} color="#a855f7" />
          </Card>
        </TabsContent>
        <TabsContent value="temp">
          <Card className="p-4">
            <Sparkline points={series.temp} color="#ef4444" />
          </Card>
        </TabsContent>
        <TabsContent value="ec">
          <Card className="p-4">
            <Sparkline points={series.ec} color="#16a34a" />
          </Card>
        </TabsContent>
      </Tabs>

      <Card className="p-4">
        <div className="text-sm text-muted-foreground">
          These live graphs help showcase reduced water usage and fertilizer needs over time as soil moisture stabilizes and pH stays in the optimal band. Add more metrics from recommendations if you persist them.
        </div>
      </Card>
    </div>
  );
}
