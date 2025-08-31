import { useCallback, useEffect, useState } from "react";
import { api, TankStatus, IrrigationAck, AlertItem, ValveEvent } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { useI18n } from "@/i18n";

export default function Irrigation() {
  const { t } = useI18n();
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [zone, setZone] = useState("Z1");
  const [duration, setDuration] = useState<number | undefined>(undefined);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [showAck, setShowAck] = useState(false);
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
    if (!zone.trim()) {
      toast({ title: "Zone required", description: "Please enter a zone id (e.g., Z1)", variant: "destructive" });
      return;
    }
    if (duration == null || duration <= 0) {
      toast({ title: "Duration required", description: "Please set a positive duration in seconds", variant: "destructive" });
      return;
    }
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
          <CardTitle>{t("tank")} {t("status")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-muted-foreground">{t("tank")}</div>
              <div className="text-xl font-semibold">{tank?.tank_id ?? "T1"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">{t("tank_level")}</div>
              <div className="text-xl font-semibold">{tank?.level_pct != null ? `${tank.level_pct.toFixed(0)}%` : "—"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">{t("tank_volume")}</div>
              <div className="text-xl font-semibold">{tank?.volume_l != null ? `${Math.round(tank.volume_l)} L` : "—"}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">{t("updated")}</div>
              <div className="text-xl font-semibold">{tank?.last_update ? new Date(tank.last_update).toLocaleString() : "—"}</div>
            </div>
            <Button variant="secondary" onClick={refresh}>{t("refresh")}</Button>
          </div>

          <div>
            <Progress
              value={tank?.level_pct ?? 0}
              className={`${(tank?.level_pct ?? 0) < 20 ? "bg-red-100" : (tank?.level_pct ?? 0) < 50 ? "bg-yellow-100" : "bg-green-100"}`}
            />
            <div className="text-xs mt-1 text-muted-foreground">
              {(tank?.level_pct ?? 0) < 20 ? t("low_level") : (tank?.level_pct ?? 0) < 50 ? t("moderate") : t("healthy")}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("nav_irrigation")} {t("status")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-4">
            <label htmlFor="zone" className="text-sm">{t("zone")}</label>
            <input
              id="zone"
              name="zone"
              className="border px-3 py-2 rounded-md"
              placeholder="e.g., Z1"
              title="Irrigation zone id"
              value={zone}
              onChange={(e) => setZone(e.target.value)}
            />
            <label htmlFor="duration" className="text-sm">{t("duration_seconds")}</label>
            <div className="relative">
              <input
                id="duration"
                name="duration"
                type="number"
                className="border px-3 py-2 rounded-md w-32 pr-10"
                placeholder="seconds"
                title="Irrigation duration in seconds"
                value={duration ?? ""}
                onChange={(e) => setDuration(e.target.value ? Math.max(0, Number(e.target.value)) : undefined)}
                min={0}
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">s</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {t("quick")}: {([60, 120, 300, 600] as const).map((d) => (
              <Button key={d} size="sm" variant="outline" onClick={() => setDuration(d)}>{d}s</Button>
            ))}
          </div>
          <div className="text-xs text-muted-foreground">
            {duration == null || duration <= 0 ? t("duration_seconds") : ""}
          </div>
          <div className="flex items-center space-x-3">
            <Button onClick={() => start(false)} disabled={loading || duration == null || duration <= 0}>{t("start")}</Button>
            <Button variant="destructive" onClick={stop} disabled={loading}>{t("stop")}</Button>
            <Button variant="outline" onClick={() => start(true)} disabled={loading || duration == null || duration <= 0}>{t("force_start")}</Button>
            <span className={`text-sm ${isRunning ? "text-green-600" : "text-muted-foreground"}`}>
              {t("status")}: {isRunning ? t("running") : t("idle")}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("recent_valve_events")}</CardTitle>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <div className="text-sm text-muted-foreground">{t("no_events")}</div>
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
          <CardTitle className="flex items-center justify-between">
            <span>{t("alerts")}</span>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={showAck} onChange={(e) => setShowAck(e.target.checked)} />
              {t("show_acknowledged")}
            </label>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.filter(a => showAck || !a.sent).length === 0 ? (
            <div className="text-sm text-muted-foreground">{t("all_clear")}</div>
          ) : (
            <ul className="space-y-2">
              {alerts.filter(a => showAck || !a.sent).map((a, i) => (
                <li key={i} className={`flex items-center justify-between border rounded-md px-3 py-2 ${a.sent ? "opacity-60" : ""}`}>
                  <div>
                    <div className="text-sm font-medium">{a.category}{a.sent ? ` • ${t("acknowledged")}` : ""}</div>
                    <div className="text-xs text-muted-foreground">{a.message}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{a.ts ? new Date(a.ts).toLocaleString() : ""}</span>
                    {!a.sent && (
                      <Button size="sm" variant="outline" onClick={async () => { if (a.ts) { await api.alertAck(a.ts); refresh(); } }}>{t("acknowledge")}</Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
