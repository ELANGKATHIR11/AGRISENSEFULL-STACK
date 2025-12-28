import os
from typing import Any, Dict, List, Optional
import datetime as dt

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING  # type: ignore
    from pymongo.collection import Collection  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    MongoClient = None  # type: ignore
    ASCENDING = 1  # type: ignore[assignment]
    DESCENDING = -1  # type: ignore[assignment]
    from typing import Any as _Any

    Collection = _Any  # type: ignore


def _get_db():
    if MongoClient is None:
        raise ImportError("pymongo is not installed. Set AGRISENSE_DB=sqlite or install pymongo to use Mongo storage.")
    uri = os.getenv("AGRISENSE_MONGO_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
    dbname = os.getenv("AGRISENSE_MONGO_DB") or os.getenv("MONGO_DB") or "agrisense"
    client = MongoClient(uri)
    db = client[dbname]
    # Ensure indexes (idempotent)
    db["readings"].create_index([("ts", DESCENDING)])
    db["readings"].create_index([("zone_id", ASCENDING), ("ts", DESCENDING)])
    db["reco_history"].create_index([("ts", DESCENDING)])
    db["reco_history"].create_index([("zone_id", ASCENDING), ("ts", DESCENDING)])
    db["tank_levels"].create_index([("tank_id", ASCENDING), ("ts", DESCENDING)])
    db["valve_events"].create_index([("zone_id", ASCENDING), ("ts", DESCENDING)])
    db["alerts"].create_index([("ts", DESCENDING)])
    db["rainwater_harvest"].create_index([("tank_id", ASCENDING), ("ts", DESCENDING)])
    return db


_db = _get_db()
# Avoid strict type annotations here to keep this module importable without pymongo in type-checking environments
_readings = _db["readings"]
_reco = _db["reco_history"]
_tank = _db["tank_levels"]
_valves = _db["valve_events"]
_alerts = _db["alerts"]
_rain = _db["rainwater_harvest"]


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _clean(doc: Dict[str, Any]) -> Dict[str, Any]:
    # Convert _id to string and drop None values for cleaner API parity
    out = {k: v for k, v in doc.items() if v is not None and k != "_id"}
    if doc.get("_id") is not None:
        out["id"] = str(doc["_id"])  # optional exposure
    return out


# --- readings ---
def insert_reading(r: Dict[str, Any]) -> None:
    doc = dict(r)
    doc.setdefault("ts", r.get("timestamp") or _iso_now())
    _readings.insert_one(doc)


def recent(zone_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    cur = _readings.find({"zone_id": zone_id}).sort("ts", DESCENDING).limit(int(limit))
    return [_clean(d) for d in cur]


# --- reco history ---
def insert_reco_snapshot(
    zone_id: str,
    plant: str,
    rec: Dict[str, Any],
    yield_potential: Optional[float] = None,
) -> None:
    doc: Dict[str, Any] = {
        "ts": rec.get("timestamp") or _iso_now(),
        "zone_id": zone_id,
        "plant": plant,
        "water_liters": float(rec.get("water_liters", 0.0) or 0.0),
        "expected_savings_liters": float(rec.get("expected_savings_liters", 0.0) or 0.0),
        "fert_n_g": float(rec.get("fert_n_g", 0.0) or 0.0),
        "fert_p_g": float(rec.get("fert_p_g", 0.0) or 0.0),
        "fert_k_g": float(rec.get("fert_k_g", 0.0) or 0.0),
        "yield_potential": (float(yield_potential) if yield_potential is not None else None),
        "water_source": rec.get("water_source"),
    }
    # Store tips as-is if present
    tips = rec.get("tips")
    if isinstance(tips, list):
        doc["tips"] = [str(x) for x in tips]
    _reco.insert_one(doc)


def recent_reco(zone_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    cur = _reco.find({"zone_id": zone_id}).sort("ts", DESCENDING).limit(int(limit))
    return [_clean(d) for d in cur]


# --- tank levels ---
def insert_tank_level(tank_id: str, level_pct: float, volume_l: float, rainfall_mm: float = 0.0) -> None:
    _tank.insert_one(
        {
            "ts": _iso_now(),
            "tank_id": tank_id,
            "level_pct": float(level_pct),
            "volume_l": float(volume_l),
            "rainfall_mm": float(rainfall_mm),
        }
    )


def latest_tank_level(tank_id: str = "T1") -> Optional[Dict[str, Any]]:
    doc = _tank.find_one({"tank_id": tank_id}, sort=[("ts", DESCENDING)])
    return _clean(doc) if doc else None


# --- valve events ---
def log_valve_event(zone_id: str, action: str, duration_s: float = 0.0, status: str = "queued") -> None:
    _valves.insert_one(
        {
            "ts": _iso_now(),
            "zone_id": zone_id,
            "action": action,
            "duration_s": float(duration_s),
            "status": status,
        }
    )


def recent_valve_events(zone_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    filt: Dict[str, Any] = {"zone_id": zone_id} if zone_id else {}
    cur = _valves.find(filt).sort("ts", DESCENDING).limit(int(limit))
    return [_clean(d) for d in cur]


# --- alerts ---
def insert_alert(zone_id: str, category: str, message: str, sent: bool = False) -> None:
    _alerts.insert_one(
        {
            "ts": _iso_now(),
            "zone_id": zone_id,
            "category": category,
            "message": message,
            "sent": bool(sent),
        }
    )


def recent_alerts(zone_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    filt: Dict[str, Any] = {"zone_id": zone_id} if zone_id else {}
    cur = _alerts.find(filt).sort("ts", DESCENDING).limit(int(limit))
    return [_clean(d) for d in cur]


def mark_alert_ack(ts: str) -> None:
    _alerts.update_one({"ts": ts}, {"$set": {"sent": True}})


# --- rainwater ---
def insert_rainwater_entry(tank_id: str, collected_liters: float = 0.0, used_liters: float = 0.0) -> None:
    _rain.insert_one(
        {
            "ts": _iso_now(),
            "tank_id": tank_id,
            "collected_liters": float(collected_liters),
            "used_liters": float(used_liters),
        }
    )


def rainwater_summary(tank_id: str = "T1") -> Dict[str, Any]:
    pipeline = [
        {"$match": {"tank_id": tank_id}},
        {
            "$group": {
                "_id": None,
                "collected": {"$sum": {"$ifNull": ["$collected_liters", 0]}},
                "used": {"$sum": {"$ifNull": ["$used_liters", 0]}},
            }
        },
    ]
    agg = list(_rain.aggregate(pipeline))
    if agg:
        collected = float(agg[0].get("collected", 0.0) or 0.0)
        used = float(agg[0].get("used", 0.0) or 0.0)
    else:
        collected = 0.0
        used = 0.0
    return {
        "tank_id": tank_id,
        "collected_total_l": collected,
        "used_total_l": used,
        "net_l": collected - used,
    }


def recent_rainwater(tank_id: str = "T1", limit: int = 10) -> List[Dict[str, Any]]:
    cur = _rain.find({"tank_id": tank_id}).sort("ts", DESCENDING).limit(int(limit))
    return [_clean(d) for d in cur]


# --- admin ---
def reset_database() -> None:
    global _db, _readings, _reco, _tank, _valves, _alerts, _rain
    # Drop collections to clear state; will be recreated lazily via indexes
    for name in (
        "readings",
        "reco_history",
        "tank_levels",
        "valve_events",
        "alerts",
        "rainwater_harvest",
    ):
        try:
            _db[name].drop()
        except Exception:
            pass
    # Recreate indexes via _get_db
    _db = _get_db()
    _readings = _db["readings"]
    _reco = _db["reco_history"]
    _tank = _db["tank_levels"]
    _valves = _db["valve_events"]
    _alerts = _db["alerts"]
    _rain = _db["rainwater_harvest"]
