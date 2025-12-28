import React, { Suspense, useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars, Sky, Html } from "@react-three/drei";
import DeviceMarker from "./DeviceMarker";
import useWeather3d from "@/hooks/useWeather3d";

type Device = { id: string; position: [number, number, number]; name: string; status: "online" | "offline" };

type Props = {
  devices?: Device[];
  onToggleDevice?: (id: string) => void;
};

const FarmGround = () => (
  <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
    <planeGeometry args={[60, 60]} />
    <meshStandardMaterial color="#6BBF59" />
  </mesh>
);

const SimpleBarn = ({ position = [0, 0.5, -4] }: { position?: [number, number, number] }) => (
  <group position={position}>
    <mesh position={[0, 0.5, 0]}>
      <boxGeometry args={[2.2, 1, 2]} />
      <meshStandardMaterial color="#8B5E3C" />
    </mesh>
    <mesh position={[0, 1.25, 0]} rotation={[0, 0, 0]}>
      <coneGeometry args={[1.5, 1, 4]} />
      <meshStandardMaterial color="#6B2E2E" />
    </mesh>
  </group>
);

const FarmScene: React.FC<Props> = ({ devices = [], onToggleDevice }) => {
  const weather = useWeather3d();

  const ambientIntensity = useMemo(() => {
    switch (weather.type) {
      case "rainy":
        return 0.6;
      case "cloudy":
        return 0.8;
      default:
        return 1.2;
    }
  }, [weather.type]);

  return (
    <div className="w-full h-96 rounded-lg overflow-hidden shadow-xl">
      <Canvas shadows camera={{ position: [6, 6, 6], fov: 50 }}>
        <ambientLight intensity={ambientIntensity} />
        <directionalLight position={[5, 10, 5]} intensity={0.8} castShadow />
        <Suspense fallback={<Html center>Loading 3D...</Html>}>
          <Sky sunPosition={weather.type === "night" ? [0, -1, 0] : [5, 2, 1]} />
          <FarmGround />
          <SimpleBarn />
          {/* Device markers passed from parent */}
          {devices.map((d) => (
            <DeviceMarker key={d.id} position={d.position} name={d.name} status={d.status} onClick={() => onToggleDevice?.(d.id)} />
          ))}
          {/* Optional visual flourishes */}
          <Stars radius={100} depth={50} count={300} factor={4} saturation={0} fade />
          <OrbitControls enablePan={true} enableRotate={true} enableZoom={true} />
        </Suspense>
      </Canvas>
    </div>
  );
};

export default FarmScene;
