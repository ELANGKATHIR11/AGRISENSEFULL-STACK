import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, PerspectiveCamera, Environment, ContactShadows } from '@react-three/drei';
import { useRef, useState } from 'react';
import * as THREE from 'three';

// Comparison data: AgriSense vs Traditional Farming
const comparisonData = {
  waterUsage: {
    traditional: 100, // 100% baseline
    agrisense: 35, // 65% reduction
    unit: 'Water Usage (L/day)',
    color1: '#93c5fd', // traditional - light blue
    color2: '#3b82f6', // agrisense - blue
  },
  costUsage: {
    traditional: 100, // 100% baseline
    agrisense: 42, // 58% reduction
    unit: 'Operating Costs ($/month)',
    color1: '#fca5a5', // traditional - light red
    color2: '#ef4444', // agrisense - red
  },
  fertilizerUsage: {
    traditional: 100, // 100% baseline
    agrisense: 48, // 52% reduction
    unit: 'Fertilizer Usage (kg/month)',
    color1: '#fde047', // traditional - light yellow
    color2: '#eab308', // agrisense - yellow
  },
};

// Animated 3D Bar Component
function AnimatedBar({ 
  height, 
  color, 
  position, 
  label, 
  value, 
  delay = 0 
}: { 
  height: number; 
  color: string; 
  position: [number, number, number]; 
  label: string; 
  value: number; 
  delay?: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [currentHeight, setCurrentHeight] = useState(0);
  const targetHeight = height;

  useFrame((state) => {
    if (meshRef.current) {
      const time = state.clock.getElapsedTime() - delay;
      if (time > 0) {
        const progress = Math.min(time / 2, 1); // 2 second animation
        const easedProgress = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const newHeight = targetHeight * easedProgress;
        setCurrentHeight(newHeight);
        meshRef.current.scale.y = easedProgress;
        
        // Gentle floating animation
        meshRef.current.position.y = position[1] + newHeight / 2 + Math.sin(state.clock.getElapsedTime() * 0.5 + delay) * 0.05;
      }
    }
  });

  return (
    <group position={position}>
      {/* Bar */}
      <mesh ref={meshRef} castShadow receiveShadow>
        <boxGeometry args={[0.8, height, 0.8]} />
        <meshStandardMaterial 
          color={color} 
          metalness={0.3} 
          roughness={0.4} 
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>
      
      {/* Base platform */}
      <mesh position={[0, -0.05, 0]} receiveShadow>
        <cylinderGeometry args={[0.5, 0.5, 0.1, 32]} />
        <meshStandardMaterial color="#374151" metalness={0.7} roughness={0.3} />
      </mesh>
      
      {/* Value text on top */}
      <Text
        position={[0, height + 0.3, 0]}
        fontSize={0.25}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        {`${Math.round(value)}%`}
      </Text>
      
      {/* Label at bottom */}
      <Text
        position={[0, -0.4, 0]}
        fontSize={0.18}
        color="#1f2937"
        anchorX="center"
        anchorY="middle"
        maxWidth={1.5}
      >
        {label}
      </Text>
    </group>
  );
}

// 3D Line Chart for trend comparison
function LineChart3D({ position }: { position: [number, number, number] }) {
  const groupRef = useRef<THREE.Group>(null);
  const [points] = useState<THREE.Vector3[]>(() => {
    // Generate trend line points (showing improvement over time)
    const pts: THREE.Vector3[] = [];
    const months = 12;
    for (let i = 0; i <= months; i++) {
      const x = (i / months) * 4 - 2; // -2 to 2 range
      const y = Math.max(0.5, 3 - (i / months) * 2.5); // Declining trend from 3 to 0.5
      const z = 0;
      pts.push(new THREE.Vector3(x, y, z));
    }
    return pts;
  });

  const [traditionalPoints] = useState<THREE.Vector3[]>(() => {
    // Traditional farming - relatively flat, high usage
    const pts: THREE.Vector3[] = [];
    const months = 12;
    for (let i = 0; i <= months; i++) {
      const x = (i / months) * 4 - 2;
      const y = 2.8 + Math.sin(i * 0.5) * 0.2; // Slight variation but stays high
      const z = 0.2;
      pts.push(new THREE.Vector3(x, y, z));
    }
    return pts;
  });

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.getElapsedTime() * 0.2) * 0.1;
    }
  });

  return (
    <group position={position} ref={groupRef}>
      {/* AgriSense trend line (green, declining) */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={new Float32Array(points.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#22c55e" linewidth={3} />
      </line>
      
      {/* Traditional farming line (red, stable high) */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={traditionalPoints.length}
            array={new Float32Array(traditionalPoints.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#ef4444" linewidth={3} />
      </line>
      
      {/* Data points on lines */}
      {points.map((point, i) => (
        <mesh key={`green-${i}`} position={[point.x, point.y, point.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#22c55e" emissive="#22c55e" emissiveIntensity={0.5} />
        </mesh>
      ))}
      
      {traditionalPoints.map((point, i) => (
        <mesh key={`red-${i}`} position={[point.x, point.y, point.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.5} />
        </mesh>
      ))}
      
      {/* Chart title */}
      <Text
        position={[0, 3.5, 0]}
        fontSize={0.22}
        color="#1f2937"
        anchorX="center"
        anchorY="middle"
        fontWeight={700}
      >
        Resource Efficiency Over Time
      </Text>
      
      {/* Legend */}
      <group position={[-1.5, 3.2, 0]}>
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#22c55e" />
        </mesh>
        <Text position={[0.3, 0, 0]} fontSize={0.12} color="#1f2937" anchorX="left">
          AgriSense
        </Text>
      </group>
      
      <group position={[0.5, 3.2, 0]}>
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#ef4444" />
        </mesh>
        <Text position={[0.3, 0, 0]} fontSize={0.12} color="#1f2937" anchorX="left">
          Traditional
        </Text>
      </group>
      
      {/* Grid */}
      <gridHelper args={[4, 10, '#94a3b8', '#e2e8f0']} position={[0, 0, 0]} />
    </group>
  );
}

// 3D Pie Chart showing savings
function PieChart3D({ position }: { position: [number, number, number] }) {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.15;
    }
  });

  const segments = [
    { percentage: 65, color: '#3b82f6', label: 'Water Saved' },
    { percentage: 58, color: '#ef4444', label: 'Cost Saved' },
    { percentage: 52, color: '#eab308', label: 'Fertilizer Saved' },
  ];

  let currentAngle = 0;

  return (
    <group position={position} ref={groupRef}>
      {segments.map((segment, index) => {
        const angle = (segment.percentage / 100) * Math.PI * 2;
        const middleAngle = currentAngle + angle / 2;
        const startAngle = currentAngle;
        currentAngle += angle;

        return (
          <group key={index}>
            {/* Pie slice */}
            <mesh
              rotation={[Math.PI / 2, 0, startAngle]}
              position={[
                Math.cos(middleAngle) * 0.1,
                0,
                Math.sin(middleAngle) * 0.1,
              ]}
            >
              <cylinderGeometry args={[0, 1.2, 0.3, 32, 1, false, 0, angle]} />
              <meshStandardMaterial
                color={segment.color}
                metalness={0.3}
                roughness={0.4}
                emissive={segment.color}
                emissiveIntensity={0.3}
              />
            </mesh>
            
            {/* Label */}
            <Text
              position={[
                Math.cos(middleAngle) * 1.8,
                0,
                Math.sin(middleAngle) * 1.8,
              ]}
              fontSize={0.16}
              color="#1f2937"
              anchorX="center"
              anchorY="middle"
            >
              {`${segment.label}\n${segment.percentage}%`}
            </Text>
          </group>
        );
      })}
      
      {/* Center circle */}
      <mesh>
        <cylinderGeometry args={[0.4, 0.4, 0.35, 32]} />
        <meshStandardMaterial color="#ffffff" metalness={0.5} roughness={0.3} />
      </mesh>
      
      {/* Title */}
      <Text
        position={[0, 1.5, 0]}
        fontSize={0.22}
        color="#1f2937"
        anchorX="center"
        anchorY="middle"
        fontWeight={700}
      >
        Average Savings with AgriSense
      </Text>
    </group>
  );
}

// Main 3D Comparison Scene
function ComparisonScene() {
  console.log('🎨 ComparisonScene rendering...');
  
  return (
    <>
      <color attach="background" args={['#e0f2fe']} />
      
      <PerspectiveCamera makeDefault position={[0, 3, 8]} fov={60} />
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={5}
        maxDistance={15}
        maxPolarAngle={Math.PI / 2.1}
        autoRotate={true}
        autoRotateSpeed={0.5}
      />

      {/* Lighting */}
      <ambientLight intensity={0.8} />
      <directionalLight position={[5, 5, 5]} intensity={1.5} castShadow />
      <directionalLight position={[-5, 5, -5]} intensity={0.8} />
      <pointLight position={[0, 3, 0]} intensity={1} color="#ffffff" />
      
      <Environment preset="city" />
      
      {/* Test cube to verify rendering */}
      <mesh position={[0, 1, 0]}>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial color="red" />
      </mesh>

      {/* Water Usage Comparison - Left */}
      <group position={[-6, 0, 2]}>
        <AnimatedBar
          height={3}
          color={comparisonData.waterUsage.color1}
          position={[-0.6, 0, 0]}
          label="Traditional"
          value={comparisonData.waterUsage.traditional}
          delay={0}
        />
        <AnimatedBar
          height={1.05}
          color={comparisonData.waterUsage.color2}
          position={[0.6, 0, 0]}
          label="AgriSense"
          value={comparisonData.waterUsage.agrisense}
          delay={0.3}
        />
        
        {/* Category Title */}
        <Text
          position={[0, 3.8, 0]}
          fontSize={0.28}
          color="#1e40af"
          anchorX="center"
          anchorY="middle"
          fontWeight={700}
        >
          💧 Water Usage
        </Text>
        
        {/* Savings Badge */}
        <mesh position={[0, 2.2, 0]}>
          <cylinderGeometry args={[0.5, 0.5, 0.15, 32]} />
          <meshStandardMaterial color="#22c55e" metalness={0.5} roughness={0.3} />
        </mesh>
        <Text position={[0, 2.2, 0.08]} fontSize={0.18} color="#ffffff" anchorX="center">
          -65%
        </Text>
      </group>

      {/* Cost Usage Comparison - Center */}
      <group position={[0, 0, 2]}>
        <AnimatedBar
          height={3}
          color={comparisonData.costUsage.color1}
          position={[-0.6, 0, 0]}
          label="Traditional"
          value={comparisonData.costUsage.traditional}
          delay={0.6}
        />
        <AnimatedBar
          height={1.26}
          color={comparisonData.costUsage.color2}
          position={[0.6, 0, 0]}
          label="AgriSense"
          value={comparisonData.costUsage.agrisense}
          delay={0.9}
        />
        
        {/* Category Title */}
        <Text
          position={[0, 3.8, 0]}
          fontSize={0.28}
          color="#dc2626"
          anchorX="center"
          anchorY="middle"
          fontWeight={700}
        >
          💰 Operating Costs
        </Text>
        
        {/* Savings Badge */}
        <mesh position={[0, 2.2, 0]}>
          <cylinderGeometry args={[0.5, 0.5, 0.15, 32]} />
          <meshStandardMaterial color="#22c55e" metalness={0.5} roughness={0.3} />
        </mesh>
        <Text position={[0, 2.2, 0.08]} fontSize={0.18} color="#ffffff" anchorX="center">
          -58%
        </Text>
      </group>

      {/* Fertilizer Usage Comparison - Right */}
      <group position={[6, 0, 2]}>
        <AnimatedBar
          height={3}
          color={comparisonData.fertilizerUsage.color1}
          position={[-0.6, 0, 0]}
          label="Traditional"
          value={comparisonData.fertilizerUsage.traditional}
          delay={1.2}
        />
        <AnimatedBar
          height={1.44}
          color={comparisonData.fertilizerUsage.color2}
          position={[0.6, 0, 0]}
          label="AgriSense"
          value={comparisonData.fertilizerUsage.agrisense}
          delay={1.5}
        />
        
        {/* Category Title */}
        <Text
          position={[0, 3.8, 0]}
          fontSize={0.28}
          color="#ca8a04"
          anchorX="center"
          anchorY="middle"
          fontWeight={700}
        >
          🌿 Fertilizer Usage
        </Text>
        
        {/* Savings Badge */}
        <mesh position={[0, 2.2, 0]}>
          <cylinderGeometry args={[0.5, 0.5, 0.15, 32]} />
          <meshStandardMaterial color="#22c55e" metalness={0.5} roughness={0.3} />
        </mesh>
        <Text position={[0, 2.2, 0.08]} fontSize={0.18} color="#ffffff" anchorX="center">
          -52%
        </Text>
      </group>

      {/* Line Chart - Back Left */}
      <LineChart3D position={[-6, 0, -3]} />

      {/* Pie Chart - Back Right */}
      <PieChart3D position={[6, 0.3, -3]} />

      {/* Main Title */}
      <Text
        position={[0, 5, 0]}
        fontSize={0.5}
        color="#059669"
        anchorX="center"
        anchorY="middle"
        fontWeight={700}
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        AgriSense vs Traditional Farming
      </Text>

      {/* Ground plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.2, 0]} receiveShadow>
        <planeGeometry args={[30, 20]} />
        <meshStandardMaterial color="#f1f5f9" metalness={0.1} roughness={0.9} />
      </mesh>

      {/* Contact Shadows */}
      <ContactShadows
        position={[0, -0.19, 0]}
        opacity={0.5}
        scale={30}
        blur={2}
        far={10}
      />
    </>
  );
}

// Main Component Export
export default function ComparisonCharts3D() {
  return (
    <div className="w-full h-[600px] rounded-xl overflow-hidden shadow-2xl bg-gradient-to-br from-green-50 to-blue-50">
      <Canvas shadows dpr={[1, 2]} gl={{ antialias: true }}>
        <ComparisonScene />
      </Canvas>
    </div>
  );
}
