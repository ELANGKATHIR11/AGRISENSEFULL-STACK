/**
 * Main Dashboard Layout
 * Combines all components into a responsive dashboard interface
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ResponsiveGrid, Card, Tabs, Container, Section, ErrorBoundary } from '../layout/ResponsiveLayout';

// API functions
const fetchDashboardData = async () => {
  const response = await fetch('/api/dashboard/overview');
  if (!response.ok) throw new Error('Failed to fetch dashboard data');
  return response.json();
};

const fetchSystemStatus = async () => {
  const response = await fetch('/api/system/status');
  if (!response.ok) throw new Error('Failed to fetch system status');
  return response.json();
};

// Main Dashboard Component
export const MainDashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  
  const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError } = useQuery({
    queryKey: ['dashboard', selectedTimeRange],
    queryFn: fetchDashboardData,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: systemStatus, isLoading: systemLoading } = useQuery({
    queryKey: ['system-status'],
    queryFn: fetchSystemStatus,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const handleTimeRangeChange = (range: string) => {
    setSelectedTimeRange(range);
  };

  if (dashboardError) {
    return (
      <Container>
        <div className="min-h-screen flex items-center justify-center">
          <Card error="Failed to load dashboard data. Please try again.">
            <div>Please check your connection and try again.</div>
          </Card>
        </div>
      </Container>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <Container>
          <div className="py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AgriSense Dashboard</h1>
              <p className="text-sm text-gray-600">Smart farming insights and monitoring</p>
            </div>
            
            {/* Time Range Selector */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">Time Range:</span>
              <select
                value={selectedTimeRange}
                onChange={(e) => handleTimeRangeChange(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            {/* System Status Indicator */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                systemLoading ? 'bg-yellow-400' : 
                systemStatus?.healthy ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-sm text-gray-700">
                {systemLoading ? 'Checking...' : 
                 systemStatus?.healthy ? 'System Healthy' : 'System Issues'}
              </span>
            </div>
          </div>
        </Container>
      </header>

      {/* Main Content */}
      <main className="py-6">
        <Container size="full">
          <ErrorBoundary>
            <Tabs
              tabs={[
                {
                  id: 'overview',
                  label: 'Overview',
                  badge: systemStatus?.alerts?.length || undefined,
                  content: <OverviewTab loading={dashboardLoading} />
                },
                {
                  id: 'monitoring',
                  label: 'Monitoring',
                  content: <MonitoringTab timeRange={selectedTimeRange} />
                },
                {
                  id: 'analytics',
                  label: 'Analytics',
                  content: <AnalyticsTab timeRange={selectedTimeRange} />
                },
                {
                  id: 'management',
                  label: 'Management',
                  content: <ManagementTab />
                },
                {
                  id: 'settings',
                  label: 'Settings',
                  content: <SettingsTab />
                }
              ]}
              defaultTab="overview"
            />
          </ErrorBoundary>
        </Container>
      </main>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<{ loading: boolean }> = ({ loading }) => {
  return (
    <div className="space-y-6">
      {/* Quick Stats Grid */}
      <ResponsiveGrid cols={{ xs: 1, sm: 2, lg: 4 }} gap={6}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card 
            title="Active Sensors" 
            loading={loading}
            className="text-center"
          >
            <div className="text-3xl font-bold text-green-600">24</div>
            <div className="text-sm text-gray-600">All systems operational</div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card 
            title="Water Saved" 
            loading={loading}
            className="text-center"
          >
            <div className="text-3xl font-bold text-blue-600">1,247L</div>
            <div className="text-sm text-gray-600">This week</div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card 
            title="Crop Health" 
            loading={loading}
            className="text-center"
          >
            <div className="text-3xl font-bold text-emerald-600">95%</div>
            <div className="text-sm text-gray-600">Excellent condition</div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card 
            title="Active Alerts" 
            loading={loading}
            className="text-center"
          >
            <div className="text-3xl font-bold text-amber-600">3</div>
            <div className="text-sm text-gray-600">Require attention</div>
          </Card>
        </motion.div>
      </ResponsiveGrid>

      {/* Main Widgets Grid */}
      <ResponsiveGrid cols={{ xs: 1, lg: 2 }} gap={6}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card title="Sensor Monitoring" loading={loading}>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm">Soil Moisture</span>
                <span className="text-sm font-medium text-blue-600">45%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Temperature</span>
                <span className="text-sm font-medium text-red-600">24°C</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Humidity</span>
                <span className="text-sm font-medium text-green-600">68%</span>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card title="Weather" loading={loading}>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold">24°C</div>
                  <div className="text-sm text-gray-600">Partly Cloudy</div>
                </div>
                <div className="text-4xl">🌤️</div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>Humidity: 68%</div>
                <div>Wind: 12 km/h</div>
                <div>UV Index: 6</div>
                <div>Pressure: 1013 hPa</div>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card title="Crop Recommendations" loading={loading}>
            <div className="space-y-3">
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-sm font-medium text-green-800">Optimal Planting</div>
                <div className="text-xs text-green-600">Tomatoes recommended for current conditions</div>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-sm font-medium text-blue-800">Irrigation Needed</div>
                <div className="text-xs text-blue-600">Zone 2 requires watering in 2 hours</div>
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card title="Active Alerts" loading={loading}>
            <div className="space-y-3">
              <div className="flex items-center p-2 bg-yellow-50 rounded-lg">
                <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></div>
                <div className="text-sm">Low moisture in Zone 1</div>
              </div>
              <div className="flex items-center p-2 bg-red-50 rounded-lg">
                <div className="w-2 h-2 bg-red-400 rounded-full mr-2"></div>
                <div className="text-sm">High temperature alert</div>
              </div>
              <div className="flex items-center p-2 bg-orange-50 rounded-lg">
                <div className="w-2 h-2 bg-orange-400 rounded-full mr-2"></div>
                <div className="text-sm">Maintenance due</div>
              </div>
            </div>
          </Card>
        </motion.div>
      </ResponsiveGrid>
    </div>
  );
};

// Monitoring Tab Component
const MonitoringTab: React.FC<{ timeRange: string }> = ({ timeRange }) => {
  return (
    <div className="space-y-6">
      {/* System Health */}
      <Section>
        <Card title="System Health">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">98%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">24</div>
              <div className="text-sm text-gray-600">Active Sensors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">5.2GB</div>
              <div className="text-sm text-gray-600">Data Stored</div>
            </div>
          </div>
        </Card>
      </Section>

      {/* Sensor Monitoring Grid */}
      <ResponsiveGrid cols={{ xs: 1, lg: 2, xl: 3 }} gap={6}>
        <Card title={`Soil Moisture Trend (${timeRange})`}>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-gray-500">Chart placeholder - Soil moisture over time</div>
          </div>
        </Card>
        
        <Card title="Temperature Gauge">
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-center">
              <div className="text-4xl font-bold text-red-600">24°C</div>
              <div className="text-sm text-gray-600">Current Temperature</div>
            </div>
          </div>
        </Card>
        
        <Card title={`Water Usage (${timeRange})`}>
          <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
            <div className="text-gray-500">Chart placeholder - Water consumption</div>
          </div>
        </Card>
      </ResponsiveGrid>

      {/* Recent Activities */}
      <Section>
        <Card title="Recent Activities">
          <div className="space-y-3">
            {[
              { time: '2 min ago', action: 'Irrigation started in Zone 1', type: 'success' },
              { time: '5 min ago', action: 'Temperature alert resolved', type: 'info' },
              { time: '12 min ago', action: 'Sensor data updated', type: 'neutral' },
              { time: '18 min ago', action: 'Maintenance completed', type: 'success' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-3 ${
                    activity.type === 'success' ? 'bg-green-400' :
                    activity.type === 'info' ? 'bg-blue-400' : 'bg-gray-400'
                  }`} />
                  <span className="text-sm">{activity.action}</span>
                </div>
                <span className="text-xs text-gray-500">{activity.time}</span>
              </div>
            ))}
          </div>
        </Card>
      </Section>
    </div>
  );
};

// Analytics Tab Component
const AnalyticsTab: React.FC<{ timeRange: string }> = ({ timeRange }) => {
  return (
    <div className="space-y-6">
      {/* Farm Analytics */}
      <Section>
        <Card title={`Farm Analytics (${timeRange})`}>
          <ResponsiveGrid cols={{ xs: 1, md: 2, lg: 4 }} gap={4}>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">1,247L</div>
              <div className="text-sm text-gray-600">Water Saved</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">89%</div>
              <div className="text-sm text-gray-600">Efficiency</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">15kg</div>
              <div className="text-sm text-gray-600">Yield Increase</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">$432</div>
              <div className="text-sm text-gray-600">Cost Savings</div>
            </div>
          </ResponsiveGrid>
        </Card>
      </Section>

      {/* Comprehensive Dashboard */}
      <Section>
        <Card title="Performance Metrics">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Water Usage Efficiency</h4>
              <div className="h-48 bg-gray-50 rounded flex items-center justify-center">
                <span className="text-gray-500">Water efficiency chart placeholder</span>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Crop Health Score</h4>
              <div className="h-48 bg-gray-50 rounded flex items-center justify-center">
                <span className="text-gray-500">Health score chart placeholder</span>
              </div>
            </div>
          </div>
        </Card>
      </Section>
    </div>
  );
};

// Management Tab Component
const ManagementTab: React.FC = () => {
  return (
    <div className="space-y-6">
      <ResponsiveGrid cols={{ xs: 1, lg: 2 }} gap={6}>
        <Card title="Irrigation Control" className="min-h-96">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Zone 1 - Tomatoes</span>
              <button className="px-3 py-1 bg-green-600 text-white rounded-md text-sm hover:bg-green-700">
                Start
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Zone 2 - Lettuce</span>
              <button className="px-3 py-1 bg-red-600 text-white rounded-md text-sm hover:bg-red-700">
                Stop
              </button>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Zone 3 - Carrots</span>
              <button className="px-3 py-1 bg-green-600 text-white rounded-md text-sm hover:bg-green-700">
                Start
              </button>
            </div>
          </div>
        </Card>

        <Card title="Schedule Management" className="min-h-96">
          <div className="space-y-4">
            <div className="text-sm">
              <div className="font-medium mb-2">Upcoming Irrigation</div>
              <div className="space-y-2">
                <div className="flex justify-between text-gray-600">
                  <span>Zone 1</span>
                  <span>Today, 6:00 AM</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Zone 3</span>
                  <span>Today, 8:00 AM</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Zone 2</span>
                  <span>Tomorrow, 6:00 AM</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </ResponsiveGrid>
    </div>
  );
};

// Settings Tab Component
const SettingsTab: React.FC = () => {
  return (
    <div className="space-y-6">
      <ResponsiveGrid cols={{ xs: 1, lg: 2 }} gap={6}>
        <Card title="System Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auto-irrigation Threshold
              </label>
              <input
                type="range"
                min="10"
                max="90"
                defaultValue="30"
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>10%</span>
                <span>30%</span>
                <span>90%</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert Notifications
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm">Low moisture alerts</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" defaultChecked className="mr-2" />
                  <span className="text-sm">High temperature warnings</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm">System maintenance reminders</span>
                </label>
              </div>
            </div>
          </div>
        </Card>

        <Card title="User Preferences">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature Unit
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                <option>Celsius (°C)</option>
                <option>Fahrenheit (°F)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Refresh Rate
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                <option>5 seconds</option>
                <option>10 seconds</option>
                <option selected>30 seconds</option>
                <option>1 minute</option>
              </select>
            </div>
          </div>
        </Card>
      </ResponsiveGrid>
    </div>
  );
};

export default MainDashboard;