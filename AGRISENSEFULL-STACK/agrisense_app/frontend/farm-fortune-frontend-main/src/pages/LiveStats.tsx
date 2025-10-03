import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
  const [zone, setZone] = useState("Z1");
  const [rows, setRows] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [edgeOk, setEdgeOk] = useState<boolean | null>(null);
  const [capturing, setCapturing] = useState(false);
  const { toast } = useToast();

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

  // poll edge health every 15s
  useEffect(() => {
    let mounted = true;
    const ping = async () => {
      try {
        const h = await api.edgeHealth();
        if (!mounted) return;
        setEdgeOk(h.status === "ok");
      } catch {
        if (!mounted) return;
        setEdgeOk(false);
      }
    };
    ping();
    const id = setInterval(ping, 15000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, []);

  // toast when edge connectivity changes
  const prevEdgeOk = useRef<boolean | null>(null);
  useEffect(() => {
    if (edgeOk === prevEdgeOk.current) return;
    if (prevEdgeOk.current !== null) {
      if (edgeOk) {
        toast({ title: t("edge_label") + " " + t("connected"), description: t("edge_label") + " " + t("available") });
      } else if (edgeOk === false) {
        toast({ title: t("edge_label") + " " + t("unavailable"), description: t("edge_label") + " " + t("not_detected") });
      }
    }
    prevEdgeOk.current = edgeOk;
  }, [edgeOk, toast, t]);

  const doCapture = async () => {
    setCapturing(true);
    try {
      const res = await api.edgeCapture(zone);
      toast({ title: "Capture complete", description: `Water: ${res.recommendation.water_liters.toFixed?.(1) ?? res.recommendation.water_liters} L` });
      // refresh recent now
      const data = await api.recent(zone, 200);
      setRows((data.items || []).slice().reverse());
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Capture failed", description: msg });
    } finally {
      setCapturing(false);
    }
  };

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
        <h1 className="text-2xl font-semibold">{t("live_farm_stats")}</h1>
        <div className="flex items-center gap-2">
          <div className={`text-sm ${edgeOk === false ? "text-red-600" : edgeOk === true ? "text-green-600" : "text-muted-foreground"}`}>
            {t("edge_label")}: {edgeOk === null ? "…" : edgeOk ? t("connected") : t("unavailable")}
          </div>
          <Select value={zone} onValueChange={setZone}>
            <SelectTrigger className="w-32"><SelectValue placeholder={t("zone_label")} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Z1">Z1</SelectItem>
              <SelectItem value="Z2">Z2</SelectItem>
              <SelectItem value="Z3">Z3</SelectItem>
            </SelectContent>
          </Select>
          <Button disabled={capturing || edgeOk === false} onClick={doCapture}>
            {capturing ? t("capturing") : t("capture_now")}
          </Button>
        </div>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      <Tabs defaultValue="moisture" className="w-full">
        <TabsList>
          <TabsTrigger value="moisture">{t("moisture_pct")}</TabsTrigger>
          <TabsTrigger value="ph">{t("soil_ph")}</TabsTrigger>
          <TabsTrigger value="temp">{t("temperature_c")}</TabsTrigger>
          <TabsTrigger value="ec">{t("ec_ds_m")}</TabsTrigger>
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
          {/* Translators: helper text for live stats page */}
          These live graphs help showcase reduced water usage and fertilizer needs over time as soil moisture stabilizes and pH stays in the optimal band.
        </div>
      </Card>
    </div>
  );
}
