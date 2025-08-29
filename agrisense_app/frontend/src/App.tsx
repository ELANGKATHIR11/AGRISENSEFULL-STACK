import React, { useState } from 'react'
import { motion } from 'framer-motion'
import Form from './components/Form'
import Results from './components/Results'
import type { Recommendation, SensorReading } from './types'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<Recommendation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [soilRecoLoading, setSoilRecoLoading] = useState(false)
  const [soilReco, setSoilReco] = useState<any[] | null>(null)
  const [soilInput, setSoilInput] = useState('loam')

  async function getReco(reading: SensorReading) {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reading)
      })
      if (!res.ok) throw new Error(`API ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch recommendation')
    } finally {
      setLoading(false)
    }
  }

  async function getCropsForSoil(soil: string) {
    setSoilRecoLoading(true)
    setSoilReco(null)
    try {
      const res = await fetch('/suggest_crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ soil_type: soil })
      })
      if (!res.ok) throw new Error(`API ${res.status}`)
      const json = await res.json()
      setSoilReco(json.top || [])
    } catch (e: any) {
      setSoilReco([])
    } finally {
      setSoilRecoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-white">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="max-w-5xl mx-auto p-4">
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold tracking-tight">Agri-Sense</h1>
            <div className="subtle">Backend: <span className="font-mono">/recommend</span></div>
          </div>
          <p className="subtle mt-1">A Smart Agriculture Solution for Sustainable Farming</p>
        </header>

        <motion.div layout className="card p-4 md:p-6">
          <h2 className="section-title mb-4">Enter field & sensor details</h2>
          <Form onSubmit={getReco} loading={loading} />
        </motion.div>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">
            {error}
          </motion.div>
        )}

        <motion.div layout className="mt-6">
          <Results data={data} />
        </motion.div>

        <motion.div layout className="mt-6 card p-4 md:p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="section-title">Which crop suits my soil?</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-[1fr_auto]">
            <input value={soilInput} onChange={e=>setSoilInput(e.target.value)} className="border border-gray-200 bg-white/70 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-300" placeholder="e.g., loam, clay, sandy loam" />
            <motion.button whileTap={{ scale: 0.98 }} whileHover={{ y: -1 }} disabled={soilRecoLoading} onClick={()=>getCropsForSoil(soilInput)} className="btn-primary">{soilRecoLoading ? 'Finding…' : 'Suggest crops'}</motion.button>
          </div>

          {soilReco && (
            <div className="mt-4 grid md:grid-cols-2 gap-3">
              {soilReco.map((r:any, i:number) => (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl p-3 ring-1 ring-gray-200 bg-white/70">
                  <div className="font-medium">{r.crop}</div>
                  <div className="text-sm text-gray-600">Suitability: {(r.suitability_score*100).toFixed(0)}%</div>
                  <div className="text-sm text-gray-600">Yield: {r.expected_yield} t/ha</div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>

        {data && (
          <motion.details layout className="mt-6 card p-3">
            <summary className="cursor-pointer select-none">Raw JSON</summary>
            <pre className="text-xs overflow-auto mt-2">{JSON.stringify(data, null, 2)}</pre>
          </motion.details>
        )}
      </motion.div>
    </div>
  )
}
