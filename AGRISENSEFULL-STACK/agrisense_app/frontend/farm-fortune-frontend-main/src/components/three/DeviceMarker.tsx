import React from "react";
import { Html } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import type * as THREE from "three";

type Props = { position: [number, number, number]; name: string; status?: "online" | "offline"; onClick?: () => void };

const DeviceMarker: React.FC<Props> = ({ position, name, status = "online", onClick }) => {
  const ref = React.useRef<THREE.Mesh | null>(null);
  // simple bobbing animation
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.position.y = position[1] + 0.05 * Math.sin(clock.getElapsedTime() * 2);
    }
  });

  return (
    <group position={position}>
      <mesh ref={ref} onClick={() => onClick?.()}>
        <boxGeometry args={[0.25, 0.25, 0.25]} />
        <meshStandardMaterial color={status === "online" ? "#10B981" : "#EF4444"} />
      </mesh>
      <Html distanceFactor={8} position={[0, 0.6, 0]}>
        <div className="bg-white/90 text-xs text-gray-800 px-2 py-1 rounded shadow">{name} <span className="ml-2 font-medium">{status}</span></div>
      </Html>
    </group>
  );
};

export default DeviceMarker;
