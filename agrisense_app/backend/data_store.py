import os, sqlite3, datetime as dt
from typing import Dict, Any, List

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
    conn.commit()
    return conn

def insert_reading(r: Dict[str, Any]):
    conn = get_conn()
    ts = r.get("timestamp") or dt.datetime.utcnow().isoformat()
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