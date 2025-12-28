"""
Lightweight weather helper to fetch daily Tmin/Tmax and compute ET0 using Hargreaves.

Uses Open-Meteo public API (no key required). Intended for offline caching and
feeding AGRISENSE_WEATHER_CACHE for the engine's optional ET0 adjustment.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Dict, List, TypedDict, Mapping, Union, cast

import requests  # type: ignore[reportMissingImports]

try:
    from . import et0 as et
except Exception:
    import et0 as et  # type: ignore


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class _Params(TypedDict):
    latitude: float
    longitude: float
    daily: str
    past_days: int
    forecast_days: int
    timezone: str


def fetch_and_cache_weather(
    lat: float,
    lon: float,
    days: int = 7,
    cache_path: str | Path = "weather_cache.csv",
    timezone: str = "auto",
) -> Path:
    """
    Fetch recent daily Tmin/Tmax and compute ET0; append/overwrite a simple CSV cache.

    CSV columns: date,doy,lat,lon,tmin_c,tmax_c,tmean_c,ra_mj_m2_day,et0_mm_day
    """
    params: _Params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_min,temperature_2m_max",
        "past_days": days,
        "forecast_days": 1,
        "timezone": timezone,
    }
    params_mapping: Mapping[str, Union[str, float, int]] = cast(Mapping[str, Union[str, float, int]], params)
    r = requests.get(OPEN_METEO_URL, params=params_mapping, timeout=20)
    r.raise_for_status()
    data = r.json()
    dates: List[str] = data["daily"]["time"]
    tmins: List[float] = data["daily"]["temperature_2m_min"]
    tmaxs: List[float] = data["daily"]["temperature_2m_max"]

    rows: List[Dict[str, str]] = []
    for d, tmin, tmax in zip(dates, tmins, tmaxs):
        y, m, dd = map(int, d.split("-"))
        date_obj = dt.date(y, m, dd)
        doy = (date_obj - dt.date(y, 1, 1)).days + 1
        tmean = (tmin + tmax) / 2.0
        ra = et.extraterrestrial_radiation_ra(lat, doy)
        et0_v = et.et0_hargreaves(tmin, tmax, tmean, ra)
        rows.append(
            {
                "date": d,
                "doy": str(doy),
                "lat": f"{lat}",
                "lon": f"{lon}",
                "tmin_c": f"{tmin:.3f}",
                "tmax_c": f"{tmax:.3f}",
                "tmean_c": f"{tmean:.3f}",
                "ra_mj_m2_day": f"{ra:.5f}",
                "et0_mm_day": f"{et0_v:.5f}",
            }
        )

    cache_path = Path(cache_path)
    # Write all fetched rows (dedupe by date if file exists)
    existing: Dict[str, Dict[str, str]] = {}
    if cache_path.exists():
        with cache_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "date" in row:
                    existing[row["date"]] = row
    for row in rows:
        existing[row["date"]] = row

    with cache_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "doy",
            "lat",
            "lon",
            "tmin_c",
            "tmax_c",
            "tmean_c",
            "ra_mj_m2_day",
            "et0_mm_day",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in sorted(existing.keys()):
            writer.writerow(existing[d])

    return cache_path


def read_latest_from_cache(cache_path: str | Path) -> Dict[str, str]:
    cache_path = Path(cache_path)
    with cache_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        last = None
        for row in reader:
            last = row
    if not last:
        raise RuntimeError("weather cache is empty")
    return last


def update_weather_data(lat: float = 27.35, lon: float = 88.6, days: int = 7) -> Dict[str, str]:
    """Update weather data and return latest values"""
    try:
        cache_path = fetch_and_cache_weather(lat, lon, days)
        return read_latest_from_cache(cache_path)
    except Exception as e:
        return {"error": str(e), "status": "failed"}
