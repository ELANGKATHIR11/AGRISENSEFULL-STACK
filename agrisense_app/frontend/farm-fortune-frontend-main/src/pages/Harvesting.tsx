import { useEffect, useState } from "react";
import { api, type WeatherCacheRow } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Harvesting() {
    const [lat, setLat] = useState<string>(() => localStorage.getItem("lat") || "27.3");
    const [lon, setLon] = useState<string>(() => localStorage.getItem("lon") || "88.6");
    const [latest, setLatest] = useState<WeatherCacheRow | null>(null);
    const [busy, setBusy] = useState(false);
    const [geoBusy, setGeoBusy] = useState(false);
    const [geoMsg, setGeoMsg] = useState<string | null>(null);

    useEffect(() => {
        localStorage.setItem("lat", lat);
        localStorage.setItem("lon", lon);
    }, [lat, lon]);

    const refresh = async () => {
        setBusy(true);
        try {
            const data = await api.adminWeatherRefresh(Number(lat), Number(lon), 10);
            setLatest(data.latest ?? null);
        } catch (e) {
            console.error(e);
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
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
        );
    };

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
                    <div className="flex items-center gap-3">
                        <label htmlFor="lat" className="text-sm">Lat</label>
                        <input
                            id="lat"
                            name="lat"
                            placeholder="e.g., 27.3"
                            className="border px-3 py-2 rounded-md w-28"
                            value={lat}
                            onChange={(e) => setLat(e.target.value)}
                            inputMode="decimal"
                        />
                        <label htmlFor="lon" className="text-sm">Lon</label>
                        <input
                            id="lon"
                            name="lon"
                            placeholder="e.g., 88.6"
                            className="border px-3 py-2 rounded-md w-28"
                            value={lon}
                            onChange={(e) => setLon(e.target.value)}
                            inputMode="decimal"
                        />
                        <Button onClick={refresh} disabled={busy} title="Fetch latest weather for the given location">
                            {busy ? "Refreshing…" : "Refresh Weather"}
                        </Button>
                        <Button variant="secondary" onClick={getMyLocation} disabled={geoBusy} title="Use your current GPS location">
                            {geoBusy ? "Getting location…" : "Use my location"}
                        </Button>
                    </div>
                    <div className="text-xs text-muted-foreground">
                        Location access requires a secure context (HTTPS) on non-localhost sites. {geoMsg ?? ""}
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
