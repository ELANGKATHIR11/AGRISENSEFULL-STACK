import React, { Suspense, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  OrbitControls, 
  Environment, 
  Text, 
  Box, 
  Sphere, 
  Plane,
  useTexture,
  Sky,
  Cloud,
  Float,
  Html,
  Billboard
} from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';

interface FarmSceneProps {
  sensorData?: {
    temperature: number;
    humidity: number;
    soilMoisture: number;
    lightIntensity: number;
  };
  irrigationActive?: boolean;
  className?: string;
}

// Animated Farm Field Component
interface SensorData {
  moisture?: number;
  temperature?: number;
  ph?: number;
  [key: string]: unknown;
}

function FarmField({ position, sensorData }: { position: [number, number, number], sensorData?: SensorData }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.02;
    }
  });

  return (
    <group position={position}>
      {/* Field Base */}
      <Plane
        ref={meshRef}
        args={[4, 4]}
        rotation={[-Math.PI / 2, 0, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial 
          color={hovered ? "#4ade80" : "#22c55e"} 
          roughness={0.8}
          metalness={0.1}
        />
      </Plane>
      
      {/* Crop Rows */}
      {Array.from({ length: 8 }, (_, i) => (
        <Float key={i} speed={1 + i * 0.1} rotationIntensity={0.1} floatIntensity={0.2}>
          <Box
            position={[
              -1.5 + (i % 4) * 1,
              0.2,
              -1.5 + Math.floor(i / 4) * 1.5
            ]}
            args={[0.1, 0.4, 0.1]}
          >
            <meshStandardMaterial color="#16a34a" />
          </Box>
        </Float>
      ))}
      
      {/* Sensor Data Display */}
      {sensorData && hovered && (
        <Html position={[0, 2, 0]} center>
          <div className="bg-white/90 backdrop-blur-sm p-3 rounded-lg shadow-lg border">
            <h4 className="font-semibold text-green-800 mb-2">Field Sensors</h4>
            <div className="space-y-1 text-sm">
              <div>🌡️ Temp: {String(sensorData.temperature)}°C</div>
              <div>💧 Humidity: {String(sensorData.humidity)}%</div>
              <div>🌱 Soil: {String(sensorData.soilMoisture)}%</div>
              <div>☀️ Light: {String(sensorData.lightIntensity)}%</div>
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}

// IoT Sensor Tower
function SensorTower({ position, active }: { position: [number, number, number], active: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current && active) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.5;
    }
  });

  return (
    <group position={position}>
      {/* Tower Base */}
      <Box args={[0.3, 2, 0.3]} position={[0, 1, 0]}>
        <meshStandardMaterial color="#64748b" metalness={0.8} roughness={0.2} />
      </Box>
      
      {/* Sensor Array */}
      <Sphere ref={meshRef} args={[0.2]} position={[0, 2.2, 0]}>
        <meshStandardMaterial 
          color={active ? "#10b981" : "#ef4444"} 
          emissive={active ? "#065f46" : "#7f1d1d"}
          emissiveIntensity={0.3}
        />
      </Sphere>
      
      {/* Signal Rings */}
      {active && Array.from({ length: 3 }, (_, i) => (
        <Float key={i} speed={2 + i} rotationIntensity={0} floatIntensity={0.5}>
          <mesh position={[0, 2.2, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3 + i * 0.2, 0.35 + i * 0.2, 16]} />
            <meshBasicMaterial 
              color="#10b981" 
              transparent 
              opacity={0.3 - i * 0.1}
            />
          </mesh>
        </Float>
      ))}
    </group>
  );
}

// Irrigation System
function IrrigationSystem({ position, active }: { position: [number, number, number], active: boolean }) {
  const waterRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (waterRef.current && active) {
      waterRef.current.scale.y = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.2;
    }
  });

  return (
    <group position={position}>
      {/* Sprinkler Head */}
      <Box args={[0.2, 0.1, 0.2]} position={[0, 1.5, 0]}>
        <meshStandardMaterial color="#3b82f6" metalness={0.7} roughness={0.3} />
      </Box>
      
      {/* Water Effect */}
      {active && (
        <>
          {Array.from({ length: 12 }, (_, i) => {
            const angle = (i / 12) * Math.PI * 2;
            return (
              <Float key={i} speed={3 + i * 0.1} rotationIntensity={0} floatIntensity={1}>
                <Sphere
                  ref={i === 0 ? waterRef : undefined}
                  args={[0.02]}
                  position={[
                    Math.cos(angle) * 0.5,
                    1.3 - Math.random() * 0.3,
                    Math.sin(angle) * 0.5
                  ]}
                >
                  <meshBasicMaterial color="#3b82f6" transparent opacity={0.7} />
                </Sphere>
              </Float>
            );
          })}
        </>
      )}
    </group>
  );
}

