import { useEffect, useRef, useState } from "react";
import { api, type WeatherCacheRow } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
// Use ESM imports for Leaflet marker images to satisfy TS and bundlers
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

// Fix default icon path issue for Leaflet when used with bundlers
// cast to unknown first to avoid 'any' complaints and then to the expected shape
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: (markerIcon2x as unknown) as string,
    iconUrl: (markerIcon as unknown) as string,
    shadowUrl: (markerShadow as unknown) as string,
});

export default function Harvesting() {
    const { toast } = useToast();
    // store coords as strings for inputs but also keep exact numeric device coords
    const [lat, setLat] = useState<string>(() => localStorage.getItem("lat") || "27.300000");
    const [lon, setLon] = useState<string>(() => localStorage.getItem("lon") || "88.600000");
    const [exactCoords, setExactCoords] = useState<{ lat: number; lon: number } | null>(null);
    // Local extended weather shape: backend WeatherCacheRow plus a few realtime fields
    type LocalWeather = WeatherCacheRow & {
        current_temp_c?: number;
        windspeed?: number;
        weathercode?: number;
        humidity?: number;
    };
    // latest may come from backend cache or direct public weather API
    const [latest, setLatest] = useState<Partial<LocalWeather> | null>(null);
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

    // react-leaflet typing varies between versions in this project; create any-casted aliases
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const AnyMapContainer = MapContainer as unknown as any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const AnyTileLayer = TileLayer as unknown as any;

    const refresh = async () => {
        setBusy(true);
        try {
            // Prefer direct public weather API (Open-Meteo) using exact device coords when available.
            const la = exactCoords ? exactCoords.lat : Number(lat);
            const lo = exactCoords ? exactCoords.lon : Number(lon);
            const url = `https://api.open-meteo.com/v1/forecast?latitude=${la}&longitude=${lo}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,precipitation&timezone=auto`;
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`Open-Meteo ${resp.status}`);
            const json = await resp.json();
            const cw = json.current_weather;
            // compute daily min/max from hourly if present
            const temps: number[] = Array.isArray(json.hourly?.temperature_2m)
                ? (json.hourly.temperature_2m as number[]).map((v) => Number(v))
                : [];
            const tmin = temps.length ? Math.min(...temps) : cw.temperature;
            const tmax = temps.length ? Math.max(...temps) : cw.temperature;
            const humidityArr: number[] = Array.isArray(json.hourly?.relativehumidity_2m)
                ? (json.hourly.relativehumidity_2m as number[])
                : [];
            const humidityNow = humidityArr.length ? Number(humidityArr[0]) : undefined;
            setLatest({
                date: new Date(cw.time).toISOString().slice(0, 10),
                et0_mm_day: String(0),
                tmin_c: String(tmin),
                tmax_c: String(tmax),
                current_temp_c: cw.temperature,
                windspeed: cw.windspeed,
                weathercode: cw.weathercode,
                humidity: humidityNow,
            } as Partial<LocalWeather>);
            setLastUpdated(Date.now());
            toast({ title: "Weather refreshed", description: `Temp ${cw.temperature}°C, wind ${cw.windspeed} m/s` });
            setBusy(false);
            return;
        } catch (e) {
            // If Open-Meteo fails, fall back to backend admin refresh (may require admin token)
            try {
                const data = await api.adminWeatherRefresh(Number(lat), Number(lon), 10);
                setLatest(data.latest ?? null);
                setLastUpdated(Date.now());
                toast({ title: "Weather refreshed (backend)", description: `ET0 ${data.latest?.et0_mm_day ?? "—"} mm/day` });
            } catch (inner) {
                console.error(e, inner);
                const msg = inner instanceof Error ? inner.message : (e instanceof Error ? e.message : String(e));
                toast({ title: "Failed to refresh", description: msg, variant: "destructive" });
            }
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
                // keep exact coords for map and weather queries; show 6 decimals in inputs
                setExactCoords({ lat: latitude, lon: longitude });
                setLat(latitude.toFixed(6));
                setLon(longitude.toFixed(6));
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
            { enableHighAccuracy: highAcc, timeout: 20000, maximumAge: 0 }
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
                    // Update exact device coords and display-friendly inputs
                    setExactCoords({ lat: latitude, lon: longitude });
                    const la = Number(latitude.toFixed(6));
                    const lo = Number(longitude.toFixed(6));
                    setLat(String(la));
                    setLon(String(lo));
                    const now = Date.now();
                    const last = lastRefreshAtRef.current;
                    const prev = lastCoordsRef.current;
                    const movedEnough = prev ? (Math.abs(prev.lat - la) > 0.0001 || Math.abs(prev.lon - lo) > 0.0001) : true;
                    if (movedEnough || now - last > 30_000) {
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
                { enableHighAccuracy: highAcc, timeout: 20000, maximumAge: 0 }
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

    // Map uses exact device coords when available (higher precision). Fall back to parsed input.
    const parsedLat = exactCoords ? exactCoords.lat : Number(lat) || 0;
    const parsedLon = exactCoords ? exactCoords.lon : Number(lon) || 0;
    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
    }, []);

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-6">
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
                                placeholder="e.g., 27.300000"
                                className="border px-3 py-2 rounded-md w-full sm:w-36"
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
                                placeholder="e.g., 88.600000"
                                className="border px-3 py-2 rounded-md w-full sm:w-36"
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

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div>
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
                        </div>

                        <div className="h-72 w-full rounded-md overflow-hidden border">
                            {/* Only render Leaflet map after client mount to avoid hydration/render issues */}
                            {mounted ? (
                                <AnyMapContainer center={[parsedLat, parsedLon]} zoom={13} style={{ height: "100%", width: "100%" }} key={`${parsedLat}-${parsedLon}`}>
                                    <AnyTileLayer
                                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    />
                                    <Marker position={[parsedLat, parsedLon]}>
                                        <Popup>
                                            Device location<br />{parsedLat.toFixed(6)}, {parsedLon.toFixed(6)}
                                        </Popup>
                                    </Marker>
                                </AnyMapContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full w-full text-sm text-muted-foreground">Map loading…</div>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
