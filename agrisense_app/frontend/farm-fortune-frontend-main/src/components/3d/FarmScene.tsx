import React, { Suspense, useRef, useState, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { 
  OrbitControls, 
  Environment, 
  Text, 
  Box, 
  Sphere, 
  Plane,
  Sky,
  Cloud,
  Float,
  Html,
  Billboard,
  MeshReflectorMaterial,
  ContactShadows,
  Stars,
  Cylinder,
  Cone
} from '@react-three/drei';
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

// Enhanced Crop Plant Component
function CropPlant({ position, type = 'wheat', growth = 1 }: { position: [number, number, number], type?: string, growth?: number }) {
  const meshRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime + position[0]) * 0.08;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2 + position[0]) * 0.02;
    }
  });

  const cropColors = {
    wheat: { stem: '#7cb342', head: '#fdd835', leaf: '#8bc34a' },
    corn: { stem: '#558b2f', head: '#ff6f00', leaf: '#689f38' },
    rice: { stem: '#66bb6a', head: '#cddc39', leaf: '#7cb342' },
    soy: { stem: '#558b2f', head: '#4caf50', leaf: '#66bb6a' },
    vegetables: { stem: '#43a047', head: '#ef5350', leaf: '#66bb6a' },
    fruits: { stem: '#2e7d32', head: '#ff5722', leaf: '#4caf50' }
  };

  const colors = cropColors[type as keyof typeof cropColors] || cropColors.wheat;
  const height = 0.6 + growth * 0.5; // MUCH TALLER - increased from 0.3 to 0.6 base

  return (
    <group ref={meshRef} position={position}>
      {/* Thicker Stem */}
      <mesh position={[0, height / 2, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.05, height, 8]} />
        <meshStandardMaterial color={colors.stem} roughness={0.7} metalness={0.1} />
      </mesh>
      
      {/* Larger Leaves */}
      {Array.from({ length: 5 }, (_, i) => (
        <mesh 
          key={i}
          position={[
            Math.sin(i * (Math.PI * 2 / 5)) * 0.15,
            height * 0.3 + i * 0.12,
            Math.cos(i * (Math.PI * 2 / 5)) * 0.15
          ]}
          rotation={[0, i * (Math.PI * 2 / 5), Math.PI / 4]}
          castShadow
        >
          <boxGeometry args={[0.25, 0.03, 0.08]} />
          <meshStandardMaterial color={colors.leaf} roughness={0.6} />
        </mesh>
      ))}
      
      {/* Larger Crop Head */}
      <mesh position={[0, height, 0]} castShadow>
        <sphereGeometry args={[0.12, 12, 10]} />
        <meshStandardMaterial color={colors.head} roughness={0.5} emissive={colors.head} emissiveIntensity={0.3} />
      </mesh>
      
      {/* Additional crop details */}
      {Array.from({ length: 3 }, (_, i) => (
        <mesh 
          key={`detail-${i}`}
          position={[
            Math.sin(i * (Math.PI * 2 / 3)) * 0.1,
            height + 0.05,
            Math.cos(i * (Math.PI * 2 / 3)) * 0.1
          ]}
          castShadow
        >
          <sphereGeometry args={[0.06, 8, 8]} />
          <meshStandardMaterial color={colors.head} roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}

// Animated Farm Field Component
interface SensorData {
  moisture?: number;
  temperature?: number;
  humidity?: number;
  soilMoisture?: number;
  lightIntensity?: number;
  ph?: number;
  [key: string]: unknown;
}

function FarmField({ position, sensorData, cropType = 'wheat' }: { position: [number, number, number], sensorData?: SensorData, cropType?: string }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  
  // Realistic soil color based on moisture
  const soilColor = useMemo(() => {
    const moisture = sensorData?.soilMoisture || 50;
    const lightness = 20 + (100 - moisture) * 0.3;
    return new THREE.Color(`hsl(30, 40%, ${lightness}%)`);
  }, [sensorData?.soilMoisture]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
    }
  });

  return (
    <group position={position}>
      {/* VIBRANT GREEN GRASS FLOOR - Larger and more visible */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.02, 0]}
        receiveShadow
      >
        <planeGeometry args={[8, 8, 32, 32]} />
        <meshStandardMaterial 
          color="#22c55e"
          roughness={0.85}
          metalness={0}
        />
      </mesh>
      
      {/* Soil Base underneath grass */}
      <Plane
        ref={meshRef}
        args={[8, 8]}
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
        receiveShadow
      >
        <meshStandardMaterial 
          color={soilColor} 
          roughness={0.95}
          metalness={0}
        />
      </Plane>
      
      {/* Dense Crop Grid - More crops, closer spacing */}
      {Array.from({ length: 36 }, (_, i) => {
        const row = Math.floor(i / 6);
        const col = i % 6;
        return (
          <Float key={i} speed={0.5 + i * 0.03} rotationIntensity={0.05} floatIntensity={0.15}>
            <CropPlant
              position={[
                -3 + col * 1.2,
                0.05,
                -3 + row * 1.2
              ]}
              type={cropType}
              growth={0.9 + Math.random() * 0.3}
            />
          </Float>
        );
      })}
      
      {/* Add grass tufts for extra detail */}
      {Array.from({ length: 20 }, (_, i) => {
        const angle = (i / 20) * Math.PI * 2;
        const radius = 3 + Math.random() * 0.5;
        return (
          <mesh
            key={`grass-${i}`}
            position={[
              Math.cos(angle) * radius,
              0.05,
              Math.sin(angle) * radius
            ]}
            rotation={[0, Math.random() * Math.PI, 0]}
            castShadow
          >
            <coneGeometry args={[0.08, 0.3, 4]} />
            <meshStandardMaterial color="#16a34a" roughness={0.8} />
          </mesh>
        );
      })}
      
      {/* Sensor Data Display - Enhanced UI */}
      {sensorData && hovered && (
        <Html position={[0, 3, 0]} center distanceFactor={8}>
          <div className="bg-gradient-to-br from-white/95 to-green-50/95 backdrop-blur-md p-4 rounded-xl shadow-2xl border-2 border-green-200 min-w-[200px]">
            <h4 className="font-bold text-green-800 mb-3 text-center border-b border-green-200 pb-2">📊 Field Sensors</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">🌡️ Temperature:</span>
                <span className="font-semibold text-orange-600">{String(sensorData.temperature)}°C</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">💧 Humidity:</span>
                <span className="font-semibold text-blue-600">{String(sensorData.humidity)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">🌱 Soil Moisture:</span>
                <span className="font-semibold text-green-600">{String(sensorData.soilMoisture)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">☀️ Light:</span>
                <span className="font-semibold text-yellow-600">{String(sensorData.lightIntensity)}%</span>
              </div>
            </div>
          </div>
        </Html>
      )}
      
      {/* Contact Shadows for realism */}
      <ContactShadows 
        position={[0, 0.01, 0]} 
        opacity={0.4} 
        scale={5} 
        blur={1.5} 
        far={2} 
      />
    </group>
  );
}

// Enhanced IoT Sensor Tower
function SensorTower({ position, active }: { position: [number, number, number], active: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const panelRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (meshRef.current && active) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.5;
    }
    if (panelRef.current) {
      // Solar panel tracking the sun
      panelRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.3;
    }
  });

  return (
    <group position={position}>
      {/* Modern Tower Base with segments */}
      <mesh position={[0, 0.5, 0]} castShadow>
        <cylinderGeometry args={[0.15, 0.2, 1, 8]} />
        <meshStandardMaterial color="#475569" metalness={0.9} roughness={0.1} />
      </mesh>
      
      {/* Middle Section */}
      <mesh position={[0, 1.3, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.15, 0.6, 8]} />
        <meshStandardMaterial color="#64748b" metalness={0.8} roughness={0.2} />
      </mesh>
      
      {/* Top Section */}
      <mesh position={[0, 1.9, 0]} castShadow>
        <cylinderGeometry args={[0.1, 0.12, 0.4, 8]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.7} roughness={0.3} />
      </mesh>
      
      {/* Solar Panel */}
      <group ref={panelRef} position={[0, 2.3, 0]}>
        <Box args={[0.4, 0.02, 0.3]} castShadow>
          <meshStandardMaterial 
            color="#1e3a8a" 
            metalness={0.9} 
            roughness={0.1}
            emissive="#1e3a8a"
            emissiveIntensity={0.2}
          />
        </Box>
      </group>
      
      {/* Advanced Sensor Array */}
      <Sphere ref={meshRef} args={[0.25, 16, 16]} position={[0, 2.6, 0]} castShadow>
        <meshStandardMaterial 
          color={active ? "#10b981" : "#ef4444"} 
          emissive={active ? "#10b981" : "#ef4444"}
          emissiveIntensity={active ? 0.8 : 0.3}
          metalness={0.8}
          roughness={0.2}
        />
      </Sphere>
      
      {/* Camera Sensors */}
      {[0, 120, 240].map((angle, i) => (
        <mesh
          key={i}
          position={[
            Math.cos((angle * Math.PI) / 180) * 0.28,
            2.6,
            Math.sin((angle * Math.PI) / 180) * 0.28
          ]}
          rotation={[0, (angle * Math.PI) / 180, 0]}
          castShadow
        >
          <boxGeometry args={[0.08, 0.06, 0.04]} />
          <meshStandardMaterial color="#1f2937" metalness={0.9} roughness={0.1} />
        </mesh>
      ))}
      
      {/* Signal Rings - Enhanced */}
      {active && Array.from({ length: 4 }, (_, i) => (
        <Float key={i} speed={2 + i * 0.3} rotationIntensity={0} floatIntensity={0.8}>
          <mesh position={[0, 2.6, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.35 + i * 0.25, 0.38 + i * 0.25, 32]} />
            <meshBasicMaterial 
              color="#10b981" 
              transparent 
              opacity={0.4 - i * 0.08}
              side={THREE.DoubleSide}
            />
          </mesh>
        </Float>
      ))}
      
      {/* Status Light */}
      {active && (
        <pointLight 
          position={[0, 2.6, 0]} 
          color="#10b981" 
          intensity={2}
          distance={5}
        />
      )}
    </group>
  );
}

