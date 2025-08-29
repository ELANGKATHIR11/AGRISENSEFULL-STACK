import React from 'react'
import { motion } from 'framer-motion'
import type { Recommendation } from '../types'

type Props = {
  data: Recommendation | null
}

export default function Results({ data }: Props) {
  if (!data) return null
  const eq = data.fertilizer_equivalents || {}
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="card p-4 md:p-6">
      <h2 className="section-title mb-4">Recommendation</h2>
  <div className="grid md:grid-cols-3 gap-4">
        <motion.div whileHover={{ y: -2 }} className="rounded-2xl p-3 ring-1 ring-emerald-100 bg-emerald-50/60">
          <div className="text-sm text-emerald-700">Total Water</div>
          <div className="text-2xl font-semibold text-emerald-900">{Math.round((data.water_liters || 0))} L</div>
          <div className="text-xs text-emerald-700">{(data.water_per_m2_l || 0).toFixed(2)} L/m²</div>
        </motion.div>
        <motion.div whileHover={{ y: -2 }} className="rounded-2xl p-3 ring-1 ring-sky-100 bg-sky-50/60">
          <div className="text-sm text-sky-700">Runtime</div>
          <div className="text-2xl font-semibold text-sky-900">{(data.suggested_runtime_min || 0).toFixed(1)} min</div>
          <div className="text-xs text-sky-700">{data.irrigation_cycles || 1} cycle(s) • {data.assumed_flow_lpm || 0} L/min</div>
        </motion.div>
        <motion.div whileHover={{ y: -2 }} className="rounded-2xl p-3 ring-1 ring-amber-100 bg-amber-50/60">
          <div className="text-sm text-amber-700">Buckets</div>
          <div className="text-2xl font-semibold text-amber-900">{Math.round(data.water_buckets_15l || 0)}</div>
          <div className="text-xs text-amber-700">15 L each</div>
        </motion.div>
      </div>
      <div className="mt-5 grid md:grid-cols-2 gap-4">
        <div className="card p-3">
          <div className="font-medium mb-2">N-P-K nutrients</div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="rounded-xl p-2 ring-1 ring-green-100 bg-green-50/60">
              <div className="text-xs text-green-700">Nitrogen</div>
              <div className="text-lg font-semibold text-green-900">{(data.fert_n_g || 0).toFixed(1)} g</div>
            </div>
            <div className="rounded-xl p-2 ring-1 ring-blue-100 bg-blue-50/60">
              <div className="text-xs text-blue-700">Phosphorus</div>
              <div className="text-lg font-semibold text-blue-900">{(data.fert_p_g || 0).toFixed(1)} g</div>
            </div>
            <div className="rounded-xl p-2 ring-1 ring-amber-100 bg-amber-50/60">
              <div className="text-xs text-amber-700">Potassium</div>
              <div className="text-lg font-semibold text-amber-900">{(data.fert_k_g || 0).toFixed(1)} g</div>
            </div>
          </div>
          <div className="text-xs text-gray-600 mt-2">Apply in 2–3 splits around irrigation; always follow local agronomy advice.</div>
        </div>
        <div className="card p-3">
          <div className="font-medium mb-2">Fertilizer equivalents</div>
          <ul className="list-disc list-inside text-sm text-gray-700">
            {'urea_g' in eq && <li><span className="font-medium">Urea</span>: {eq['urea_g']} g</li>}
            {'dap_g' in eq && <li><span className="font-medium">DAP</span>: {eq['dap_g']} g (includes {eq['n_from_dap_g']} g N)</li>}
            {'mop_g' in eq && <li><span className="font-medium">MOP</span>: {eq['mop_g']} g</li>}
          </ul>
          <div className="text-xs text-gray-600 mt-2">Split applications are recommended; avoid fertilizing during midday heat and water lightly after application.</div>
        </div>
        <div className="card p-3 md:col-span-2">
          <div className="font-medium mb-1">Tips</div>
          <ul className="list-disc list-inside text-sm text-gray-700">
            {data.best_time && <li>Best time to irrigate: {data.best_time}</li>}
            {typeof data.target_moisture_pct === 'number' && <li>Target soil moisture: {data.target_moisture_pct}%</li>}
            {data.notes?.map((n, i) => <li key={i}>{n}</li>)}
          </ul>
        </div>
      </div>
    </motion.div>
  )
}
