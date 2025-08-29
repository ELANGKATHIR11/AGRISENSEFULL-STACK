import os, sqlite3, datetime as dt
from typing import Dict, Any, List, Optional

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "sensors.db")

def get_conn():
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
    conn.commit()
    return conn

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