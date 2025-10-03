/**
 * Data Visualization Widgets for AgriSense Dashboard
 * Ready-to-use widgets for sensor data, recommendations, and analytics
 */
import React, { useState, useEffect } from 'react';
import { 
  AgriLineChart, 
  AgriAreaChart, 
  AgriBarChart, 
  AgriPieChart, 
  AgriGaugeChart, 
  AgriMultiLineChart 
} from '../charts/AgriCharts';
import { useQuery } from '@tanstack/react-query';

// Types
interface SensorReading {
  timestamp: string;
  temperature: number;
  humidity: number;
  soilMoisture: number;
  ph: number;
  light: number;
  zone_id: string;
}

interface RecommendationData {
  timestamp: string;
  water_liters: number;
  fertilizer_n: number;
  fertilizer_p: number;
  fertilizer_k: number;
  crop_type: string;
  zone_id: string;
}

interface AlertData {
  timestamp: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  zone_id: string;
}

// Data fetching hooks
const useSensorData = (zoneId: string, timeRange: string = '24h') => {
  return useQuery({
    queryKey: ['sensorData', zoneId, timeRange],
    queryFn: async () => {
      const response = await fetch(`/api/sensors/history?zone_id=${zoneId}&range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch sensor data');
      return response.json();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

const useRecommendationData = (zoneId: string, timeRange: string = '7d') => {
  return useQuery({
    queryKey: ['recommendations', zoneId, timeRange],
    queryFn: async () => {
      const response = await fetch(`/api/recommendations/history?zone_id=${zoneId}&range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch recommendation data');
      return response.json();
    },
    refetchInterval: 60000, // Refetch every minute
  });
};

const useAlertData = (timeRange: string = '7d') => {
  return useQuery({
    queryKey: ['alerts', timeRange],
    queryFn: async () => {
      const response = await fetch(`/api/alerts?range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch alert data');
      return response.json();
    },
    refetchInterval: 30000,
  });
};

// Widget Components

// Sensor Monitoring Widget
export const SensorMonitoringWidget: React.FC<{
  zoneId: string;
  timeRange?: string;
  className?: string;
}> = ({ zoneId, timeRange = '24h', className }) => {
  const { data: sensorData, isLoading, error } = useSensorData(zoneId, timeRange);

  if (!sensorData?.readings) {
    return (
      <AgriMultiLineChart
        data={[]}
        lines={[]}
        title="Sensor Monitoring"
        loading={isLoading}
        error={error?.message}
        className={className}
      />
    );
  }

  const chartData = sensorData.readings.map((reading: SensorReading) => ({
    timestamp: reading.timestamp,
    temperature: reading.temperature,
    humidity: reading.humidity,
    soilMoisture: reading.soilMoisture,
    light: reading.light,
  }));

  const lines = [
    { dataKey: 'temperature', color: '#ef4444', name: 'Temperature (°C)' },
    { dataKey: 'humidity', color: '#3b82f6', name: 'Humidity (%)' },
    { dataKey: 'soilMoisture', color: '#10b981', name: 'Soil Moisture (%)' },
    { dataKey: 'light', color: '#f59e0b', name: 'Light Level' },
  ];

  return (
    <AgriMultiLineChart
      data={chartData}
      lines={lines}
      title={`Sensor Monitoring - Zone ${zoneId}`}
      loading={isLoading}
      error={error?.message}
      className={className}
    />
  );
};

// Soil Moisture Trend Widget
export const SoilMoistureTrendWidget: React.FC<{
  zoneId: string;
  timeRange?: string;
  className?: string;
}> = ({ zoneId, timeRange = '7d', className }) => {
  const { data: sensorData, isLoading, error } = useSensorData(zoneId, timeRange);

  const chartData = sensorData?.readings?.map((reading: SensorReading) => ({
    timestamp: reading.timestamp,
    value: reading.soilMoisture,
  })) || [];

  return (
    <AgriAreaChart
      data={chartData}
      dataKey="value"
      title="Soil Moisture Trend"
      fillColor="#10b981"
      strokeColor="#059669"
      gradient={true}
      loading={isLoading}
      error={error?.message}
      className={className}
    />
  );
};

// Temperature Gauge Widget
export const TemperatureGaugeWidget: React.FC<{
  zoneId: string;
  className?: string;
}> = ({ zoneId, className }) => {
  const { data: sensorData, isLoading, error } = useSensorData(zoneId, '1h');

  const latestReading = sensorData?.readings?.[sensorData.readings.length - 1];
  const temperature = latestReading?.temperature || 0;

  if (isLoading || error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold mb-4">Current Temperature</h3>
        <div className="flex items-center justify-center h-48">
          {isLoading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          ) : (
            <p className="text-red-600">Error loading data</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <AgriGaugeChart
      value={temperature}
      max={50}
      title="Current Temperature"
      unit="°C"
      color={temperature > 35 ? '#ef4444' : temperature > 25 ? '#f59e0b' : '#10b981'}
      className={className}
    />
  );
};

// Water Usage Chart Widget
export const WaterUsageWidget: React.FC<{
  zoneId: string;
  timeRange?: string;
  className?: string;
}> = ({ zoneId, timeRange = '7d', className }) => {
  const { data: recData, isLoading, error } = useRecommendationData(zoneId, timeRange);

  const chartData = recData?.recommendations?.map((rec: RecommendationData) => ({
    timestamp: rec.timestamp,
    value: rec.water_liters,
  })) || [];

  return (
    <AgriBarChart
      data={chartData}
      dataKey="value"
      title="Water Usage Recommendations"
      fillColor="#3b82f6"
      loading={isLoading}
      error={error?.message}
      className={className}
    />
  );
};

// Fertilizer Distribution Widget
export const FertilizerDistributionWidget: React.FC<{
  zoneId: string;
  timeRange?: string;
  className?: string;
}> = ({ zoneId, timeRange = '30d', className }) => {
  const { data: recData, isLoading, error } = useRecommendationData(zoneId, timeRange);

  if (!recData?.recommendations) {
    return (
      <AgriPieChart
        data={[]}
        dataKey="value"
        labelKey="label"
        title="Fertilizer Distribution"
        loading={isLoading}
        error={error?.message}
        className={className}
      />
    );
  }

  const totalN = recData.recommendations.reduce((sum: number, rec: RecommendationData) => sum + rec.fertilizer_n, 0);
  const totalP = recData.recommendations.reduce((sum: number, rec: RecommendationData) => sum + rec.fertilizer_p, 0);
  const totalK = recData.recommendations.reduce((sum: number, rec: RecommendationData) => sum + rec.fertilizer_k, 0);

  const chartData = [
    { label: 'Nitrogen (N)', value: totalN },
    { label: 'Phosphorus (P)', value: totalP },
    { label: 'Potassium (K)', value: totalK },
  ];

  return (
    <AgriPieChart
      data={chartData}
      dataKey="value"
      labelKey="label"
      title="Fertilizer Distribution (30 days)"
      colors={['#10b981', '#3b82f6', '#f59e0b']}
      loading={isLoading}
      error={error?.message}
      className={className}
    />
  );
};

// Alert Summary Widget
export const AlertSummaryWidget: React.FC<{
  timeRange?: string;
  className?: string;
}> = ({ timeRange = '7d', className }) => {
  const { data: alertData, isLoading, error } = useAlertData(timeRange);

  if (!alertData?.alerts) {
    return (
      <AgriBarChart
        data={[]}
        dataKey="count"
        title="Alert Summary"
        loading={isLoading}
        error={error?.message}
        className={className}
      />
    );
  }

  const alertCounts = alertData.alerts.reduce((acc: Record<string, number>, alert: AlertData) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1;
    return acc;
  }, {});

  const chartData = Object.entries(alertCounts).map(([severity, count]) => ({
    label: severity.charAt(0).toUpperCase() + severity.slice(1),
    value: 0, // Required by ChartDataPoint interface
    count: count as number,
  }));

  return (
    <AgriBarChart
      data={chartData}
      dataKey="count"
      title={`Alert Summary (${timeRange})`}
      fillColor="#ef4444"
      className={className}
    />
  );
};

// Environmental Conditions Widget
export const EnvironmentalConditionsWidget: React.FC<{
  zoneId: string;
  className?: string;
}> = ({ zoneId, className }) => {
  const { data: sensorData, isLoading, error } = useSensorData(zoneId, '1h');

  const latestReading = sensorData?.readings?.[sensorData.readings.length - 1];

  if (isLoading || error || !latestReading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold mb-4">Current Conditions</h3>
        <div className="flex items-center justify-center h-32">
          {isLoading ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          ) : (
            <p className="text-red-600">{error?.message || 'No data available'}</p>
          )}
        </div>
      </div>
    );
  }

  const conditions = [
    {
      label: 'Temperature',
      value: `${latestReading.temperature.toFixed(1)}°C`,
      color: latestReading.temperature > 35 ? 'text-red-600' : latestReading.temperature > 25 ? 'text-yellow-600' : 'text-green-600',
      icon: '🌡️'
    },
    {
      label: 'Humidity',
      value: `${latestReading.humidity.toFixed(1)}%`,
      color: latestReading.humidity < 30 ? 'text-red-600' : latestReading.humidity > 70 ? 'text-blue-600' : 'text-green-600',
      icon: '💧'
    },
    {
      label: 'Soil Moisture',
      value: `${latestReading.soilMoisture.toFixed(1)}%`,
      color: latestReading.soilMoisture < 30 ? 'text-red-600' : latestReading.soilMoisture > 80 ? 'text-blue-600' : 'text-green-600',
      icon: '🌱'
    },
    {
      label: 'pH Level',
      value: latestReading.ph.toFixed(1),
      color: latestReading.ph < 6.0 || latestReading.ph > 8.0 ? 'text-red-600' : 'text-green-600',
      icon: '⚗️'
    },
  ];

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Current Conditions - Zone {zoneId}</h3>
      <div className="grid grid-cols-2 gap-4">
        {conditions.map((condition, index) => (
          <div key={index} className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl mb-1">{condition.icon}</div>
            <div className="text-sm font-medium text-gray-600">{condition.label}</div>
            <div className={`text-lg font-bold ${condition.color}`}>{condition.value}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-xs text-gray-500 text-center">
        Last updated: {new Date(latestReading.timestamp).toLocaleString()}
      </div>
    </div>
  );
};

// Comprehensive Dashboard Widget
export const ComprehensiveDashboard: React.FC<{
  zoneId: string;
  className?: string;
}> = ({ zoneId, className }) => {
  const [timeRange, setTimeRange] = useState('24h');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Time Range Selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">Farm Analytics Dashboard</h2>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Current Conditions and Gauges */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <EnvironmentalConditionsWidget zoneId={zoneId} />
        <TemperatureGaugeWidget zoneId={zoneId} />
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <button className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
              Manual Irrigation
            </button>
            <button className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700">
              Get Recommendation
            </button>
            <button className="w-full bg-yellow-600 text-white py-2 px-4 rounded hover:bg-yellow-700">
              View Alerts
            </button>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <SensorMonitoringWidget zoneId={zoneId} timeRange={timeRange} />
        <SoilMoistureTrendWidget zoneId={zoneId} timeRange={timeRange} />
        <WaterUsageWidget zoneId={zoneId} timeRange={timeRange} />
        <FertilizerDistributionWidget zoneId={zoneId} timeRange="30d" />
      </div>

      {/* Alert Summary */}
      <AlertSummaryWidget timeRange={timeRange} />
    </div>
  );
};