// Enhanced Irrigation System
function IrrigationSystem({ position, active }: { position: [number, number, number], active: boolean }) {
  const waterRef = useRef<THREE.Group>(null);
  const sprinklerRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (sprinklerRef.current && active) {
      sprinklerRef.current.rotation.y = state.clock.elapsedTime * 2;
    }
  });

  return (
    <group position={position}>
      {/* Irrigation Pipe Base */}
      <mesh position={[0, 0.75, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.04, 1.5, 16]} />
        <meshStandardMaterial color="#71717a" metalness={0.9} roughness={0.2} />
      </mesh>
      
      {/* Pipe Joint */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial color="#52525b" metalness={0.9} roughness={0.2} />
      </mesh>
      
      {/* Modern Sprinkler Head */}
      <mesh ref={sprinklerRef} position={[0, 1.65, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.08, 0.2, 8]} />
        <meshStandardMaterial 
          color={active ? "#3b82f6" : "#94a3b8"} 
          metalness={0.8} 
          roughness={0.2}
          emissive={active ? "#3b82f6" : "#000000"}
          emissiveIntensity={active ? 0.3 : 0}
        />
      </mesh>
      
      {/* Sprinkler Nozzles */}
      {[0, 90, 180, 270].map((angle, i) => (
        <mesh
          key={i}
          position={[
            Math.cos((angle * Math.PI) / 180) * 0.12,
            1.65,
            Math.sin((angle * Math.PI) / 180) * 0.12
          ]}
          rotation={[Math.PI / 2, 0, (angle * Math.PI) / 180]}
          castShadow
        >
          <cylinderGeometry args={[0.02, 0.01, 0.08, 8]} />
          <meshStandardMaterial color="#3b82f6" metalness={0.9} roughness={0.1} />
        </mesh>
      ))}
      
      {/* Enhanced Water Effect */}
      {active && (
        <group ref={waterRef}>
          {/* Water Arc Particles */}
          {Array.from({ length: 24 }, (_, i) => {
            const angle = (i / 24) * Math.PI * 2;
            const radius = 0.8 + Math.random() * 0.4;
            const height = 1.6 - Math.random() * 0.8;
            return (
              <Float key={i} speed={4 + i * 0.1} rotationIntensity={0} floatIntensity={1.5}>
                <Sphere
                  args={[0.03, 8, 8]}
                  position={[
                    Math.cos(angle) * radius,
                    height,
                    Math.sin(angle) * radius
                  ]}
                  castShadow
                >
                  <meshStandardMaterial 
                    color="#60a5fa" 
                    transparent 
                    opacity={0.8}
                    metalness={0.3}
                    roughness={0.2}
                    emissive="#3b82f6"
                    emissiveIntensity={0.2}
                  />
                </Sphere>
              </Float>
            );
          })}
          
          {/* Water Spray Effect */}
          {Array.from({ length: 6 }, (_, i) => {
            const angle = (i / 6) * Math.PI * 2;
            return (
              <mesh
                key={`spray-${i}`}
                position={[
                  Math.cos(angle) * 0.6,
                  1.4,
                  Math.sin(angle) * 0.6
                ]}
                rotation={[0, angle, Math.PI / 4]}
              >
                <coneGeometry args={[0.15, 0.4, 8, 1, true]} />
                <meshBasicMaterial 
                  color="#60a5fa" 
                  transparent 
                  opacity={0.3}
                  side={THREE.DoubleSide}
                />
              </mesh>
            );
          })}
          
          {/* Ground Water Puddle */}
          <mesh position={[0, 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <circleGeometry args={[1.2, 32]} />
            <meshStandardMaterial 
              color="#3b82f6" 
              transparent 
              opacity={0.4}
              metalness={0.8}
              roughness={0.1}
            />
          </mesh>
          
          {/* Blue light effect */}
          <pointLight 
            position={[0, 1.5, 0]} 
            color="#3b82f6" 
            intensity={1.5}
            distance={3}
          />
        </group>
      )}
    </group>
  );
}

// Enhanced Weather Visualization
function WeatherSystem({ temperature, humidity }: { temperature: number, humidity: number }) {
  const cloudOpacity = Math.min(humidity / 100, 0.7);
  const sunIntensity = Math.max(0.8, temperature / 35);
  const sunColor = temperature > 30 ? "#fbbf24" : "#fed7aa";

  return (
    <>
      {/* Realistic Sky with gradient */}
      <Sky 
        distance={450000}
        sunPosition={[100, 30, 100]}
        inclination={0.49}
        azimuth={0.25}
        turbidity={2}
        rayleigh={0.5}
      />
      
      {/* Stars for evening effect (if low temperature) */}
      {temperature < 20 && (
        <Stars 
          radius={100} 
          depth={50} 
          count={3000} 
          factor={2} 
          saturation={0}
          fade
          speed={0.5}
        />
      )}
      
      {/* Dynamic Volumetric Clouds */}
      {humidity > 50 && (
        <>
          <Cloud
            position={[15, 12, -15]}
            speed={0.15}
            opacity={cloudOpacity}
            color="#e0f2fe"
            segments={20}
          />
          <Cloud
            position={[-12, 10, -8]}
            speed={0.12}
            opacity={cloudOpacity * 0.85}
            color="#dbeafe"
            segments={18}
          />
          <Cloud
            position={[5, 14, -20]}
            speed={0.18}
            opacity={cloudOpacity * 0.7}
            color="#f0f9ff"
            segments={16}
          />
        </>
      )}
      
      {humidity > 75 && (
        <>
          <Cloud
            position={[-8, 8, 10]}
            speed={0.1}
            opacity={cloudOpacity * 0.9}
            color="#cbd5e1"
            segments={22}
          />
          <Cloud
            position={[18, 11, -5]}
            speed={0.14}
            opacity={cloudOpacity * 0.75}
            color="#e2e8f0"
            segments={19}
          />
        </>
      )}
      
      {/* Enhanced Sun lighting with realistic shadows */}
      <directionalLight
        position={[15, 20, 10]}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
        shadow-mapSize-width={4096}
        shadow-mapSize-height={4096}
        shadow-camera-far={50}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={20}
        shadow-camera-bottom={-20}
        shadow-bias={-0.0001}
      />
      
      {/* Ambient warm light */}
      <hemisphereLight
        args={["#87ceeb", "#6b7280", 0.4]}
      />
      
      {/* Fill light for better detail visibility */}
      <directionalLight
        position={[-10, 15, -10]}
        intensity={0.3}
        color="#e0f2fe"
      />
    </>
  );
}

// ========================================
// ADVANCED COMPONENT: Complex Polygonal Farmland Terrain
// ========================================
function ComplexFarmTerrain() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  console.log('[ComplexFarmTerrain] Rendering terrain component');
  
  // Create realistic terrain with complex polygon geometry
  const terrainGeometry = useMemo(() => {
    console.log('[ComplexFarmTerrain] Creating terrain geometry');
    const geometry = new THREE.PlaneGeometry(60, 60, 80, 80);
    const positions = geometry.attributes.position;
    
    // Advanced terrain generation with multiple noise layers
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const z = positions.getZ(i);
      
      // Layer 1: Large rolling hills
      const hills = Math.sin(x * 0.08) * Math.cos(z * 0.08) * 1.5;
      
      // Layer 2: Medium variations (farmland rows)
      const rows = Math.sin(x * 0.3) * 0.3;
      
      // Layer 3: Fine detail (soil texture)
      const detail = Math.sin(x * 2) * Math.cos(z * 2) * 0.05;
      
      positions.setY(i, hills + rows + detail);
    }
    
    positions.needsUpdate = true;
    geometry.computeVertexNormals();
    return geometry;
  }, []);

  return (
    <>
      {/* Main farmland terrain - 360° view optimized */}
      <mesh 
        ref={meshRef}
        geometry={terrainGeometry}
        rotation={[-Math.PI / 2, 0, 0]} 
        position={[0, -0.1, 0]}
        receiveShadow
      >
        <meshStandardMaterial 
          color="#4d7c0f" 
          roughness={0.9}
          metalness={0}
          wireframe={false}
        />
      </mesh>
      
      {/* Circular farm boundary */}
      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[28, 30, 64]} />
        <meshStandardMaterial color="#65a30d" roughness={0.8} metalness={0.2} />
      </mesh>
      
      {/* Irrigation channels (water trenches) - Cross pattern for 360° */}
      {[-10, 0, 10].map((x, i) => (
        <mesh key={`h-${i}`} position={[x, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[1, 60]} />
          <meshStandardMaterial color="#0ea5e9" roughness={0.1} metalness={0.8} />
        </mesh>
      ))}
      {[-10, 0, 10].map((z, i) => (
        <mesh key={`v-${i}`} position={[0, 0.05, z]} rotation={[-Math.PI / 2, 0, Math.PI / 2]} receiveShadow>
          <planeGeometry args={[1, 60]} />
          <meshStandardMaterial color="#0ea5e9" roughness={0.1} metalness={0.8} />
        </mesh>
      ))}
      
      {/* Farmland plot dividers */}
      <ContactShadows 
        position={[0, 0, 0]} 
        opacity={0.4} 
        scale={65} 
        blur={2.5} 
        far={12} 
      />
    </>
  );
}

