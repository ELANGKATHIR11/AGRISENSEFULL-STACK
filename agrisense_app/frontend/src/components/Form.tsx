import React, { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import type { SensorReading } from '../types'

type Props = {
  onSubmit: (reading: SensorReading) => void
  loading: boolean
}

type PlantOption = { value: string; label: string }
const FALLBACK_PLANTS: PlantOption[] = [
  { value: 'generic', label: 'Generic' },
  { value: 'rice', label: 'Rice' },
  { value: 'wheat', label: 'Wheat' },
  { value: 'maize', label: 'Maize' },
  { value: 'tomato', label: 'Tomato' },
]
const SOILS = ['loam', 'clay', 'sandy']

export default function Form({ onSubmit, loading }: Props) {
  const [plants, setPlants] = useState<PlantOption[]>(FALLBACK_PLANTS)
  const [plantSearch, setPlantSearch] = useState('')
  const [plant, setPlant] = useState('generic')
  const [soil, setSoil] = useState('loam')
  const [area, setArea] = useState(100)
  const [ph, setPh] = useState(6.5)
  const [moisture, setMoisture] = useState(35)
  const [temp, setTemp] = useState(28)
  const [ec, setEc] = useState(1.0)
  const [n, setN] = useState<number | ''>('')
  const [p, setP] = useState<number | ''>('')
  const [k, setK] = useState<number | ''>('')

  const reading = useMemo<SensorReading>(() => ({
    plant,
    soil_type: soil,
    area_m2: area,
    ph,
    moisture_pct: moisture,
    temperature_c: temp,
    ec_dS_m: ec,
    ...(n !== '' ? { n_ppm: Number(n) } : {}),
    ...(p !== '' ? { p_ppm: Number(p) } : {}),
    ...(k !== '' ? { k_ppm: Number(k) } : {}),
  }), [plant, soil, area, ph, moisture, temp, ec, n, p, k])

  const filteredPlants = useMemo(() => {
    const q = plantSearch.trim().toLowerCase()
    if (!q) return plants
    return plants.filter(p => p.label.toLowerCase().includes(q) || p.value.toLowerCase().includes(q))
  }, [plants, plantSearch])

  useEffect(() => {
    let ignore = false
    ;(async () => {
      try {
        const r = await fetch('/plants')
        if (!r.ok) return
        const j = await r.json()
        if (!ignore && Array.isArray(j?.items) && j.items.length) {
          setPlants(j.items as PlantOption[])
          // If current plant not in list, reset to first or generic
          const has = (j.items as PlantOption[]).some(p => p.value === plant)
          if (!has) setPlant('generic')
        }
      } catch {}
    })()
    return () => { ignore = true }
  }, [])

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit(reading)
      }}
      className="grid gap-4 md:grid-cols-2"
    >
      <div className="card p-4 md:p-5">
        <h2 className="section-title mb-3">Crop & Soil</h2>
        <div className="grid gap-3">
          <label className="grid gap-1">
            <span className="subtle">Search crop</span>
            <input className="input" placeholder="Type to filter (e.g., rice, wheat, tomato)" value={plantSearch} onChange={e=>setPlantSearch(e.target.value)} />
          </label>
          <label className="grid gap-1">
            <span className="subtle">Plant</span>
            <select className="input" value={plant} onChange={e=>setPlant(e.target.value)}>
              {filteredPlants.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </label>
          <label className="grid gap-1">
            <span className="subtle">Soil Type</span>
            <select className="input" value={soil} onChange={e=>setSoil(e.target.value)}>
              {SOILS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="grid gap-1">
            <span className="subtle flex items-center gap-2">Area <span className="badge">m²</span></span>
            <input type="number" min={1} className="input" value={area} onChange={e=>setArea(parseFloat(e.target.value))} />
          </label>
        </div>
      </div>
      <div className="card p-4 md:p-5">
        <h2 className="section-title mb-3">Readings</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="grid gap-1">
            <span className="subtle">pH</span>
            <input type="number" step="0.1" className="input" value={ph} onChange={e=>setPh(parseFloat(e.target.value))} />
          </label>
          <label className="grid gap-1">
            <span className="subtle flex items-center gap-2">Moisture <span className="badge">%</span></span>
            <input type="number" step="1" className="input" value={moisture} onChange={e=>setMoisture(parseFloat(e.target.value))} />
          </label>
          <label className="grid gap-1">
            <span className="subtle flex items-center gap-2">Temperature <span className="badge">°C</span></span>
            <input type="number" step="0.1" className="input" value={temp} onChange={e=>setTemp(parseFloat(e.target.value))} />
          </label>
          <label className="grid gap-1">
            <span className="subtle flex items-center gap-2">Electrical Conductivity <span className="badge">dS/m</span></span>
            <input type="number" step="0.1" className="input" value={ec} onChange={e=>setEc(parseFloat(e.target.value))} />
          </label>
          <div className="md:col-span-2 mt-2">
            <div className="text-sm font-medium mb-1">Soil nutrients <span className="badge">ppm</span></div>
            <div className="grid gap-3 md:grid-cols-3">
              <label className="grid gap-1">
                <span className="subtle">Nitrogen (N)</span>
                <input type="number" min={0} className="input" value={n} onChange={e=>setN(e.target.value === '' ? '' : Number(e.target.value))} placeholder="e.g. 20" />
              </label>
              <label className="grid gap-1">
                <span className="subtle">Phosphorus (P)</span>
                <input type="number" min={0} className="input" value={p} onChange={e=>setP(e.target.value === '' ? '' : Number(e.target.value))} placeholder="e.g. 15" />
              </label>
              <label className="grid gap-1">
                <span className="subtle">Potassium (K)</span>
                <input type="number" min={0} className="input" value={k} onChange={e=>setK(e.target.value === '' ? '' : Number(e.target.value))} placeholder="e.g. 25" />
              </label>
            </div>
            <div className="text-xs text-gray-600 mt-1">Leave blank to auto-estimate from crop and soil.</div>
          </div>
        </div>
      </div>
      <div className="md:col-span-2 flex gap-3 justify-end">
        <motion.button whileTap={{ scale: 0.98 }} whileHover={{ y: -1 }} disabled={loading} className="btn-primary disabled:opacity-60">
          {loading ? 'Calculating…' : 'Get Recommendation'}
        </motion.button>
      </div>
    </form>
  )
}
