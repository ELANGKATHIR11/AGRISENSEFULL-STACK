import React, { useState, useCallback } from "react";
import FarmScene from "./FarmScene";
import FarmHUD from "./FarmHUD";

const initialDevices = [
  { id: "sensor-a", position: [2, 0.4, 2] as [number, number, number], name: "Soil Sensor A", status: "online" as const },
  { id: "valve-1", position: [-2, 0.4, -1.5] as [number, number, number], name: "Irrigation Valve", status: "offline" as const },
];

const Farm3DContainer: React.FC = () => {
  const [devices, setDevices] = useState(initialDevices);

  const toggleDevice = useCallback((id: string) => {
    setDevices((d) => d.map((x) => (x.id === id ? { ...x, status: x.status === "online" ? "offline" : "online" } : x)));
  }, []);

  const simulateIrrigation = useCallback(() => {
    // Demo: briefly set valve online then offline
    setDevices((d) => d.map((x) => (x.id === "valve-1" ? { ...x, status: "online" } : x)));
    setTimeout(() => toggleDevice("valve-1"), 3000);
  }, [toggleDevice]);

  return (
    <div className="relative">
      <FarmScene devices={devices} onToggleDevice={toggleDevice} />
      <FarmHUD onIrrigate={simulateIrrigation} onToggleDevice={toggleDevice} />
    </div>
  );
};

export default Farm3DContainer;
