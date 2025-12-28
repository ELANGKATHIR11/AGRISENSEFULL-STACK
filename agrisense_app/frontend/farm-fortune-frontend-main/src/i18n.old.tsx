import React, { createContext, useContext, useMemo, useState, useEffect } from "react";

type Locale = "en" | "ne";

type Dict = Record<string, string>;

const en: Dict = {
  app_title: "AgriSense",
  app_tagline: "Smart Farming Platform",
  nav_home: "Home",
  nav_recommend: "Recommend",
  nav_soil: "Soil Analysis",
  nav_crops: "Crops",
  nav_disease: "Disease Management",
  nav_weed: "Weed Management",
  nav_live: "Live",
  nav_irrigation: "Irrigation",
  nav_harvesting: "Harvesting",
  nav_impact: "Impact",
  nav_admin: "Admin",
  nav_chat: "Chat",

  dashboard: "Dashboard",
  refresh: "Refresh",
  start_irrigation_10m: "Start irrigation 10 min",
  stop_irrigation: "Stop irrigation",
  tank: "Tank",
  tank_level: "Level",
  tank_volume: "Volume",
  tank_updated: "Updated",
  zone: "Zone",
  duration_seconds: "Duration (s)",
  quick: "Quick",
  start: "Start",
  stop: "Stop",
  force_start: "Force Start",
  status: "Status",
  running: "Running",
  idle: "Idle",
  weather: "Weather",
  soil_moisture: "Soil Moisture",
  temp: "Temperature",
  ec: "EC",
  alerts: "Alerts",
  acknowledge: "Acknowledge",
  acknowledged: "Acknowledged",
  show_acknowledged: "Show acknowledged",
  all_clear: "All clear",
  no_data: "No data",
  no_weather: "No weather yet",
  updated: "Updated",
  low_level: "Low level",
  moderate: "Moderate",
  healthy: "Healthy",
  impact_metrics: "Impact metrics",
  saved_water_l: "Saved water (L)",
  cost_saving_rs: "Cost saving (Rs)",
  co2e_kg: "CO2e (kg)",
  rainwater: "Rainwater",
  collected_total: "Collected",
  used_total: "Used",
  net_balance: "Net",
  log_entry: "Log Entry",
  collected_liters: "Collected (L)",
  used_liters: "Used (L)",
  add: "Add",

  // Crops page
  crops_browse_subtitle: "Browse our comprehensive crop library with growing requirements and tips",
  search_crops_placeholder: "Search crops by name or scientific name...",
  all_crops: "All Crops",
  showing_n_of_m: "Showing {n} of {m} crops",
  water_label: "Water",
  season: "Season",
  temp_short: "Temp",
  ph_short: "pH",
  growth_period: "Growth Period",
  growing_tips: "Growing Tips:",
  no_crops_found: "No crops found",
  try_adjusting_search: "Try adjusting your search terms or category filter",

  // Irrigation page
  recent_valve_events: "Recent valve events",
  no_events: "No events",

  // Recommend page
  water_source: "Water source",
  notes: "Notes",
  smart_recommendations: "Smart Recommendations",

  // LiveStats
  live_farm_stats: "Live Farm Stats",
  edge_label: "Edge",
  connected: "connected",
  unavailable: "unavailable",
  capture_now: "Capture now",
  capturing: "Capturing…",
  zone_label: "Zone",
  moisture_pct: "Moisture %",
  soil_ph: "Soil pH",
  temperature_c: "Temperature °C",
  ec_ds_m: "EC dS/m",
  available: "available",
  not_detected: "not detected",

  // ImpactGraphs
  impact_over_time: "Impact Over Time",
  water_savings_l: "Water Savings (L)",
  water_applied_l: "Water Applied (L)",
  fertilizer_total_g: "Fertilizer Total (g)",
  yield_potential: "Yield Potential",
  no_reco_snapshots: "No recommendation snapshots yet. They’ll appear after calling Recommend or by posting to /reco/log.",

  // Admin
  system_administration: "System Administration",
  monitor_and_manage: "Monitor and manage AgriSense system components",
  overview: "Overview",
  ml_models: "ML Models",
  system: "System",
  activity: "Activity",
  quick_actions: "Quick Actions",
  common_admin_tasks: "Common administrative tasks",
  reload_models: "Reload Models",
  reload_dataset: "Reload Dataset",
  view_logs: "View Logs",
  config: "Config",
  erase_all_data: "Erase All Data",
  system_health: "System Health",
  configuration: "Configuration",
  recent_activity: "Recent Activity",
  system_events_actions: "System events and administrative actions",
  models_reloaded: "Models Reloaded",
  models_reload_done: "All ML models have been successfully reloaded.",
  dataset_reloaded: "Dataset Reloaded",
  dataset_reload_done: "Enhanced agricultural dataset has been refreshed.",
  confirm_erase_all: "This will erase ALL stored data (readings, tank levels, events, alerts). Continue?",
  all_data_erased: "All data erased",
  storage_reset_done: "Storage reset completed.",
  reset_failed: "Reset failed",

  // Rainwater
  recent_entries: "Recent entries",

  // Recommend page
  sensor_data_input: "Sensor Data Input",
  enter_readings: "Enter current readings from your field sensors",
  environmental_conditions: "Environmental Conditions",
  temperature_c_label: "Temperature (°C)",
  humidity_pct: "Humidity (%)",
  soil_analysis: "Soil Analysis",
  soil_moisture_pct: "Soil Moisture (%)",
  ph_level: "pH Level",
  nutrient_levels_ppm: "Nutrient Levels (ppm)",
  nitrogen_n: "Nitrogen (N)",
  phosphorus_p: "Phosphorus (P)",
  potassium_k: "Potassium (K)",
  soil_type: "Soil Type",
  select_soil_type: "Select soil type",
  area_m2: "Area (m²)",
  warn_ph_range: "pH must be between 3.5 and 9.5",
  warn_moisture_range: "Moisture must be between 0 and 100%",
  warn_temp_range: "Temperature must be between -10 and 60°C",
  warn_area_positive: "Area must be greater than 0",
  crop_type: "Crop Type",
  select_crop_type: "Select crop type",
  analyzing: "Analyzing...",
  generate_recommendations: "Generate Recommendations",
  ai_insights: "AI-powered insights for optimal crop management",
  enter_sensor_prompt: "Enter sensor data to receive personalized recommendations",
  irrigation_fertilizer_plan: "Irrigation & Fertilizer Plan",
  water_liters_total: "Water (liters total)",
  irrigation_cycles: "Irrigation cycles",
  runtime_min: "Runtime (min)",
  best_time: "Best time",
  impact: "Impact",
  water_saved_l: "Water saved (L)",
  cost_saved_rs2: "Cost saved (Rs)",
  co2e_kg2: "CO2e (kg)",
  fertilizer_equivalents: "Fertilizer equivalents",
  detailed_tips: "Detailed Tips",
};

