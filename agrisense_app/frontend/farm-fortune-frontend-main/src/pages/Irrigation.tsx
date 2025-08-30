import { useCallback, useEffect, useState } from "react";
import { api, TankStatus, IrrigationAck, AlertItem, ValveEvent } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";

export default function Irrigation() {
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [zone, setZone] = useState("Z1");
  const [duration, setDuration] = useState<number | undefined>(undefined);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [events, setEvents] = useState<ValveEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const { toast } = useToast();

  const refresh = useCallback(async () => {
    try {
  const [t, a, ev] = await Promise.all([api.tankStatus("T1"), api.alerts(zone, 10), api.valveEvents(zone, 10)]);
      setTank(t);
      setAlerts(a.items);
  setEvents(ev.items);
  const running = ev.items.find((e) => e.action === "start" && (e.status === "sent" || e.status === "queued"));
  const stopped = ev.items.find((e) => e.action === "stop" && (e.status === "sent" || e.status === "queued"));
  setIsRunning(!!running && (!stopped || new Date(stopped.ts) < new Date(running.ts)));
    } catch (e) {
      console.error(e);
    }
  }, [zone]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);

  const start = async (force = false) => {
    setLoading(true);
    try {
      const r: IrrigationAck = await api.irrigationStart(zone, duration, force);
      toast({ title: r.ok ? "Irrigation queued" : "Blocked", description: r.note || r.status });
      refresh();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    setLoading(true);
    try {
      const r = await api.irrigationStop(zone);
      toast({ title: r.ok ? "Stop sent" : "Stop queued", description: r.status });
      refresh();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Tank status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-muted-foreground">Tank</div>
              <div className="text-xl font-semibold">{tank?.tank_id ?? "T1"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Level</div>
              <div className="text-xl font-semibold">{tank?.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : "—"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Volume</div>
              <div className="text-xl font-semibold">{tank?.volume_l != null ? `${Math.round(tank.volume_l)} L` : "—"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Updated</div>
              <div className="text-xl font-semibold">{tank?.last_update ? new Date(tank.last_update).toLocaleString() : "—"}</div>
            </div>
            <Button variant="secondary" onClick={refresh}>Refresh</Button>
          </div>

          <div>
            <Progress
              value={tank?.level_pct ?? 0}
              className={`${(tank?.level_pct ?? 0) < 20 ? "bg-red-100" : (tank?.level_pct ?? 0) < 50 ? "bg-yellow-100" : "bg-green-100"}`}
            />
            <div className="text-xs mt-1 text-muted-foreground">
              {(tank?.level_pct ?? 0) < 20 ? "Low level" : (tank?.level_pct ?? 0) < 50 ? "Moderate" : "Healthy"}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Irrigation control</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <label className="text-sm">Zone</label>
            <input className="border px-3 py-2 rounded-md" value={zone} onChange={(e) => setZone(e.target.value)} />
            <label className="text-sm">Duration (s)</label>
            <input type="number" className="border px-3 py-2 rounded-md w-28" value={duration ?? ""} onChange={(e) => setDuration(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            Quick: {([60, 120, 300, 600] as const).map((d) => (
              <Button key={d} size="sm" variant="outline" onClick={() => setDuration(d)}>{d}s</Button>
            ))}
          </div>
          <div className="flex items-center space-x-3">
            <Button onClick={() => start(false)} disabled={loading}>Start</Button>
            <Button variant="destructive" onClick={stop} disabled={loading}>Stop</Button>
            <Button variant="outline" onClick={() => start(true)} disabled={loading}>Force Start</Button>
            <span className={`text-sm ${isRunning ? "text-green-600" : "text-muted-foreground"}`}>
              Status: {isRunning ? "Running" : "Idle"}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent valve events</CardTitle>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="text-sm text-muted-foreground">No events</div>
          ) : (
            <ul className="space-y-2">
              {events.map((ev, i) => (
                <li key={i} className="flex items-center justify-between border rounded-md px-3 py-2">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${ev.action === "start" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>{ev.action}</span>
                    <span className="text-xs text-muted-foreground">{ev.duration_s ? `${Math.round(ev.duration_s)}s` : "—"}</span>
                    <span className="text-xs text-muted-foreground">{ev.status}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">{new Date(ev.ts).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-sm text-muted-foreground">No alerts</div>
          ) : (
            <ul className="space-y-2">
              {alerts.map((a, i) => (
                <li key={i} className="flex items-center justify-between border rounded-md px-3 py-2">
                  <div>
                    <div className="text-sm font-medium">{a.category}</div>
                    <div className="text-xs text-muted-foreground">{a.message}</div>
                  </div>
                  <div className="text-xs text-muted-foreground">{a.ts ? new Date(a.ts).toLocaleString() : ""}</div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
