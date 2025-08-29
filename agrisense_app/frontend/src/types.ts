export type Recommendation = {
  zone_id?: string
  plant: string
  soil_type: string
  area_m2: number
  ph: number
  moisture_pct: number
  temperature_c: number
  ec_dS_m: number
  // fertilizer outputs
  fert_n_g: number
  fert_p_g: number
  fert_k_g: number
  // outputs (subset)
  water_liters?: number
  water_per_m2_l?: number
  water_buckets_15l?: number
  suggested_runtime_min?: number
  irrigation_cycles?: number
  assumed_flow_lpm?: number
  fertilizer_equivalents?: Record<string, number | string>
  best_time?: string
  target_moisture_pct?: number
  expected_savings_liters?: number
  expected_cost_saving_rs?: number
  expected_co2e_kg?: number
  notes?: string[]
}

export type SensorReading = Omit<
  Recommendation,
  | 'water_liters'
  | 'water_per_m2_l'
  | 'water_buckets_15l'
  | 'suggested_runtime_min'
  | 'irrigation_cycles'
  | 'assumed_flow_lpm'
  | 'fertilizer_equivalents'
  | 'best_time'
  | 'target_moisture_pct'
  | 'expected_savings_liters'
  | 'expected_cost_saving_rs'
  | 'expected_co2e_kg'
  | 'fert_n_g'
  | 'fert_p_g'
  | 'fert_k_g'
  | 'notes'
> & {
  // Optional soil nutrient readings in ppm
  n_ppm?: number
  p_ppm?: number
  k_ppm?: number
}