// ========================================
// ADVANCED COMPONENT: Large Water Tank Complex
// ========================================
function WaterTankSystem({ position }: { position: [number, number, number] }) {
  const [isActive, setIsActive] = useState(true);
  
  return (
    <group position={position}>
      {/* Large cylindrical water tank */}
      <mesh position={[0, 3, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[2, 2.2, 6, 32]} />
        <meshStandardMaterial 
          color="#38bdf8" 
          roughness={0.2} 
          metalness={0.8}
          transparent
          opacity={0.7}
        />
      </mesh>
      
      {/* Tank top dome */}
      <mesh position={[0, 6, 0]} castShadow>
        <sphereGeometry args={[2.1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial color="#0284c7" roughness={0.3} metalness={0.9} />
      </mesh>
      
      {/* Water level indicator */}
      <mesh position={[0, 4, 2.3]}>
        <boxGeometry args={[0.4, 3, 0.1]} />
        <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.5} />
      </mesh>
      
      {/* Tank support structure (legs) */}
      {[0, 90, 180, 270].map((angle, i) => (
        <mesh
          key={i}
          position={[
            Math.cos((angle * Math.PI) / 180) * 2,
            1.5,
            Math.sin((angle * Math.PI) / 180) * 2
          ]}
          castShadow
        >
          <cylinderGeometry args={[0.15, 0.15, 3, 8]} />
          <meshStandardMaterial color="#71717a" roughness={0.4} metalness={0.9} />
        </mesh>
      ))}
      
      {/* Main outlet pipe */}
      <mesh position={[0, 0.5, 2.5]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.2, 3, 16]} />
        <meshStandardMaterial color="#52525b" roughness={0.3} metalness={0.9} />
      </mesh>
      
      {/* Distribution pipes network */}
      {[-1, 0, 1].map((offset, i) => (
        <mesh key={i} position={[offset * 3, 0.3, 4]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.12, 0.12, 6, 12]} />
          <meshStandardMaterial color="#3f3f46" roughness={0.3} metalness={0.9} />
        </mesh>
      ))}
      
      {/* Water flow particles (when active) */}
      {isActive && (
        <pointLight position={[0, 4, 0]} color="#0ea5e9" intensity={3} distance={8} />
      )}
      
      {/* Control panel */}
      <mesh position={[2.5, 1.5, 0]} castShadow>
        <boxGeometry args={[0.5, 1, 0.3]} />
        <meshStandardMaterial color="#1f2937" roughness={0.4} metalness={0.8} />
      </mesh>
      
      {/* Status indicator light */}
      <mesh position={[2.5, 2.2, 0.2]}>
        <sphereGeometry args={[0.1, 16, 16]} />
        <meshStandardMaterial 
          color={isActive ? "#10b981" : "#ef4444"} 
          emissive={isActive ? "#10b981" : "#ef4444"}
          emissiveIntensity={1}
        />
      </mesh>
      
      {/* Tank label */}
      <Html position={[0, 7, 0]} center>
        <div className="bg-white/90 px-3 py-1 rounded-lg shadow-lg text-xs font-bold text-blue-700">
          💧 Water Tank: 5000L
        </div>
      </Html>
    </group>
  );
}

