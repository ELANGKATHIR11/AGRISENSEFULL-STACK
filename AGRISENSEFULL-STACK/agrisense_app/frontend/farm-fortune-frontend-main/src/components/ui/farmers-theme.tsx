import React from 'react';
import { motion } from 'framer-motion';
import { 
  Sprout, 
  Droplets, 
  Sun, 
  Cloud, 
  Thermometer,
  Gauge,
  Zap,
  Leaf,
  TreePine,
  Wheat
} from 'lucide-react';

// Farmers Theme Color Palette
export const farmersTheme = {
  colors: {
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d'
    },
    earth: {
      50: '#fefdf8',
      100: '#fef7cd',
      200: '#fef08a',
      500: '#eab308',
      600: '#ca8a04',
      700: '#a16207',
      800: '#854d0e'
    },
    sky: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1'
    },
    nature: {
      grass: '#22c55e',
      soil: '#92400e',
      water: '#0ea5e9',
      sun: '#f59e0b',
      leaf: '#16a34a'
    }
  },
  gradients: {
    field: 'from-green-100 via-emerald-50 to-green-100',
    sky: 'from-blue-100 via-sky-50 to-blue-100',
    earth: 'from-yellow-100 via-amber-50 to-yellow-100',
    water: 'from-blue-100 via-cyan-50 to-blue-100'
  }
};

// Animated Farm Icon Component
interface FarmIconProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color?: string;
  size?: number;
  animate?: boolean;
  className?: string;
}

export const FarmIcon: React.FC<FarmIconProps> = ({ 
  icon: Icon, 
  color = farmersTheme.colors.nature.grass,
  size = 24,
  animate = true,
  className = ''
}) => {
  return (
    <motion.div
      className={`inline-flex items-center justify-center ${className}`}
      animate={animate ? {
        rotate: [0, 5, -5, 0],
        scale: [1, 1.1, 1]
      } : {}}
      transition={{
        duration: 2,
        repeat: Infinity,
        repeatType: "reverse",
        ease: "easeInOut"
      }}
    >
      <Icon size={size} color={color} />
    </motion.div>
  );
};

// Weather-based Background Component
interface WeatherBackgroundProps {
  temperature: number;
  humidity: number;
  children: React.ReactNode;
  className?: string;
}

export const WeatherBackground: React.FC<WeatherBackgroundProps> = ({
  temperature,
  humidity,
  children,
  className = ''
}) => {
  // Determine weather condition
  const getWeatherGradient = () => {
    if (temperature > 30) return 'from-orange-100 via-red-50 to-orange-100';
    if (temperature < 15) return 'from-blue-100 via-cyan-50 to-blue-100';
    if (humidity > 70) return 'from-gray-100 via-slate-50 to-gray-100';
    return 'from-green-100 via-emerald-50 to-green-100';
  };

  const getWeatherIcon = () => {
    if (temperature > 30) return Sun;
    if (humidity > 70) return Cloud;
    return Sprout;
  };

  const WeatherIcon = getWeatherIcon();

  return (
    <div className={`relative bg-gradient-to-br ${getWeatherGradient()} ${className}`}>
      {/* Animated Weather Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating weather icons */}
        {Array.from({ length: 3 }, (_, i) => (
          <motion.div
            key={i}
            className="absolute opacity-10"
            style={{
              left: `${20 + i * 30}%`,
              top: `${10 + i * 20}%`
            }}
            animate={{
              y: [0, -10, 0],
              rotate: [0, 5, -5, 0],
              opacity: [0.1, 0.2, 0.1]
            }}
            transition={{
              duration: 3 + i,
              repeat: Infinity,
              delay: i * 0.5
            }}
          >
            <WeatherIcon size={40 + i * 10} />
          </motion.div>
        ))}
      </div>
      
      {children}
    </div>
  );
};

// Farm Status Indicator
interface FarmStatusProps {
  status: 'healthy' | 'warning' | 'critical';
  label: string;
  value: string | number;
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  className?: string;
}

export const FarmStatus: React.FC<FarmStatusProps> = ({
  status,
  label,
  value,
  icon: Icon = Gauge,
  className = ''
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'from-green-100 to-emerald-100 border-green-200 text-green-800';
      case 'warning': return 'from-yellow-100 to-amber-100 border-yellow-200 text-yellow-800';
      case 'critical': return 'from-red-100 to-red-100 border-red-200 text-red-800';
      default: return 'from-gray-100 to-slate-100 border-gray-200 text-gray-800';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy': return '🌱';
      case 'warning': return '⚠️';
      case 'critical': return '🚨';
      default: return '📊';
    }
  };

  return (
    <motion.div
      className={`bg-gradient-to-r ${getStatusColor()} p-4 rounded-lg border-2 ${className}`}
      whileHover={{ scale: 1.05 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getStatusIcon()}</span>
          <Icon size={20} />
        </div>
        <div className="flex-1">
          <div className="text-sm font-medium opacity-80">{label}</div>
          <div className="text-xl font-bold">{value}</div>
        </div>
      </div>
    </motion.div>
  );
};

// Animated Farm Metrics Grid
interface FarmMetricsProps {
  metrics: Array<{
    label: string;
    value: string | number;
    status: 'healthy' | 'warning' | 'critical';
    icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  }>;
  className?: string;
}

export const FarmMetrics: React.FC<FarmMetricsProps> = ({ 
  metrics, 
  className = '' 
}) => {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
      {metrics.map((metric, index) => (
        <motion.div
          key={metric.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <FarmStatus
            status={metric.status}
            label={metric.label}
            value={metric.value}
            icon={metric.icon}
          />
        </motion.div>
      ))}
    </div>
  );
};

// Seasonal Theme Provider
interface SeasonalThemeProps {
  children: React.ReactNode;
  season?: 'spring' | 'summer' | 'autumn' | 'winter';
}

export const SeasonalTheme: React.FC<SeasonalThemeProps> = ({ 
  children, 
  season = 'spring' 
}) => {
  const getSeasonalGradient = () => {
    switch (season) {
      case 'spring': return 'from-green-50 via-emerald-25 to-green-50';
      case 'summer': return 'from-yellow-50 via-orange-25 to-yellow-50';
      case 'autumn': return 'from-orange-50 via-red-25 to-orange-50';
      case 'winter': return 'from-blue-50 via-cyan-25 to-blue-50';
      default: return 'from-green-50 via-emerald-25 to-green-50';
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br ${getSeasonalGradient()}`}>
      {children}
    </div>
  );
};

export default {
  farmersTheme,
  FarmIcon,
  WeatherBackground,
  FarmStatus,
  FarmMetrics,
  SeasonalTheme
};
