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
    # Store individual tips for richer analytics
    conn.execute('''
    CREATE TABLE IF NOT EXISTS reco_tips(
        ts TEXT, zone_id TEXT, plant TEXT,
        tip TEXT, category TEXT
    )
    ''')
    # Water tank levels (for rainwater harvesting storage)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS tank_levels(
        ts TEXT, tank_id TEXT, level_pct REAL, volume_l REAL, rainfall_mm REAL
    )
    ''')
    # Rainwater harvesting ledger for collections/usages
    conn.execute('''
    CREATE TABLE IF NOT EXISTS rainwater_harvest(
        ts TEXT, tank_id TEXT, collected_liters REAL, used_liters REAL
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

def _ensure_reco_history_columns(conn) -> None:
    """Idempotently add new columns to reco_history if missing."""
    try:
        cur = conn.execute("PRAGMA table_info(reco_history)")
        cols = [row[1] for row in cur.fetchall()]
        if "water_source" not in cols:
            try:
                conn.execute("ALTER TABLE reco_history ADD COLUMN water_source TEXT")
            except Exception:
                pass
        if "tips" not in cols:
            try:
                conn.execute("ALTER TABLE reco_history ADD COLUMN tips TEXT")
            except Exception:
                pass
    except Exception:
        pass


def insert_reco_snapshot(zone_id: str, plant: str, rec: Dict[str, Any], yield_potential: Optional[float] = None) -> None:
    conn = get_conn()
    _ensure_reco_history_columns(conn)
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
    # Insert base columns first
    conn.execute("INSERT INTO reco_history (ts, zone_id, plant, water_liters, expected_savings_liters, fert_n_g, fert_p_g, fert_k_g, yield_potential) VALUES (?,?,?,?,?,?,?,?,?)", vals)
    # Update water_source and tips if present
    try:
        ws = rec.get("water_source")
        if ws is not None:
            conn.execute("UPDATE reco_history SET water_source=? WHERE ts=? AND zone_id=?", (str(ws), ts, zone_id))
    except Exception:
        pass
    try:
        tips = rec.get("tips")
        if isinstance(tips, list) and tips:
            # Store as a single string joined by ' | ' to keep schema simple
            s = " | ".join(str(x) for x in tips)
            conn.execute("UPDATE reco_history SET tips=? WHERE ts=? AND zone_id=?", (s, ts, zone_id))
    except Exception:
        pass
    # Insert individual tips, categorize by simple heuristics
    try:
        tips = rec.get("tips")
        if isinstance(tips, list):
            for tip in tips:
                t = str(tip)
                cat = "other"
                lower = t.lower()
                if "ph " in lower:
                    cat = "ph"
                elif "moisture" in lower or "%" in lower:
                    cat = "moisture"
                elif "ec" in lower or "salinity" in lower:
                    cat = "ec"
                elif "nitrogen" in lower or "urea" in lower:
                    cat = "nitrogen"
                elif "phosphorus" in lower or "dap" in lower:
                    cat = "phosphorus"
                elif "potassium" in lower or "mop" in lower:
                    cat = "potassium"
                elif "temperature" in lower or "irrigation" in lower or "mulch" in lower:
                    cat = "climate"
                conn.execute("INSERT INTO reco_tips VALUES (?,?,?,?,?)", (ts, zone_id, plant, t, cat))
    except Exception:
        pass
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

def recent_tank_levels(tank_id: str = "T1", limit: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return recent tank level rows for a tank, optionally filtered by ISO timestamp 'since'.
    Results are ordered DESC by ts and limited to 'limit'.
    """
    conn = get_conn()
    try:
        if since:
            cur = conn.execute(
                "SELECT * FROM tank_levels WHERE tank_id=? AND ts>=? ORDER BY ts DESC LIMIT ?",
                (tank_id, since, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM tank_levels WHERE tank_id=? ORDER BY ts DESC LIMIT ?",
                (tank_id, limit),
            )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return rows
    finally:
        conn.close()

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

# --- Rainwater ledger helpers ---
def insert_rainwater_entry(tank_id: str, collected_liters: float = 0.0, used_liters: float = 0.0) -> None:
    conn = get_conn()
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    conn.execute("INSERT INTO rainwater_harvest VALUES (?,?,?,?)", (ts, tank_id, float(collected_liters), float(used_liters)))
    conn.commit()
    conn.close()

def rainwater_summary(tank_id: str = "T1") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT IFNULL(SUM(collected_liters),0), IFNULL(SUM(used_liters),0) FROM rainwater_harvest WHERE tank_id=?",
        (tank_id,),
    )
    row = cur.fetchone() or (0.0, 0.0)
    collected, used = float(row[0] or 0.0), float(row[1] or 0.0)
    conn.close()
    return {"tank_id": tank_id, "collected_total_l": collected, "used_total_l": used, "net_l": collected - used}

def recent_rainwater(tank_id: str = "T1", limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT * FROM rainwater_harvest WHERE tank_id=? ORDER BY ts DESC LIMIT ?",
        (tank_id, limit),
    )
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows

# --- Alerts ack ---
def mark_alert_ack(ts: str) -> None:
    conn = get_conn()
    # Mark as sent=1 to indicate acknowledged; or could add a new column in a future migration
    conn.execute("UPDATE alerts SET sent=1 WHERE ts=?", (ts,))
    conn.commit()
    conn.close()