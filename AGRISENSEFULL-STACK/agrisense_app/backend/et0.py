from __future__ import annotations
__all__ = ["extraterrestrial_radiation_ra", "et0_hargreaves"]
"""
ET0 helpers (FAO-56/Hargreaves) for irrigation modeling.

Implements:
- extraterrestrial_radiation_ra: MJ/m^2/day for a given latitude and day-of-year
- et0_hargreaves: FAO alternative when full weather data is missing

References:
- FAO-56 Irrigation and Drainage Paper 56 (Chapter 3, equations 21, 22-26, 52)
"""
import math


def extraterrestrial_radiation_ra(lat_deg: float, day_of_year: int) -> float:
    """Compute extraterrestrial radiation Ra (MJ m^-2 day^-1) per FAO-56 Eq. 21.

    lat_deg: latitude in decimal degrees (+N, -S)
    day_of_year: J, 1..365/366
    """
    # Convert degrees to radians (Eq. 22)
    phi = math.radians(lat_deg)
    # Inverse relative distance Earth-Sun (Eq. 23)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365.0)
    # Solar declination (Eq. 24)
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365.0 - 1.39)
    # Sunset hour angle (Eq. 25)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    # Solar constant Gsc = 0.0820 MJ m^-2 min^-1, 24*60/pi ≈ 37.586
    Gsc = 0.0820
    Ra = (
        (24 * 60 / math.pi)
        * Gsc
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )
    return max(0.0, Ra)


def et0_hargreaves(tmin_c: float, tmax_c: float, tmean_c: float, ra_MJ_m2_day: float) -> float:
    """Estimate daily reference evapotranspiration ET0 (mm/day) via Hargreaves (FAO-56 Eq. 52).

    ETo = 0.0023 (Tmean + 17.8) (Tmax - Tmin)^0.5 * Ra
    where Ra is extraterrestrial radiation (MJ m^-2 d^-1) and ETo is in mm/day.
    """
    dT = max(0.0, tmax_c - tmin_c)
    return max(0.0, 0.0023 * (tmean_c + 17.8) * math.sqrt(dT) * ra_MJ_m2_day)
