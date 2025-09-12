# HACKATHON_UPGRADE_PLAN.md
AgroSmart (SIH 2025 – Problem Statement 25062)
================================================

This file documents **all changes and upgrades** needed to make the AgriSense full-stack project **hackathon-ready** for SIH 2025.  
Place this file in the **repo root** so GitHub Copilot can use it for code generation.

---

## 📂 Backend (FastAPI – `agrisense_app/backend/`)

### 1. Engine (`engine.py`)
- **Enhance irrigation recommendation**:
  - Factor **rainwater tank levels** before recommending groundwater usage.
  - Add new field in recommendation JSON:
    ```json
    {
      "water_source": "tank" | "groundwater"
    }
    ```
- Add **“best time to irrigate”** logic (morning/evening).
- Add fertilizer equivalents (Urea/DAP/MOP).
- Add “skip irrigation” note if soil is moist enough.

### 2. API Routes (`main.py` / `routes/`)
- **New/Updated Endpoints:**
  - `GET /tank/status` → returns tank capacity (liters, %).
  - `POST /tank/level` → store water level from ESP32.
  - `POST /alerts` → extend categories (`LOW_TANK`, `RECOMMENDATION`, `OVERWATER`).
  - `POST /edge/ingest` → accept real sensor data from ESP32.
- Update `/recommend` response to include:
  - Water source (tank/groundwater).
  - Impact metrics: liters saved, ₹ saved, CO₂ saved.

### 3. Database (`data_store.py`)
- Extend SQLite schema:
  ```sql
  CREATE TABLE IF NOT EXISTS rainwater_harvest (
    ts TEXT,
    tank_id TEXT,
    collected_liters REAL,
    used_liters REAL
  );
  ```
- Add `water_source` column to `reco_history`.

### 4. Models (`models.py`)
- Update `Recommendation` model:
  ```python
  class Recommendation(BaseModel):
      water_liters: float
      fert_n_g: float
      fert_p_g: float
      fert_k_g: float
      water_source: str  # "tank" or "groundwater"
      best_time: str
      fertilizer_equivalents: dict
      expected_savings_liters: float
      expected_cost_saving_rs: float
      expected_co2e_kg: float
      notes: List[str]
  ```

### 5. Notifications (`notifier.py`)
- Add Twilio SMS integration for:
  - Tank low warnings.
  - Irrigation recommendation alerts.
- Add Push notification hook (Firebase optional).

---

## 📂 Edge (ESP32 + Raspberry Pi)

### 1. ESP32 Firmware
- Reads sensors:
  - Soil moisture (capacitive).
  - Temperature & humidity (DHT22/BME280).
  - pH sensor.
  - EC probe.
  - Ultrasonic tank sensor.
- Publishes data to:
  - `POST /edge/ingest` (HTTP) OR
  - MQTT topic `agrosmart/edge/data`.

### 2. Valve Control
- ESP32 subscribes to `agrosmart/<zone_id>/command`.
- Commands:
  - `{"action": "start", "duration_s": 120}`
  - `{"action": "stop"}`

---

## 📂 ML Models (`agrisense_app/scripts/train_models.py`)

### 1. Dataset
- Replace **`india_crop_dataset.csv`** with **`sikkim_crop_dataset.csv`**.
- Include:
  - Cardamom, ginger, turmeric, maize, paddy, vegetables.
  - Ideal soil pH, moisture %, NPK levels, water needs.

### 2. Training
- Retrain:
  - `crop_classification_model.joblib`
  - `yield_prediction_model.joblib`
- Ensure model outputs:
  - Recommended crops for Sikkim.
  - Irrigation optimized with harvested water logic.

---

## 📂 Frontend (`frontend/farm-fortune-frontend-main/`)

### 1. Dashboard (`Dashboard.jsx`)
- Add:
  - **Tank Level Gauge** (liters, %).
  - **Live Sensor Cards** (moisture, pH, EC, temp, humidity).
  - **Alerts Panel** (low tank, overwater).
- Display impact metrics from backend:
  - Water saved.
  - Cost saved.
  - CO₂ saved.
- Multilingual Support:
  - English + Nepali toggle.

### 2. Irrigation Control
- Add **Start/Stop buttons**.
- Call `/irrigation/start` and `/irrigation/stop`.

---

## 📂 Mobile App (`mobile_app/`)

### 1. Features (React Native)
- Live display of:
  - Soil data.
  - Tank status.
- Recommendations (from `/recommend`).
- Control buttons (Start/Stop irrigation).
- SMS/App alerts.
- Offline-first (connects to local Pi hotspot).

---

## 📂 Deployment

### 1. Raspberry Pi (Hackathon Demo)
- Run backend on Pi:
  ```bash
  uvicorn agrisense_app.backend.main:app --host 0.0.0.0 --port 8004
  ```
- Run frontend (built) served at `/ui`.
- Farmers connect to Pi hotspot → `http://192.168.x.x:8004/ui`.

### 2. Azure Cloud (Optional)
- Use existing `infra/bicep/` setup.
- Sync Pi → cloud DB periodically.

---

## 📂 Demo Flow (For Judges)

1. Show **soil pot + tank + ESP32 valve** setup.  
2. Dry soil → ESP32 reads low moisture → backend `/recommend`.  
3. Backend recommends irrigation → MQTT command → valve ON → water flows.  
4. Tank level decreases (live gauge update).  
5. Farmer dashboard/mobile app updates → SMS alert sent.  
6. Impact metrics shown (liters + ₹ saved).

---

## ✅ Summary

With these upgrades, AgroSmart will:
- Address **Sikkim-specific challenges**.  
- Provide **live IoT + ML demo**.  
- Impress judges with **real hardware + farmer UI + impact metrics**.  
- Be **scalable** and **cloud-ready** for future deployment.  