// ========================================
// ADVANCED COMPONENT: Advanced IoT Sensor Array
// ========================================
function IoTSensorHub({ position, type = 'weather' }: { position: [number, number, number], type?: 'weather' | 'soil' | 'camera' }) {
  const sensorRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (sensorRef.current) {
      // Gentle rotation for weather vane effect
      sensorRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
    }
  });
  
  const sensorColors = {
    weather: { primary: '#f59e0b', secondary: '#d97706', icon: '🌤️' },
    soil: { primary: '#84cc16', secondary: '#65a30d', icon: '🌱' },
    camera: { primary: '#3b82f6', secondary: '#2563eb', icon: '📷' }
  };
  
  const colors = sensorColors[type];
  
  return (
    <group ref={sensorRef} position={position}>
      {/* Sensor pole */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <cylinderGeometry args={[0.08, 0.08, 3, 16]} />
        <meshStandardMaterial color="#3f3f46" roughness={0.3} metalness={0.9} />
      </mesh>
      
      {/* Solar panel */}
      <mesh position={[0, 3.2, 0]} rotation={[-Math.PI / 6, 0, 0]} castShadow>
        <boxGeometry args={[0.8, 0.05, 1.2]} />
        <meshStandardMaterial color="#1e40af" roughness={0.2} metalness={0.9} />
      </mesh>
      
      {/* Main sensor housing */}
      <mesh position={[0, 2.5, 0]} castShadow>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial color={colors.primary} roughness={0.3} metalness={0.7} />
      </mesh>
      
      {/* Sensor antenna */}
      <mesh position={[0, 3.8, 0]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 1.2, 8]} />
        <meshStandardMaterial color="#dc2626" emissive="#dc2626" emissiveIntensity={0.5} />
      </mesh>
      
      {/* Signal indicator rings */}
      {[0, 1, 2].map((i) => (
        <Float key={i} speed={2 + i} rotationIntensity={0} floatIntensity={0.5}>
          <mesh position={[0, 4.2 + i * 0.3, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3 + i * 0.2, 0.32 + i * 0.2, 24]} />
            <meshBasicMaterial 
              color={colors.secondary} 
              transparent 
              opacity={0.5 - i * 0.1}
              side={THREE.DoubleSide}
            />
          </mesh>
        </Float>
      ))}
      
      {/* IoT connectivity light */}
      <pointLight position={[0, 2.5, 0]} color={colors.primary} intensity={2} distance={4} />
      
      {/* Sensor type label */}
      <Billboard position={[0, 5, 0]}>
        <Text fontSize={0.3} color="#fff" outlineWidth={0.02} outlineColor="#000">
          {colors.icon} {type.toUpperCase()}
        </Text>
      </Billboard>
    </group>
  );
}