const ne: Dict = {
  app_title: "एग्रिसेन्स",
  app_tagline: "स्मार्ट खेती प्लेटफर्म",
  nav_home: "होम",
  nav_recommend: "सिफारिस",
  nav_soil: "माटो विश्लेषण",
  nav_crops: "बाली",
  nav_disease: "रोग व्यवस्थापन",
  nav_weed: "झार व्यवस्थापन",
  nav_live: "लाइभ",
  nav_irrigation: "सिँचाइ",
  nav_harvesting: "कटनी",
  nav_impact: "प्रभाव",
  nav_admin: "एडमिन",
  nav_chat: "च्याट",

  dashboard: "ड्यासबोर्ड",
  refresh: "रिफ्रेस",
  start_irrigation_10m: "१० मिनेट सिँचाइ सुरु",
  stop_irrigation: "सिँचाइ रोक्ने",
  tank: "ट्यांकी",
  tank_level: "स्तर",
  tank_volume: "परिमाण",
  tank_updated: "अद्यावधिक",
  zone: "क्षेत्र",
  duration_seconds: "अवधि (सेकेन्ड)",
  quick: "छिटो",
  start: "सुरु",
  stop: "रोक",
  force_start: "बलपूर्वक सुरु",
  status: "स्थिति",
  running: "चलिरहेको",
  idle: "निष्क्रिय",
  weather: "मौसम",
  soil_moisture: "माटो चिस्यान",
  temp: "तापक्रम",
  ec: "ईसी",
  alerts: "चेतावनी",
  acknowledge: "स्वीकार",
  acknowledged: "स्वीकृत",
  show_acknowledged: "स्वीकृत देखाउनुहोस्",
  all_clear: "सबै ठिक",
  no_data: "डाटा छैन",
  no_weather: "अहिले मौसम छैन",
  updated: "अद्यावधिक",
  low_level: "कम स्तर",
  moderate: "मध्यम",
  healthy: "स्वस्थ",
  impact_metrics: "प्रभाव मेट्रिक्स",
  saved_water_l: "बचत पानी (लिटर)",
  cost_saving_rs: "लागत बचत (रु)",
  co2e_kg: "CO2e (किलो)",
  rainwater: "वर्षा पानी",
  collected_total: "सङ्कलन",
  used_total: "प्रयोग",
  net_balance: "नेट",
  log_entry: "दर्ता गर्नुहोस्",
  collected_liters: "सङ्कलित (लिटर)",
  used_liters: "प्रयोग (लिटर)",
  add: "थप्नुहोस्",

  // Crops page
  crops_browse_subtitle: "बढ्ने आवश्यकताहरु र सुझावसँग हाम्रो बाली पुस्तकालय ब्राउज गर्नुहोस्",
  search_crops_placeholder: "बाली नाम वा वैज्ञानिक नामले खोज्नुहोस्...",
  all_crops: "सबै बाली",
  showing_n_of_m: "{m} मध्ये {n} बाली देखाइँदै",
  water_label: "पानी",
  season: "मौसम",
  temp_short: "तापक्रम",
  ph_short: "pH",
  growth_period: "विकास अवधि",
  growing_tips: "खेती गर्ने सुझाव:",
  no_crops_found: "कुनै बाली फेला परेन",
  try_adjusting_search: "कृपया खोज शब्द वा वर्ग छनोट परिवर्तन गर्नुहोस्",

  // Irrigation page
  recent_valve_events: "भल्भका पछिल्ला गतिविधि",
  no_events: "घटना छैन",

  // Recommend page
  water_source: "पानीको स्रोत",
  notes: "टिप्पणी",
  smart_recommendations: "स्मार्ट सिफारिस",

  // LiveStats
  live_farm_stats: "लाइभ फार्म तथ्यांक",
  edge_label: "एज",
  connected: "जोडिएको",
  unavailable: "उपलब्ध छैन",
  capture_now: "अहिले क्याप्चर",
  capturing: "क्याप्चर हुँदै…",
  zone_label: "क्षेत्र",
  moisture_pct: "चिस्यान %",
  soil_ph: "माटो pH",
  temperature_c: "तापक्रम °C",
  ec_ds_m: "EC dS/m",
  available: "उपलब्ध",
  not_detected: "पत्ता लागेन",

  // ImpactGraphs
  impact_over_time: "समयसँगको प्रभाव",
  water_savings_l: "पानी बचत (L)",
  water_applied_l: "प्रयोग गरिएको पानी (L)",
  fertilizer_total_g: "मल कुल (g)",
  yield_potential: "उत्पादन सम्भावना",
  no_reco_snapshots: "अझै सिफारिस स्न्यापशट छैन। Recommend चलाएपछि वा /reco/log मा पोस्ट गरेपछि देखिन्छ।",

  // Admin
  system_administration: "प्रणाली प्रशासन",
  monitor_and_manage: "एग्रिसेन्स प्रणाली व्यवस्थापन र निगरानी गर्नुहोस्",
  overview: "अवलोकन",
  ml_models: "ML मोडेल",
  system: "प्रणाली",
  activity: "गतिविधि",
  quick_actions: "छिटो कार्य",
  common_admin_tasks: "सामान्य प्रशासनिक कार्य",
  reload_models: "मोडेल रीलोड",
  reload_dataset: "डेटासेट रीलोड",
  view_logs: "लग्स हेर्नुहोस्",
  config: "कन्फिग",
  erase_all_data: "सबै डाटा मेटाउनुहोस्",
  system_health: "प्रणाली स्वास्थ्य",
  configuration: "कन्फिगरेसन",
  recent_activity: "हालको गतिविधि",
  system_events_actions: "प्रणाली घटनाहरू र प्रशासनिक कार्यहरू",
  models_reloaded: "मोडेल रीलोड गरियो",
  models_reload_done: "सबै ML मोडेल सफलतापूर्वक रीलोड भयो।",
  dataset_reloaded: "डेटासेट रीलोड गरियो",
  dataset_reload_done: "कृषि डाटासेट ताजा गरियो।",
  confirm_erase_all: "यसले सबै डाटा (पढाइ, ट्यांकी, इभेन्ट, अलर्ट) मेटाउँछ। जारी राख्ने?",
  all_data_erased: "सबै डाटा मेटियो",
  storage_reset_done: "स्टोरेज रिसेट पूरा भयो।",
  reset_failed: "रिसेट असफल",

  // Rainwater
  recent_entries: "हालका प्रविष्टिहरू",

  // Recommend page
  sensor_data_input: "सेन्सर डाटा इनपुट",
  enter_readings: "फिल्ड सेन्सरबाट अहिलेको रिडिङ प्रविष्ट गर्नुहोस्",
  environmental_conditions: "वातावरणीय अवस्था",
  temperature_c_label: "तापक्रम (°C)",
  humidity_pct: "आर्द्रता (%)",
  soil_analysis: "माटो विश्लेषण",
  soil_moisture_pct: "माटो चिस्यान (%)",
  ph_level: "pH स्तर",
  nutrient_levels_ppm: "पोषक तत्व स्तर (ppm)",
  nitrogen_n: "नाइट्रोजन (N)",
  phosphorus_p: "फस्फोरस (P)",
  potassium_k: "पोटासियम (K)",
  soil_type: "माटोको प्रकार",
  select_soil_type: "माटोको प्रकार चयन",
  area_m2: "क्षेत्रफल (m²)",
  warn_ph_range: "pH 3.5 देखि 9.5 बीच हुनुपर्छ",
  warn_moisture_range: "चिस्यान 0 देखि 100% बीच हुनुपर्छ",
  warn_temp_range: "तापक्रम -10 देखि 60°C बीच हुनुपर्छ",
  warn_area_positive: "क्षेत्रफल 0 भन्दा ठूलो हुनुपर्छ",
  crop_type: "बाली प्रकार",
  select_crop_type: "बाली चयन गर्नुहोस्",
  analyzing: "विश्लेषण हुँदै...",
  generate_recommendations: "सिफारिसहरू बनाउनुहोस्",
  ai_insights: "उत्तम बाली व्यवस्थापनका लागि AI सिफारिस",
  enter_sensor_prompt: "व्यक्तिगत सिफारिसको लागि सेन्सर डाटा प्रविष्ट गर्नुहोस्",
  irrigation_fertilizer_plan: "सिँचाइ र मल योजना",
  water_liters_total: "पानी (कुल लिटर)",
  irrigation_cycles: "सिँचाइ चक्र",
  runtime_min: "रनटाइम (मिन)",
  best_time: "उत्तम समय",
  impact: "प्रभाव",
  water_saved_l: "बचत गरिएको पानी (L)",
  cost_saved_rs2: "बचत लागत (Rs)",
  co2e_kg2: "CO2e (kg)",
  fertilizer_equivalents: "मल समतुल्य",
  detailed_tips: "विस्तृत सुझाव",
};

const tables: Record<Locale, Dict> = { en, ne };

type I18nContextValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocale] = useState<Locale>(() => (localStorage.getItem("locale") as Locale) || "en");

  useEffect(() => {
    localStorage.setItem("locale", locale);
  }, [locale]);

  const t = useMemo(() => {
    const dict = tables[locale] || tables.en;
    return (key: string) => dict[key] || tables.en[key] || key;
  }, [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}

export function LanguageToggle() {
  const { locale, setLocale } = useI18n();
  const next = locale === "en" ? "ne" : "en";
  return (
    <button
      type="button"
      onClick={() => setLocale(next)}
      className="text-sm px-3 py-1 rounded-md border hover:bg-secondary text-foreground"
      title={locale === "en" ? "Switch to Nepali" : "Switch to English"}
    >
      {locale === "en" ? "ने" : "EN"}
    </button>
  );
}
