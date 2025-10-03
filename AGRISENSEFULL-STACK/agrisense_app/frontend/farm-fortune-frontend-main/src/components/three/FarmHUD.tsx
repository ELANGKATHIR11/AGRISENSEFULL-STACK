import React from "react";
import { Button } from "@/components/ui/button";

type Props = { onIrrigate?: () => void; onToggleDevice?: (id: string) => void };

const FarmHUD: React.FC<Props> = ({ onIrrigate, onToggleDevice }) => {
  return (
    <div className="absolute right-6 top-6 flex flex-col gap-3 z-50">
      <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white" onClick={onIrrigate}>Simulate Irrigation</Button>
      <Button size="sm" variant="outline" onClick={() => onToggleDevice?.("valve-1")}>Toggle Valve</Button>
    </div>
  );
};

export default FarmHUD;
