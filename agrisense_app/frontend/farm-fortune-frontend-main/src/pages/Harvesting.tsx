import { useEffect, useRef, useState } from "react";
import { api, type WeatherCacheRow } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

export default function Harvesting() {
    const { toast } = useToast();
    const [lat, setLat] = useState<string>(() => localStorage.getItem("lat") || "27.3");
    const [lon, setLon] = useState<string>(() => localStorage.getItem("lon") || "88.6");
    const [latest, setLatest] = useState<WeatherCacheRow | null>(null);
    const [busy, setBusy] = useState(false);
    const [geoBusy, setGeoBusy] = useState(false);
    const [geoMsg, setGeoMsg] = useState<string | null>(null);
    const [live, setLive] = useState<boolean>(() => localStorage.getItem("geo_live") === "1");
    const [highAcc, setHighAcc] = useState<boolean>(() => localStorage.getItem("geo_highacc") === "1");
    const watchIdRef = useRef<number | null>(null);
    const lastRefreshAtRef = useRef<number>(0);
    const lastCoordsRef = useRef<{ lat: number; lon: number } | null>(null);

    useEffect(() => {
        localStorage.setItem("lat", lat);
        localStorage.setItem("lon", lon);
    }, [lat, lon]);

    useEffect(() => {
        localStorage.setItem("geo_live", live ? "1" : "0");
    }, [live]);

    useEffect(() => {
        localStorage.setItem("geo_highacc", highAcc ? "1" : "0");
    }, [highAcc]);

    const [lastUpdated, setLastUpdated] = useState<number | null>(null);

    const refresh = async () => {
        setBusy(true);
        try {
            const data = await api.adminWeatherRefresh(Number(lat), Number(lon), 10);
            setLatest(data.latest ?? null);
            setLastUpdated(Date.now());
            toast({ title: "Weather refreshed", description: `ET0 ${data.latest?.et0_mm_day ?? "—"} mm/day` });
        } catch (e) {
            console.error(e);
            const msg = e instanceof Error ? e.message : String(e);
            toast({ title: "Failed to refresh", description: msg, variant: "destructive" });
        } finally {
            setBusy(false);
        }
    };

    const getMyLocation = () => {
        setGeoMsg(null);
        if (!("geolocation" in navigator)) {
            setGeoMsg("Geolocation is not supported by this browser.");
            return;
        }
        setGeoBusy(true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                const la = latitude.toFixed(5);
                const lo = longitude.toFixed(5);
                setLat(la);
                setLon(lo);
                setGeoBusy(false);
                // Auto-refresh with the detected location
                refresh();
            },
            (err) => {
                setGeoBusy(false);
                switch (err.code) {
                    case err.PERMISSION_DENIED:
                        setGeoMsg("Location permission denied. Please allow access and try again.");
                        break;
                    case err.POSITION_UNAVAILABLE:
                        setGeoMsg("Location unavailable. Ensure GPS is on and try again.");
                        break;
                    case err.TIMEOUT:
                        setGeoMsg("Timed out getting location. Try again.");
                        break;
                    default:
                        setGeoMsg("Failed to get location. Try again.");
                }
            },
            { enableHighAccuracy: highAcc, timeout: 10000, maximumAge: 60000 }
        );
    };

    // Live location tracking using watchPosition
    useEffect(() => {
        if (!("geolocation" in navigator)) {
            if (live) setGeoMsg("Geolocation is not supported by this browser.");
            return;
        }
        const stopWatch = () => {
            if (watchIdRef.current != null) {
                navigator.geolocation.clearWatch(watchIdRef.current);
                watchIdRef.current = null;
            }
        };
        if (live) {
            setGeoMsg(null);
            watchIdRef.current = navigator.geolocation.watchPosition(
                (pos) => {
                    const { latitude, longitude } = pos.coords;
                    const la = Number(latitude.toFixed(5));
                    const lo = Number(longitude.toFixed(5));
                    setLat(String(la));
                    setLon(String(lo));
                    const now = Date.now();
                    const last = lastRefreshAtRef.current;
                    const prev = lastCoordsRef.current;
                    const movedEnough = prev ? (Math.abs(prev.lat - la) > 0.001 || Math.abs(prev.lon - lo) > 0.001) : true;
                    if (movedEnough || now - last > 60_000) {
                        lastCoordsRef.current = { lat: la, lon: lo };
                        lastRefreshAtRef.current = now;
                        refresh();
                    }
                },
                (err) => {
                    switch (err.code) {
                        case err.PERMISSION_DENIED:
                            setGeoMsg("Location permission denied. Disable live tracking or allow access.");
                            break;
                        case err.POSITION_UNAVAILABLE:
                            setGeoMsg("Location unavailable. Ensure GPS is on and try again.");
                            break;
                        case err.TIMEOUT:
                            setGeoMsg("Timed out watching location.");
                            break;
                        default:
                            setGeoMsg("Failed to watch location.");
                    }
                },
                { enableHighAccuracy: highAcc, timeout: 10000, maximumAge: 0 }
            );
        } else {
            stopWatch();
        }
        return stopWatch;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [live, highAcc]);

    // If permission already granted, auto-fill on load without prompting
    useEffect(() => {
        const maybeAutofill = async () => {
            try {
                if (navigator.permissions?.query) {
                    const res = await navigator.permissions.query({ name: "geolocation" as PermissionName });
                    if (res && res.state === "granted") getMyLocation();
                }
            } catch {
                // ignore permission query errors
            }
        };
        maybeAutofill();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="max-w-3xl mx-auto p-6 space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Rainwater Harvesting & Weather</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                        Set your farm location to compute daily reference ET0 and cache weather. Use this to size your tank and plan irrigation in dry spells.
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        {/* Lat */}
                        <div className="flex items-center gap-2 min-w-[180px] sm:min-w-0">
                            <label htmlFor="lat" className="text-sm">Lat</label>
                            <input
                                id="lat"
                                name="lat"
                                placeholder="e.g., 27.3"
                                className="border px-3 py-2 rounded-md w-full sm:w-28"
                                value={lat}
                                onChange={(e) => setLat(e.target.value)}
                                inputMode="decimal"
                            />
                        </div>
                        {/* Lon */}
                        <div className="flex items-center gap-2 min-w-[180px] sm:min-w-0">
                            <label htmlFor="lon" className="text-sm">Lon</label>
                            <input
                                id="lon"
                                name="lon"
                                placeholder="e.g., 88.6"
                                className="border px-3 py-2 rounded-md w-full sm:w-28"
                                value={lon}
                                onChange={(e) => setLon(e.target.value)}
                                inputMode="decimal"
                            />
                        </div>
                        {/* Actions */}
                        <div className="flex gap-2">
                            <Button onClick={refresh} disabled={busy} title="Fetch latest weather for the given location">
                                {busy ? "Refreshing…" : "Refresh Weather"}
                            </Button>
                            <Button variant="secondary" onClick={getMyLocation} disabled={geoBusy} title="Use your current GPS location">
                                {geoBusy ? "Getting location…" : "Use my location"}
                            </Button>
                        </div>
                        {/* Toggles */}
                        <div className="flex items-center gap-2">
                            <input id="live" name="live" type="checkbox" className="w-4 h-4" checked={live} onChange={(e) => setLive(e.target.checked)} />
                            <label htmlFor="live" className="text-sm">Live location</label>
                        </div>
                        <div className="flex items-center gap-2">
                            <input id="highacc" name="highacc" type="checkbox" className="w-4 h-4" checked={highAcc} onChange={(e) => setHighAcc(e.target.checked)} />
                            <label htmlFor="highacc" className="text-sm" title="Enable GPS for best accuracy (more battery)">High accuracy</label>
                        </div>
                        {/* Status chip */}
                        <div className={`text-xs px-2 py-1 rounded-full ${live ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"}`} title={highAcc ? "High accuracy enabled" : undefined}>
                            Live: {live ? (highAcc ? "On (high)" : "On") : "Off"}
                        </div>
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                        <span>Location access requires a secure context (HTTPS) on non-localhost sites.</span>
                        {geoMsg ? <span className="text-destructive">{geoMsg}</span> : null}
                        {lastUpdated ? <span className="opacity-80">Last updated: {new Date(lastUpdated).toLocaleTimeString()}</span> : null}
                    </div>
                    {latest ? (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div><span className="text-muted-foreground">Date:</span> {latest.date}</div>
                            <div><span className="text-muted-foreground">ET0 (mm/day):</span> {Number(latest.et0_mm_day).toFixed?.(2) ?? latest.et0_mm_day}</div>
                            <div><span className="text-muted-foreground">Tmin (°C):</span> {Number(latest.tmin_c).toFixed?.(1) ?? latest.tmin_c}</div>
                            <div><span className="text-muted-foreground">Tmax (°C):</span> {Number(latest.tmax_c).toFixed?.(1) ?? latest.tmax_c}</div>
                        </div>
                    ) : (
                        <div className="text-sm text-muted-foreground">No cached weather yet. Click Refresh Weather.</div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
