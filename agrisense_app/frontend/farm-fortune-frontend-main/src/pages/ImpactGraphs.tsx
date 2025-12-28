import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTranslation } from "react-i18next";

function Sparkline({ points, color = "#16a34a" }: { points: number[]; color?: string }) {
  if (!points.length) return <div className="h-12" />;
  const w = 320, h = 60, pad = 6;
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

type RecoItem = {
  ts: string;
  zone_id: string;
  plant: string;
  water_liters?: number;
  expected_savings_liters?: number;
  fert_n_g?: number;
  fert_p_g?: number;
  fert_k_g?: number;
  yield_potential?: number | null;
};

export default function ImpactGraphs() {
  const { t } = useTranslation();
  const [zone, setZone] = useState("Z1");
  const [rows, setRows] = useState<RecoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchOnce = async () => {
      try {
        const data = await api.recoRecent(zone, 200);
        if (!mounted) return;
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
    const id = setInterval(fetchOnce, 7000);
    return () => {
      mounted = false;
      clearInterval(id);
    };
  }, [zone]);

  const series = useMemo(() => {
    const ts = rows.map((r) => r.ts);
    const water = rows.map((r) => Number(r.water_liters ?? 0));
    const savings = rows.map((r) => Number(r.expected_savings_liters ?? 0));
    const fertTotal = rows.map((r) => Number((r.fert_n_g ?? 0) + (r.fert_p_g ?? 0) + (r.fert_k_g ?? 0)));
    const yieldPotential = rows.map((r) => Number(r.yield_potential ?? 0));
    return { ts, water, savings, fertTotal, yieldPotential };
  }, [rows]);

  return (
    <div className="container mx-auto p-4 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">{t("impact_over_time")}</h1>
        <Select value={zone} onValueChange={setZone}>
          <SelectTrigger className="w-32"><SelectValue placeholder={t("zone_label")} /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Z1">Z1</SelectItem>
            <SelectItem value="Z2">Z2</SelectItem>
            <SelectItem value="Z3">Z3</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && <div className="text-sm text-red-600">{error}</div>}

      {!rows.length && !loading && (
        <Card className="p-4 text-sm text-muted-foreground">
          {t("no_reco_snapshots")}
        </Card>
      )}

      <Tabs defaultValue="savings" className="w-full">
        <TabsList>
          <TabsTrigger value="savings">{t("water_savings_l")}</TabsTrigger>
          <TabsTrigger value="water">{t("water_applied_l")}</TabsTrigger>
          <TabsTrigger value="fert">{t("fertilizer_total_g")}</TabsTrigger>
          <TabsTrigger value="yield">{t("yield_potential")}</TabsTrigger>
        </TabsList>
        <TabsContent value="savings">
          <Card className="p-4">
            <Sparkline points={series.savings} color="#0ea5e9" />
          </Card>
        </TabsContent>
        <TabsContent value="water">
          <Card className="p-4">
            <Sparkline points={series.water} color="#22c55e" />
          </Card>
        </TabsContent>
        <TabsContent value="fert">
          <Card className="p-4">
            <Sparkline points={series.fertTotal} color="#f59e0b" />
          </Card>
        </TabsContent>
        <TabsContent value="yield">
          <Card className="p-4">
            <Sparkline points={series.yieldPotential} color="#a855f7" />
          </Card>
        </TabsContent>
      </Tabs>

      <Card className="p-4">
        <div className="text-sm text-muted-foreground">
          These graphs show your reduced water and fertilizer usage and any increase in predicted yield over time.
        </div>
      </Card>
    </div>
  );
}
