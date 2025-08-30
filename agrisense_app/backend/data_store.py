import os, sqlite3, datetime as dt
from typing import Dict, Any, List, Optional

HERE = os.path.dirname(__file__)
# Allow overriding the database path for containerized deployments.
# Prefer explicit AGRISENSE_DB_PATH, else use AGRISENSE_DATA_DIR/sensors.db, else default next to this file.
_DATA_DIR = os.getenv("AGRISENSE_DATA_DIR")
if _DATA_DIR:
    os.makedirs(_DATA_DIR, exist_ok=True)
DB_PATH = os.getenv("AGRISENSE_DB_PATH") or os.path.join(_DATA_DIR or HERE, "sensors.db")

def get_conn():
    # Ensure directory for DB exists (covers default and custom locations)
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    except Exception:
        # Fallback to module directory
        os.makedirs(HERE, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS readings(
        ts TEXT, zone_id TEXT, plant TEXT, soil_type TEXT,
        area_m2 REAL, ph REAL, moisture_pct REAL, temperature_c REAL,
        ec_dS_m REAL, n_ppm REAL, p_ppm REAL, k_ppm REAL
    )
    ''')
    # Store recommendation snapshots to enable trend graphs
    conn.execute('''
    CREATE TABLE IF NOT EXISTS reco_history(
        ts TEXT, zone_id TEXT, plant TEXT,
        water_liters REAL,
        expected_savings_liters REAL,
        fert_n_g REAL, fert_p_g REAL, fert_k_g REAL,
        yield_potential REAL
    )
    ''')
    # Water tank levels (for rainwater harvesting storage)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS tank_levels(
        ts TEXT, tank_id TEXT, level_pct REAL, volume_l REAL, rainfall_mm REAL
    )
    ''')
    # Valve actuation history for irrigation control
    conn.execute('''
    CREATE TABLE IF NOT EXISTS valve_events(
        ts TEXT, zone_id TEXT, action TEXT, duration_s REAL, status TEXT
    )
    ''')
    # Alerts log (SMS/app)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS alerts(
        ts TEXT, zone_id TEXT, category TEXT, message TEXT, sent INTEGER
    )
    ''')
    conn.commit()
    return conn

def reset_database() -> None:
    """Erase all stored data by deleting the SQLite database file.
    Tables will be recreated on next connection.
    """
    try:
        if os.path.exists(DB_PATH):
            # Close any lingering connections by opening and closing quickly
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.close()
            except Exception:
                pass
            os.remove(DB_PATH)
    except Exception:
        # Fallback: truncate tables if file removal fails
        try:
            conn = sqlite3.connect(DB_PATH)
            for tbl in ("readings", "reco_history", "tank_levels", "valve_events", "alerts"):
                try:
                    conn.execute(f"DELETE FROM {tbl}")
                except Exception:
                    pass
            conn.commit()
            conn.close()
        except Exception:
            pass

def insert_reading(r: Dict[str, Any]):
    conn = get_conn()
    ts = r.get("timestamp") or dt.datetime.now(dt.timezone.utc).isoformat()
    vals = (
        ts, r.get("zone_id","Z1"), r.get("plant","generic"), r.get("soil_type","loam"),
        float(r.get("area_m2",100.0)), float(r.get("ph",6.5)), float(r.get("moisture_pct",35.0)),
        float(r.get("temperature_c",28.0)), float(r.get("ec_dS_m",1.0)),
        r.get("n_ppm"), r.get("p_ppm"), r.get("k_ppm")
    )
    conn.execute("INSERT INTO readings VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()

def recent(zone_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM readings WHERE zone_id=? ORDER BY ts DESC LIMIT ?", (zone_id, limit))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

def insert_reco_snapshot(zone_id: str, plant: str, rec: Dict[str, Any], yield_potential: Optional[float] = None) -> None:
    conn = get_conn()
    ts = rec.get("timestamp") or dt.datetime.now(dt.timezone.utc).isoformat()
    vals = (
        ts,
        zone_id,
        plant,
        float(rec.get("water_liters", 0.0)),
        float(rec.get("expected_savings_liters", 0.0)),
        float(rec.get("fert_n_g", 0.0)),
        float(rec.get("fert_p_g", 0.0)),
        float(rec.get("fert_k_g", 0.0)),
        float(yield_potential) if yield_potential is not None else None,
    )
    conn.execute("INSERT INTO reco_history VALUES (?,?,?,?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()

def recent_reco(zone_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT * FROM reco_history WHERE zone_id=? ORDER BY ts DESC LIMIT ?",
        (zone_id, limit),
    )
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

# --- Tank levels ---
def insert_tank_level(tank_id: str, level_pct: float, volume_l: float, rainfall_mm: float = 0.0) -> None:
    conn = get_conn()
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute("INSERT INTO tank_levels VALUES (?,?,?,?,?)", (ts, tank_id, float(level_pct), float(volume_l), float(rainfall_mm)))
    conn.commit()
    conn.close()

def latest_tank_level(tank_id: str = "T1") -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT * FROM tank_levels WHERE tank_id=? ORDER BY ts DESC LIMIT 1", (tank_id,))
    row = cur.fetchone()
    result = None
    if row is not None:
        cols = [c[0] for c in cur.description]
        result = dict(zip(cols, row))
    conn.close()
    return result

# --- Valve events ---
def log_valve_event(zone_id: str, action: str, duration_s: float = 0.0, status: str = "queued") -> None:
    conn = get_conn()
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute("INSERT INTO valve_events VALUES (?,?,?,?,?)", (ts, zone_id, action, float(duration_s), status))
    conn.commit()
    conn.close()

def recent_valve_events(zone_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_conn()
    if zone_id:
        cur = conn.execute("SELECT * FROM valve_events WHERE zone_id=? ORDER BY ts DESC LIMIT ?", (zone_id, limit))
    else:
        cur = conn.execute("SELECT * FROM valve_events ORDER BY ts DESC LIMIT ?", (limit,))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

# --- Alerts ---
def insert_alert(zone_id: str, category: str, message: str, sent: bool = False) -> None:
    conn = get_conn()
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute("INSERT INTO alerts VALUES (?,?,?,?,?)", (ts, zone_id, category, message, 1 if sent else 0))
    conn.commit()
    conn.close()

def recent_alerts(zone_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_conn()
    if zone_id:
        cur = conn.execute("SELECT * FROM alerts WHERE zone_id=? ORDER BY ts DESC LIMIT ?", (zone_id, limit))
    else:
        cur = conn.execute("SELECT * FROM alerts ORDER BY ts DESC LIMIT ?", (limit,))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows