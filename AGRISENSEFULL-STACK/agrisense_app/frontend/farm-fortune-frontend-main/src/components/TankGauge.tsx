import React from "react";

export function TankGauge({ percent = 0, liters }: { percent?: number | null; liters?: number | null }) {
  const p = Math.max(0, Math.min(100, Number(percent ?? 0)));
  const circumference = 2 * Math.PI * 45; // r=45
  const offset = circumference * (1 - p / 100);
  // Dynamic color by level: <30 red, 30-59 amber, 60+ green
  const color = p < 30 ? "#ef4444" : p < 60 ? "#f59e0b" : "#10b981";
  return (
    <div className="flex items-center gap-4">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r="45"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <text x="60" y="58" textAnchor="middle" fontSize="18" fontWeight="600" fill="#111827">{Math.round(p)}%</text>
        <text x="60" y="78" textAnchor="middle" fontSize="10" fill="#6b7280">{liters != null ? `${Math.round(liters)} L` : ""}</text>
      </svg>
    </div>
  );
}

export default TankGauge;
