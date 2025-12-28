import React, { useState } from "react";
import cropApi from "../lib/cropApi";

type DetectionResult = {
  label: string;
  confidence?: number;
  notes?: string[];
};

export default function CropDetector() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<DetectionResult[] | null>(null);
  const [mode, setMode] = useState<"disease" | "weed">("disease");
  const [cropType, setCropType] = useState<string>("");
  const [growthStage, setGrowthStage] = useState<string | undefined>(undefined);

  const toBase64 = (f: File) =>
    new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve((reader.result || "") as string);
      reader.onerror = reject;
      reader.readAsDataURL(f);
    });

  const onSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setError(null);
    setResults(null);
    if (!file) return setError("Please choose an image file first.");
    setLoading(true);
    try {
      const dataUrl = await toBase64(file);
      // strip data URL prefix to send compact base64 payload
      const match = dataUrl.match(/^data:.*;base64,(.*)$/);
      const payload: { image_data: string; crop_type?: string; field_info?: Record<string, unknown> } = {
        image_data: match ? match[1] : dataUrl,
        crop_type: cropType || undefined,
        field_info: { growth_stage: growthStage || undefined },
      };

      // Use unified frontend adapter endpoint via cropApi
  const w = window as unknown as { __API_BASE__?: string };
  const apiBase = w.__API_BASE__ || "";
      const res = await fetch(`${apiBase}/api/frontend/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode, ...payload }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
      const json = await res.json();

      const out: DetectionResult[] = [];
      if (json.type === "disease") {
        out.push({ label: json.primary_disease || "unknown", confidence: json.confidence, notes: json.prevention_tips || [] });
      } else if (json.type === "weed") {
        out.push({ label: `Weed coverage ${json.weed_coverage_percentage}%`, confidence: json.weed_pressure === "high" ? 0.9 : 0.5, notes: json.management_plan ? [JSON.stringify(json.management_plan)] : [] });
      } else {
        out.push({ label: JSON.stringify(json) });
      }
      setResults(out);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="crop-detector card p-4">
      <h3 className="text-lg font-medium mb-2">Crop Disease & Weed Detector</h3>
      <form onSubmit={onSubmit}>
        <div className="mb-2">
          <label className="mr-2">Mode:</label>
          <select value={mode} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setMode(e.target.value as "disease" | "weed") }>
            <option value="disease">Disease</option>
            <option value="weed">Weed</option>
          </select>
        </div>
        <div className="mb-2">
          <input type="text" placeholder="Crop type (e.g. tomato)" value={cropType} onChange={(e) => setCropType(e.target.value)} className="input" />
        </div>
        <div className="mb-2">
          <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <div className="mb-2">
          <button type="submit" className="btn" disabled={loading}>
            {loading ? "Analyzing…" : "Analyze"}
          </button>
        </div>
      </form>

      {error && <div className="text-red-600">{error}</div>}

      {results && (
        <div className="mt-3">
          <h4 className="font-semibold">Results</h4>
          <ul>
            {results.map((r, i) => (
              <li key={i} className="mb-2">
                <div className="font-medium">{r.label}</div>
                {r.confidence !== undefined && <div>Confidence: {(r.confidence * 100).toFixed(1)}%</div>}
                {r.notes && r.notes.length > 0 && (
                  <ul className="text-sm list-disc ml-5">
                    {r.notes.map((n, j) => (
                      <li key={j}>{n}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
