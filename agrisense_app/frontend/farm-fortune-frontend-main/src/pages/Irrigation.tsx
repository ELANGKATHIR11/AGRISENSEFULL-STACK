import { useCallback, useEffect, useState } from "react";
import { api, TankStatus, IrrigationAck, AlertItem, ValveEvent } from "../lib/api";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
import { ToastAction } from "../components/ui/toast";
import { useToast } from "../hooks/use-toast";
import { useTranslation } from "react-i18next";

export default function Irrigation() {
  const { t } = useTranslation();
  const [tank, setTank] = useState<TankStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [zone, setZone] = useState("Z1");
  const [duration, setDuration] = useState<number | undefined>(undefined);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [showAck, setShowAck] = useState(false);
  const [events, setEvents] = useState<ValveEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [initial, setInitial] = useState(true);
  const { toast } = useToast();
  const zoneValid = zone.trim().length > 0;
  const durationValid = duration != null && duration > 0;

  const refresh = useCallback(async () => {
    try {
  const [t, a, ev] = await Promise.all([api.tankStatus("T1"), api.alerts(zone, 10), api.valveEvents(zone, 10)]);
      setTank(t);
      setAlerts(a.items);
  setEvents(ev.items);
  const running = ev.items.find((e) => e.action === "start" && (e.status === "sent" || e.status === "queued"));
  const stopped = ev.items.find((e) => e.action === "stop" && (e.status === "sent" || e.status === "queued"));
  setIsRunning(!!running && (!stopped || new Date(stopped.ts) < new Date(running.ts)));
      setInitial(false);
    } catch (e) {
      console.error(e);
      setInitial(false);
    }
  }, [zone]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, [refresh]);


  const start = useCallback(async (force = false) => {
    if (!zoneValid) {
      toast({ title: "Zone required", description: "Please enter a zone id (e.g., Z1)", variant: "destructive" });
      document.getElementById('zone')?.focus();
      return;
    }
    if (!durationValid) {
      toast({ title: "Duration required", description: "Please set a positive duration in seconds", variant: "destructive" });
      document.getElementById('duration')?.focus();
      return;
    }
    // Optimistic update
    setLoading(true);
    const prevEvents = events;
    const prevIsRunning = isRunning;
    const optimistic: ValveEvent = {
      ts: new Date().toISOString(),
      zone_id: zone,
      action: "start",
      duration_s: duration ?? 0,
      status: "queued",
    };
    setEvents([optimistic, ...events]);
    setIsRunning(true);
    try {
      const r: IrrigationAck = await api.irrigationStart(zone, duration, force);
      // Mark optimistic as sent
      setEvents((evs) => evs.map((e) => (e === optimistic ? { ...e, status: r.ok ? "sent" : "queued" } : e)));
      const undo = toast({
        title: r.ok ? "Irrigation queued" : "Blocked",
        description: r.note || r.status,
        action: (
          <ToastAction
            altText="Undo"
            onClick={async () => {
              try {
                await api.irrigationStop(zone);
                setIsRunning(false);
                // Remove the optimistic start and add an optimistic stop
                setEvents((evs) => [
                  { ts: new Date().toISOString(), zone_id: zone, action: "stop", duration_s: 0, status: "queued" },
                  ...evs.filter((e) => e !== optimistic),
                ]);
              } catch (err) {
                console.error(err);
              } finally {
                void refresh();
              }
            }}
          >
            Undo
          </ToastAction>
        ),
      });
      // Auto refresh to reconcile
      void refresh();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
      // Revert optimistic state
      setEvents(prevEvents);
      setIsRunning(prevIsRunning);
    } finally {
      setLoading(false);
    }
  }, [zoneValid, durationValid, events, isRunning, zone, duration, toast, refresh]);

  const stop = useCallback(async () => {
    // Optimistic update
    setLoading(true);
    const prevEvents = events;
    const prevIsRunning = isRunning;
    const optimistic: ValveEvent = { ts: new Date().toISOString(), zone_id: zone, action: "stop", duration_s: 0, status: "queued" };
    setEvents([optimistic, ...events]);
    setIsRunning(false);
    try {
      const r = await api.irrigationStop(zone);
      // Mark optimistic as sent
      setEvents((evs) => evs.map((e) => (e === optimistic ? { ...e, status: r.ok ? "sent" : "queued" } : e)));
      toast({ title: r.ok ? "Stop sent" : "Stop queued", description: r.status });
      void refresh();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: "Failed", description: msg, variant: "destructive" });
      // Revert optimistic state
      setEvents(prevEvents);
      setIsRunning(prevIsRunning);
    } finally {
      setLoading(false);
    }
  }, [events, isRunning, zone, toast, refresh]);

  // Accessibility: keyboard shortcuts (r=refresh, s=start, x=stop)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (document.activeElement?.tagName || '').toLowerCase();
      const isTyping = tag === 'input' || tag === 'textarea' || (document.activeElement as HTMLElement | null)?.isContentEditable;
      if (isTyping) return;
      if (e.key === 'r') {
        e.preventDefault();
        void refresh();
      } else if (e.key === 's') {
        e.preventDefault();
        if (zoneValid && durationValid) void start(false);
        else {
          toast({ title: 'Fix inputs', description: 'Provide a zone and positive duration', variant: 'destructive' });
          const el = !zoneValid ? document.getElementById('zone') : document.getElementById('duration');
          el?.focus();
        }
      } else if (e.key === 'x') {
        e.preventDefault();
        void stop();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [zoneValid, durationValid, refresh, start, stop, toast]);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
    <Card role="region" aria-labelledby="tank-card-title">
        <CardHeader>
      <CardTitle id="tank-card-title">{t("tank")} {t("status")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {initial ? (
            <div className="space-y-2">
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-32" />
            </div>
          ) : (
            <>
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
                <Button variant="secondary" aria-label="Refresh tank status (R)" onClick={refresh}>{t("refresh")}</Button>
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
            </>
          )}
        </CardContent>
      </Card>

      <Card role="region" aria-labelledby="irrigation-card-title">
        <CardHeader>
          <CardTitle id="irrigation-card-title">{t("nav_irrigation")} {t("status")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-4">
            <label htmlFor="zone" className="text-sm">{t("zone")}</label>
            {zoneValid ? (
              <input
                id="zone"
                name="zone"
                className="border px-3 py-2 rounded-md"
                placeholder="e.g., Z1"
                title="Irrigation zone id"
                value={zone}
                onChange={(e) => setZone(e.target.value)}
              />
            ) : (
              <input
                id="zone"
                name="zone"
                className="border px-3 py-2 rounded-md border-red-600 focus:outline-red-600"
                placeholder="e.g., Z1"
                title="Irrigation zone id"
                value={zone}
                onChange={(e) => setZone(e.target.value)}
                aria-invalid="true"
                aria-describedby="zone-help"
              />
            )}
            {!zoneValid && (
              <span id="zone-help" className="text-xs text-red-600">Zone is required</span>
            )}
            <label htmlFor="duration" className="text-sm">{t("duration_seconds")}</label>
            <div className="relative">
              {durationValid ? (
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
              ) : (
                <input
                  id="duration"
                  name="duration"
                  type="number"
                  className="border px-3 py-2 rounded-md w-32 pr-10 border-red-600 focus:outline-red-600"
                  placeholder="seconds"
                  title="Irrigation duration in seconds"
                  value={duration ?? ""}
                  onChange={(e) => setDuration(e.target.value ? Math.max(0, Number(e.target.value)) : undefined)}
                  min={0}
                  aria-invalid="true"
                  aria-describedby="duration-help"
                />
              )}
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">s</span>
            </div>
            {!durationValid && (
              <span id="duration-help" className="text-xs text-red-600">Enter a positive number of seconds</span>
            )}
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
            <Button aria-label="Start irrigation (S)" onClick={() => start(false)} disabled={loading || !durationValid || !zoneValid}>{t("start")}</Button>
            <Button aria-label="Stop irrigation (X)" variant="destructive" onClick={stop} disabled={loading}>{t("stop")}</Button>
            <Button aria-label="Force start irrigation" variant="outline" onClick={() => start(true)} disabled={loading || !durationValid || !zoneValid}>{t("force_start")}</Button>
            <span role="status" aria-live="polite" className={`text-sm ${isRunning ? "text-green-600" : "text-muted-foreground"}`}>
              {t("status")}: {isRunning ? t("running") : t("idle")}
            </span>
          </div>
        </CardContent>
      </Card>

    <Card role="region" aria-labelledby="events-card-title">
        <CardHeader>
      <CardTitle id="events-card-title">{t("recent_valve_events")}</CardTitle>
        </CardHeader>
        <CardContent>
          {initial ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-4 w-56" />
              <Skeleton className="h-4 w-48" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-sm text-muted-foreground">{t("no_events")}</div>
          ) : (
            <ul className="space-y-2" role="list" aria-label="Recent valve events">
              {events.map((ev, i) => (
                <li key={i} role="listitem" className="flex items-center justify-between border rounded-md px-3 py-2">
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

      <Card role="region" aria-labelledby="alerts-card-title">
        <CardHeader>
          <CardTitle id="alerts-card-title" className="flex items-center justify-between">
            <span>{t("alerts")}</span>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input type="checkbox" checked={showAck} onChange={(e) => setShowAck(e.target.checked)} />
              {t("show_acknowledged")}
            </label>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {initial ? (
            <div className="space-y-2">
              <Skeleton className="h-4 w-64" />
              <Skeleton className="h-4 w-56" />
            </div>
          ) : alerts.filter(a => showAck || !a.sent).length === 0 ? (
            <div className="text-sm text-muted-foreground">{t("all_clear")}</div>
          ) : (
            <ul className="space-y-2" role="list" aria-label="Alerts list">
              {alerts.filter(a => showAck || !a.sent).map((a, i) => (
                <li key={i} role="listitem" className={`flex items-center justify-between border rounded-md px-3 py-2 ${a.sent ? "opacity-60" : ""}`}>
                  <div>
                    <div className="text-sm font-medium">{a.category}{a.sent ? ` • ${t("acknowledged")}` : ""}</div>
                    <div className="text-xs text-muted-foreground">{a.message}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{a.ts ? new Date(a.ts).toLocaleString() : ""}</span>
                    {!a.sent && (
                      <Button size="sm" aria-label="Acknowledge alert" variant="outline" onClick={async () => { if (a.ts) { await api.alertAck(a.ts); refresh(); } }}>{t("acknowledge")}</Button>
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
