import { useEffect, useState } from "react";
import { api, TankStatus as TankStatusType } from "../lib/api";
import TankGauge from "../components/TankGauge";
import { useToast } from "../hooks/use-toast";

const Tank = () => {
  const { toast } = useToast();
  const [tankId, setTankId] = useState("T1");
  const [status, setStatus] = useState<TankStatusType | null>(null);
  const [levelPct, setLevelPct] = useState<string>("");
  const [volumeL, setVolumeL] = useState<string>("");
  const [rainfall, setRainfall] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const load = async () => {
    try {
      const s = await api.tankStatus(tankId);
      setStatus(s);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed to load tank status", description: msg, variant: "destructive" });
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tankId]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.tankLevel(tankId, Number(levelPct), Number(volumeL), rainfall ? Number(rainfall) : undefined);
      toast({ title: "Tank updated" });
      setLevelPct("");
      setVolumeL("");
      setRainfall("");
      await load();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed to update tank", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const percent = status?.level_pct ?? null;
  const liters = status?.volume_l ?? null;

  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="bg-white dark:bg-card shadow-md rounded-lg p-4 mb-4">
        <h2 className="text-2xl font-bold text-green-700 dark:text-green-400 mb-1">🌱 Tank & Irrigation Status</h2>
        <p className="text-sm text-muted-foreground">Monitor tank level and update readings</p>
      </div>
      <div className="flex items-center gap-6 mb-6 bg-white dark:bg-card shadow-md rounded-lg p-4">
        <TankGauge percent={percent} liters={liters ?? undefined} />
        <div>
          <label className="form-control w-36">
            <span className="label-text text-sm text-muted-foreground">Tank ID</span>
            <input
              id="tank-id"
              type="text"
              className="input input-bordered"
              value={tankId}
              onChange={(e) => setTankId(e.target.value)}
              placeholder="e.g., T1"
              title="Tank ID"
              autoComplete="off"
            />
          </label>
          <div className="mt-2 text-sm">Capacity: {status?.capacity_liters ?? 0} L</div>
          <div className="text-xs text-muted-foreground">Last update: {status?.last_update ?? "-"}</div>
        </div>
      </div>

      <form onSubmit={submit} className="space-y-3 bg-white dark:bg-card shadow-md rounded-lg p-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label className="form-control">
            <span className="label-text">Level %</span>
            <input type="number" step="0.1" className="input input-bordered" value={levelPct} onChange={(e) => setLevelPct(e.target.value)} placeholder="e.g., 42" />
          </label>
          <label className="form-control">
            <span className="label-text">Volume (L)</span>
            <input type="number" step="1" className="input input-bordered" value={volumeL} onChange={(e) => setVolumeL(e.target.value)} placeholder="e.g., 500" />
          </label>
          <label className="form-control">
            <span className="label-text">Rainfall (mm)</span>
            <input type="number" step="0.1" className="input input-bordered" value={rainfall} onChange={(e) => setRainfall(e.target.value)} placeholder="optional" />
          </label>
        </div>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Saving..." : "Update Tank"}
        </button>
      </form>
    </div>
  );
};

export default Tank;