// Weather Visualization
function WeatherSystem({ temperature, humidity }: { temperature: number, humidity: number }) {
  const cloudOpacity = Math.min(humidity / 100, 0.8);
  const sunIntensity = Math.max(0.3, temperature / 40);

  return (
    <>
      <Sky 
        distance={450000}
        sunPosition={[100, 20, 100]}
        inclination={0.49}
        azimuth={0.25}
      />
      
      {/* Dynamic Clouds based on humidity */}
      {humidity > 60 && (
        <>
          <Cloud
            position={[10, 8, -10]}
            speed={0.2}
            opacity={cloudOpacity}
          />
          <Cloud
            position={[-8, 6, -5]}
            speed={0.15}
            opacity={cloudOpacity * 0.8}
          />
        </>
      )}
      
      {/* Sun intensity based on temperature */}
      <directionalLight
        position={[10, 10, 5]}
        intensity={sunIntensity}
        color="#fbbf24"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
    </>
  );
}

// Main Farm Scene Component
export default function FarmScene({ sensorData, irrigationActive = false, className }: FarmSceneProps) {
  const defaultSensorData = {
    temperature: 25,
    humidity: 65,
    soilMoisture: 45,
    lightIntensity: 80,
    ...sensorData
  };

  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{ position: [8, 6, 8], fov: 60 }}
        shadows
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          {/* Environment and Lighting */}
          <WeatherSystem 
            temperature={defaultSensorData.temperature} 
            humidity={defaultSensorData.humidity} 
          />
          <ambientLight intensity={0.4} />
          <fog attach="fog" args={['#f0f9ff', 10, 50]} />
          
          {/* Ground */}
          <Plane 
            args={[30, 30]} 
            rotation={[-Math.PI / 2, 0, 0]} 
            position={[0, -0.1, 0]}
            receiveShadow
          >
            <meshStandardMaterial color="#84cc16" roughness={0.9} />
          </Plane>
          
          {/* Farm Fields */}
          <FarmField position={[0, 0, 0]} sensorData={defaultSensorData} />
          <FarmField position={[6, 0, 0]} sensorData={{...defaultSensorData, temperature: 27}} />
          <FarmField position={[0, 0, 6]} sensorData={{...defaultSensorData, soilMoisture: 60}} />
          <FarmField position={[6, 0, 6]} sensorData={{...defaultSensorData, humidity: 70}} />
          
          {/* IoT Infrastructure */}
          <SensorTower position={[3, 0, 3]} active={true} />
          <SensorTower position={[-3, 0, -3]} active={true} />
          
          {/* Irrigation Systems */}
          <IrrigationSystem position={[1, 0, 1]} active={irrigationActive} />
          <IrrigationSystem position={[5, 0, 1]} active={irrigationActive} />
          <IrrigationSystem position={[1, 0, 5]} active={false} />
          <IrrigationSystem position={[5, 0, 5]} active={irrigationActive} />
          
          {/* Farm Title */}
          <Billboard position={[0, 4, -8]}>
            <Text
              fontSize={1.5}
              color="#16a34a"
              anchorX="center"
              anchorY="middle"
            >
              AgriSense Smart Farm
            </Text>
          </Billboard>
          
          {/* Controls */}
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={5}
            maxDistance={20}
            maxPolarAngle={Math.PI / 2}
          />
        </Suspense>
      </Canvas>
      
      {/* UI Overlay */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm p-4 rounded-lg shadow-lg">
        <h3 className="font-semibold text-green-800 mb-2">Farm Status</h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${irrigationActive ? 'bg-blue-500' : 'bg-gray-400'}`} />
            <span>Irrigation: {irrigationActive ? 'Active' : 'Inactive'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>Sensors: Online</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
            <span>Weather: Monitoring</span>
          </div>
        </div>
      </div>
    </div>
  );
}