// ========================================
// ADVANCED COMPONENT: AI/ML Processing Unit
// ========================================
function AIMLProcessor({ position }: { position: [number, number, number] }) {
  const processorRef = useRef<THREE.Group>(null);
  const [isProcessing, setIsProcessing] = useState(true);
  
  useFrame((state) => {
    if (processorRef.current && isProcessing) {
      processorRef.current.rotation.y = state.clock.elapsedTime * 0.5;
    }
  });
  
  return (
    <group position={position}>
      {/* AI Server rack */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <boxGeometry args={[2, 3, 1.5]} />
        <meshStandardMaterial color="#1f2937" roughness={0.3} metalness={0.9} />
      </mesh>
      
      {/* Server rack details (horizontal lines) */}
      {[0.5, 1, 1.5, 2, 2.5].map((h, i) => (
        <mesh key={i} position={[0, h, 0.76]}>
          <boxGeometry args={[1.8, 0.05, 0.02]} />
          <meshStandardMaterial color="#4ade80" emissive="#4ade80" emissiveIntensity={0.3} />
        </mesh>
      ))}
      
      {/* Processing core (rotating) */}
      <group ref={processorRef} position={[0, 3.5, 0]}>
        <mesh castShadow>
          <boxGeometry args={[0.8, 0.8, 0.8]} />
          <meshStandardMaterial 
            color="#8b5cf6" 
            roughness={0.2} 
            metalness={0.9}
            emissive="#8b5cf6"
            emissiveIntensity={0.5}
          />
        </mesh>
        
        {/* Processing cores */}
        {[-0.3, 0, 0.3].map((offset, i) => (
          <mesh key={i} position={[offset, 0, 0.41]}>
            <sphereGeometry args={[0.08, 16, 16]} />
            <meshStandardMaterial color="#10b981" emissive="#10b981" emissiveIntensity={1} />
          </mesh>
        ))}
      </group>
      
      {/* Neural network visualization */}
      {[0, 120, 240].map((angle, i) => (
        <Float key={i} speed={2 + i * 0.5} rotationIntensity={0} floatIntensity={1}>
          <mesh
            position={[
              Math.cos((angle * Math.PI) / 180) * 1.5,
              3.5,
              Math.sin((angle * Math.PI) / 180) * 1.5
            ]}
          >
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshStandardMaterial 
              color="#06b6d4" 
              emissive="#06b6d4" 
              emissiveIntensity={0.8}
              transparent
              opacity={0.7}
            />
          </mesh>
        </Float>
      ))}
      
      {/* Data connection lines */}
      <pointLight position={[0, 3.5, 0]} color="#8b5cf6" intensity={5} distance={6} />
      
      {/* AI label */}
      <Html position={[0, 5, 0]} center>
        <div className="bg-purple-500/90 px-4 py-2 rounded-lg shadow-xl text-white font-bold flex items-center gap-2">
          <span className="text-xl">🧠</span>
          <div className="text-left">
            <div className="text-sm">AI/ML Engine</div>
            <div className="text-xs opacity-80">Processing Data...</div>
          </div>
        </div>
      </Html>
    </group>
  );
}

// ========================================
// ADVANCED COMPONENT: Autonomous Drone Fleet
// ========================================
function MonitoringDrone({ position, patrolPath = 0 }: { position: [number, number, number], patrolPath?: number }) {
  const droneRef = useRef<THREE.Group>(null);
  const propellerRefs = useRef<THREE.Mesh[]>([]);
  
  useFrame((state) => {
    if (droneRef.current) {
      // Enhanced circular patrol pattern for 360° visibility
      const time = state.clock.elapsedTime + patrolPath * 2;
      const radius = 12 + patrolPath * 2;
      droneRef.current.position.x = position[0] + Math.cos(time * 0.4) * radius;
      droneRef.current.position.z = position[2] + Math.sin(time * 0.4) * radius;
      droneRef.current.position.y = position[1] + Math.sin(time * 0.8) * 1.5;
      
      // Enhanced drone tilt based on movement direction
      droneRef.current.rotation.z = -Math.cos(time * 0.4) * 0.3;
      droneRef.current.rotation.x = -Math.sin(time * 0.4) * 0.3;
      droneRef.current.rotation.y = time * 0.4;
    }
    
    // Spin propellers
    propellerRefs.current.forEach((prop) => {
      if (prop) prop.rotation.y += 0.5;
    });
  });
  
  return (
    <group ref={droneRef} position={position}>
      {/* Drone body */}
      <mesh castShadow>
        <boxGeometry args={[0.6, 0.2, 0.6]} />
        <meshStandardMaterial color="#1f2937" roughness={0.3} metalness={0.9} />
      </mesh>
      
      {/* Camera gimbal */}
      <mesh position={[0, -0.2, 0]} castShadow>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial color="#3b82f6" roughness={0.2} metalness={0.9} />
      </mesh>
      
      {/* Camera lens */}
      <mesh position={[0, -0.3, 0.1]} rotation={[Math.PI / 4, 0, 0]}>
        <cylinderGeometry args={[0.08, 0.06, 0.15, 16]} />
        <meshStandardMaterial color="#1e3a8a" roughness={0.1} metalness={1} />
      </mesh>
      
      {/* Drone arms and propellers */}
      {[
        [-0.4, 0, -0.4],
        [0.4, 0, -0.4],
        [-0.4, 0, 0.4],
        [0.4, 0, 0.4]
      ].map((armPos, i) => (
        <group key={i}>
          {/* Arm */}
          <mesh position={armPos as [number, number, number]} castShadow>
            <cylinderGeometry args={[0.03, 0.03, 0.3, 8]} />
            <meshStandardMaterial color="#52525b" />
          </mesh>
          
          {/* Motor */}
          <mesh position={[armPos[0], armPos[1] + 0.15, armPos[2]]} castShadow>
            <cylinderGeometry args={[0.06, 0.05, 0.08, 12]} />
            <meshStandardMaterial color="#dc2626" roughness={0.3} metalness={0.8} />
          </mesh>
          
          {/* Propeller */}
          <mesh
            ref={(el) => { if (el) propellerRefs.current[i] = el; }}
            position={[armPos[0], armPos[1] + 0.2, armPos[2]]}
            rotation={[Math.PI / 2, 0, 0]}
          >
            <boxGeometry args={[0.6, 0.02, 0.08]} />
            <meshStandardMaterial color="#3b82f6" transparent opacity={0.6} />
          </mesh>
        </group>
      ))}
      
      {/* Status LED */}
      <pointLight position={[0, 0.2, 0]} color="#10b981" intensity={2} distance={3} />
      
      {/* Drone label */}
      <Billboard position={[0, 0.8, 0]}>
        <Text fontSize={0.2} color="#fff" outlineWidth={0.015} outlineColor="#000">
          🚁 PATROL
        </Text>
      </Billboard>
    </group>
  );
}

// Enhanced Ground (keeping original for compatibility)
function EnhancedGround() {
  return null; // Replaced by ComplexFarmTerrain
}

// Main Enhanced Farm Scene Component
export default function FarmScene({ sensorData, irrigationActive = false, className }: FarmSceneProps) {
  const defaultSensorData = {
    temperature: 25,
    humidity: 65,
    soilMoisture: 45,
    lightIntensity: 80,
    ...sensorData
  };

  const cropTypes = ['wheat', 'corn', 'tomato', 'lettuce'];

  console.log('[FarmScene] Rendering scene with irrigationActive:', irrigationActive);

  return (
    <div className={`w-full h-full relative ${className}`}>
      <Canvas 
        camera={{ 
          position: [35, 25, 35], 
          fov: 60,
          near: 0.1,
          far: 1000
        }}
        shadows="soft"
        gl={{ 
          antialias: true, 
          alpha: false
        }}
      >
        <color attach="background" args={['#87ceeb']} />
        <Suspense fallback={null}>
          {/* ========================================
              LIGHTING SYSTEM
              ======================================== */}
          <ambientLight intensity={0.8} />
          <directionalLight 
            position={[20, 30, 20]} 
            intensity={1.5}
            castShadow
            shadow-mapSize-width={2048}
            shadow-mapSize-height={2048}
          />
          <pointLight position={[0, 15, 0]} intensity={0.8} color="#ffd700" />
          <hemisphereLight args={['#87ceeb', '#228b22', 0.4]} />
          <fog attach="fog" args={['#87ceeb', 80, 200]} />
          
          {/* ========================================
              LARGE GREEN GRASS BASE FLOOR
              ======================================== */}
          <mesh position={[0, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[150, 150, 50, 50]} />
            <meshStandardMaterial 
              color="#22c55e"
              roughness={0.9}
              metalness={0}
            />
          </mesh>
          
          {/* Dark green borders for depth */}
          <mesh position={[0, -0.08, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <ringGeometry args={[75, 78, 64]} />
            <meshStandardMaterial 
              color="#16a34a"
              roughness={0.95}
            />
          </mesh>
          
          {/* ========================================
              ENVIRONMENT & WEATHER
              ======================================== */}
          <WeatherSystem temperature={defaultSensorData.temperature} humidity={defaultSensorData.humidity} />
          
          {/* ========================================
              MAIN FARM TERRAIN
              ======================================== */}
          <ComplexFarmTerrain />
          
          {/* ========================================
              WATER TANK SYSTEMS (x4 at corners)
              ======================================== */}
          <WaterTankSystem position={[-20, 0, -20]} />
          <WaterTankSystem position={[20, 0, -20]} />
          <WaterTankSystem position={[-20, 0, 20]} />
          <WaterTankSystem position={[20, 0, 20]} />
          
          {/* ========================================
              IOT SENSOR NETWORK (x8 strategic placement)
              ======================================== */}
          <IoTSensorHub position={[-15, 0, -15]} type="weather" />
          <IoTSensorHub position={[15, 0, -15]} type="weather" />
          <IoTSensorHub position={[-15, 0, 0]} type="soil" />
          <IoTSensorHub position={[0, 0, -15]} type="soil" />
          <IoTSensorHub position={[15, 0, 0]} type="soil" />
          <IoTSensorHub position={[0, 0, 15]} type="soil" />
          <IoTSensorHub position={[-15, 0, 15]} type="camera" />
          <IoTSensorHub position={[15, 0, 15]} type="camera" />
          
          {/* ========================================
              AI/ML PROCESSING CENTER
              ======================================== */}
          <AIMLProcessor position={[0, 0, -25]} />
          
          {/* ========================================
              AUTONOMOUS DRONE FLEET (x4)
              ======================================== */}
          <MonitoringDrone position={[0, 12, 0]} patrolPath={0} />
          <MonitoringDrone position={[10, 10, 10]} patrolPath={1} />
          <MonitoringDrone position={[-10, 14, -10]} patrolPath={2} />
          <MonitoringDrone position={[8, 11, -8]} patrolPath={3} />
          
          {/* ========================================
              FARM FIELDS (x6 with different crops)
              ======================================== */}
          <FarmField position={[-12, 0.1, -8]} cropType="wheat" />
          <FarmField position={[12, 0.1, -8]} cropType="corn" />
          <FarmField position={[-12, 0.1, 8]} cropType="rice" />
          <FarmField position={[12, 0.1, 8]} cropType="soy" />
          <FarmField position={[-5, 0.1, 0]} cropType="vegetables" />
          <FarmField position={[5, 0.1, 0]} cropType="fruits" />
          
          {/* ========================================
              SENSOR TOWERS (x4 at cardinal points)
              ======================================== */}
          <SensorTower position={[0, 0, -30]} active={true} />
          <SensorTower position={[30, 0, 0]} active={true} />
          <SensorTower position={[0, 0, 30]} active={true} />
          <SensorTower position={[-30, 0, 0]} active={true} />
          
          {/* ========================================
              IRRIGATION SYSTEM (x6 grid)
              ======================================== */}
          {irrigationActive && (
            <>
              <IrrigationSystem position={[-15, 0, -10]} active={true} />
              <IrrigationSystem position={[0, 0, -10]} active={true} />
              <IrrigationSystem position={[15, 0, -10]} active={true} />
              <IrrigationSystem position={[-15, 0, 10]} active={true} />
              <IrrigationSystem position={[0, 0, 10]} active={true} />
              <IrrigationSystem position={[15, 0, 10]} active={true} />
            </>
          )}
          
          {/* ========================================
              SCENE LABELS
              ======================================== */}
          <Billboard position={[0, 25, 0]}>
            <Text fontSize={3} color="#2d5016" fontWeight="bold">
              AgriSense Farm
            </Text>
          </Billboard>
          
          <Billboard position={[0, 20, 0]}>
            <Text fontSize={1.2} color="#4a7c23">
              360° IoT-Enabled Smart Agriculture
            </Text>
          </Billboard>
          
          {/* ========================================
              CAMERA CONTROLS - 360° Rotation
              ======================================== */}
          <OrbitControls 
            autoRotate={true}
            autoRotateSpeed={0.5}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={20}
            maxDistance={100}
            maxPolarAngle={Math.PI / 2.2}
          />
          
          {/* ========================================
              ENVIRONMENT EFFECTS
              ======================================== */}
          <Environment preset="sunset" />
        </Suspense>
      </Canvas>      {/* ========================================
          ADVANCED UI OVERLAY - System Status
          ========================================*/}
      <div className="absolute top-4 left-4 bg-gradient-to-br from-white/90 to-green-50/90 backdrop-blur-xl p-6 rounded-2xl shadow-2xl border-2 border-green-200/50">
        <h3 className="font-bold text-green-900 mb-4 text-xl flex items-center gap-2">
          <span className="text-3xl">🌾</span>
          <div>
            <div>AgriSense Farm</div>
            <div className="text-xs font-normal text-green-600">Advanced IoT Platform</div>
          </div>
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse shadow-lg" />
              <span className="font-medium">💧 Water Tanks:</span>
            </div>
            <span className="font-bold text-blue-600">2 Active</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse shadow-lg" />
              <span className="font-medium">📡 IoT Sensors:</span>
            </div>
            <span className="font-bold text-green-600">8 Online</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500 animate-pulse shadow-lg" />
              <span className="font-medium">🧠 AI/ML Engine:</span>
            </div>
            <span className="font-bold text-purple-600">Processing</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-500 animate-pulse shadow-lg" />
              <span className="font-medium">🚁 Drones:</span>
            </div>
            <span className="font-bold text-cyan-600">3 Patrolling</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${irrigationActive ? 'bg-teal-500 animate-pulse' : 'bg-gray-400'} shadow-lg`} />
              <span className="font-medium">💦 Irrigation:</span>
            </div>
            <span className={`font-bold ${irrigationActive ? 'text-teal-600' : 'text-gray-500'}`}>
              {irrigationActive ? 'Active' : 'Standby'}
            </span>
          </div>
        </div>
      </div>
      
      {/* ========================================
          SYSTEM METRICS - Live Data
          ========================================*/}
      <div className="absolute bottom-4 right-4 bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl p-5 rounded-2xl shadow-2xl border-2 border-cyan-400/50 min-w-[280px]">
        <h4 className="font-bold text-cyan-300 mb-3 text-base flex items-center gap-2">
          <span className="text-xl">📊</span> Live System Metrics
        </h4>
        <div className="space-y-2.5 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Farm Fields:</span>
            <span className="font-bold text-green-400 text-lg">6/6</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">IoT Network:</span>
            <span className="font-bold text-blue-400 text-lg">8/8</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Water Systems:</span>
            <span className="font-bold text-cyan-400 text-lg">2/2</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">AI Processing:</span>
            <span className="font-bold text-purple-400 text-lg">100%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Drone Fleet:</span>
            <span className="font-bold text-orange-400 text-lg">3/3</span>
          </div>
          <div className="h-px bg-gray-600 my-2"></div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Temperature:</span>
            <span className="font-bold text-yellow-400 text-lg">{defaultSensorData.temperature}°C</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Soil Moisture:</span>
            <span className="font-bold text-teal-400 text-lg">{defaultSensorData.soilMoisture}%</span>
          </div>
        </div>
      </div>
      
      {/* ========================================
          FEATURE LEGEND
          ========================================*/}
      <div className="absolute top-4 right-4 bg-gradient-to-br from-amber-50/90 to-orange-50/90 backdrop-blur-md p-4 rounded-xl shadow-xl border border-orange-200/50 max-w-[220px]">
        <h4 className="font-bold text-orange-800 mb-2 text-sm">🎯 Scene Features</h4>
        <div className="space-y-1 text-xs text-gray-700">
          <div>✓ Complex Polygon Terrain</div>
          <div>✓ 2x Water Tank Systems</div>
          <div>✓ 8x IoT Sensor Array</div>
          <div>✓ AI/ML Processing Unit</div>
          <div>✓ 3x Autonomous Drones</div>
          <div>✓ 6x Farm Fields</div>
          <div>✓ Smart Irrigation Network</div>
        </div>
      </div>
    </div>
  );
}
