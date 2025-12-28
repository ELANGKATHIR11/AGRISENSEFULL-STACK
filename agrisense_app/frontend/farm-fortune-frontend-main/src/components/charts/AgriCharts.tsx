/**
 * Reusable Chart Components for AgriSense
 * Data visualization components using Recharts with responsive design
 */
import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  RadialBarChart,
  RadialBar
} from 'recharts';
import { format, parseISO } from 'date-fns';

// Types
interface ChartDataPoint {
  timestamp?: string;
  date?: string;
  value: number;
  label?: string;
  category?: string;
  [key: string]: string | number | undefined;
}

interface BaseChartProps {
  data: ChartDataPoint[];
  height?: number;
  title?: string;
  className?: string;
  loading?: boolean;
  error?: string;
}

interface LineChartProps extends BaseChartProps {
  dataKey: string;
  strokeColor?: string;
  showGrid?: boolean;
  showDots?: boolean;
  timeFormat?: string;
}

interface AreaChartProps extends BaseChartProps {
  dataKey: string;
  fillColor?: string;
  strokeColor?: string;
  gradient?: boolean;
}

interface BarChartProps extends BaseChartProps {
  dataKey: string;
  fillColor?: string;
  horizontal?: boolean;
}

interface PieChartProps extends BaseChartProps {
  dataKey: string;
  labelKey: string;
  colors?: string[];
  showLabels?: boolean;
}

interface ScatterChartProps extends BaseChartProps {
  xDataKey: string;
  yDataKey: string;
  fillColor?: string;
}

// Utility components
const ChartContainer: React.FC<{
  title?: string;
  loading?: boolean;
  error?: string;
  className?: string;
  children: React.ReactNode;
}> = ({ title, loading, error, className, children }) => {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-2 text-gray-600">Loading chart...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
        <div className="flex items-center justify-center h-64 text-red-600">
          <div className="text-center">
            <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.96-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {title && <h3 className="text-lg font-semibold mb-4 text-gray-800">{title}</h3>}
      {children}
    </div>
  );
};

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    color: string;
    unit?: string;
  }>;
  label?: string;
  timeFormat?: string;
}

const CustomTooltip: React.FC<TooltipProps> = ({ active, payload, label, timeFormat = 'PPp' }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">
          {label && (
            typeof label === 'string' && label.includes('T') 
              ? format(parseISO(label), timeFormat)
              : label
          )}
        </p>
        {payload.map((entry, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            <span className="font-medium">{entry.dataKey}:</span> {entry.value}
            {entry.unit && <span className="text-gray-500"> {entry.unit}</span>}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Line Chart Component
export const AgriLineChart: React.FC<LineChartProps> = ({
  data,
  dataKey,
  title,
  height = 300,
  strokeColor = '#10b981',
  showGrid = true,
  showDots = false,
  timeFormat = 'MMM dd HH:mm',
  className,
  loading,
  error
}) => {
  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />}
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(value) => {
              try {
                return format(parseISO(value), 'MMM dd');
              } catch {
                return value;
              }
            }}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip content={<CustomTooltip timeFormat={timeFormat} />} />
          <Line 
            type="monotone" 
            dataKey={dataKey} 
            stroke={strokeColor} 
            strokeWidth={2}
            dot={showDots ? { fill: strokeColor, strokeWidth: 2, r: 4 } : false}
            activeDot={{ r: 6, fill: strokeColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Area Chart Component
export const AgriAreaChart: React.FC<AreaChartProps> = ({
  data,
  dataKey,
  title,
  height = 300,
  fillColor = '#10b981',
  strokeColor = '#059669',
  gradient = true,
  className,
  loading,
  error
}) => {
  const gradientId = `area-gradient-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          {gradient && (
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={fillColor} stopOpacity={0.8}/>
                <stop offset="95%" stopColor={fillColor} stopOpacity={0.1}/>
              </linearGradient>
            </defs>
          )}
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => {
              try {
                return format(parseISO(value), 'MMM dd');
              } catch {
                return value;
              }
            }}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey={dataKey} 
            stroke={strokeColor} 
            strokeWidth={2}
            fill={gradient ? `url(#${gradientId})` : fillColor}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Bar Chart Component
export const AgriBarChart: React.FC<BarChartProps> = ({
  data,
  dataKey,
  title,
  height = 300,
  fillColor = '#10b981',
  horizontal = false,
  className,
  loading,
  error
}) => {
  const ChartComponent = horizontal ? BarChart : BarChart;

  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent 
          data={data} 
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          layout={horizontal ? 'horizontal' : 'vertical'}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis 
            type={horizontal ? 'number' : 'category'} 
            dataKey={horizontal ? undefined : 'label'}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis 
            type={horizontal ? 'category' : 'number'} 
            dataKey={horizontal ? 'label' : undefined}
            stroke="#6b7280"
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey={dataKey} fill={fillColor} radius={[2, 2, 0, 0]} />
        </ChartComponent>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Pie Chart Component
export const AgriPieChart: React.FC<PieChartProps> = ({
  data,
  dataKey,
  labelKey,
  title,
  height = 300,
  colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
  showLabels = true,
  className,
  loading,
  error
}) => {
  const renderLabel = (entry: ChartDataPoint) => {
    if (!showLabels) return '';
    const total = data.reduce((sum, item) => sum + (typeof item[dataKey] === 'number' ? item[dataKey] : 0), 0);
    const entryValue = typeof entry[dataKey] === 'number' ? entry[dataKey] : 0;
    const percent = ((entryValue / total) * 100).toFixed(1);
    return `${entry[labelKey] || 'Unknown'}: ${percent}%`;
  };

  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderLabel}
            outerRadius={Math.min(height * 0.35, 120)}
            fill="#8884d8"
            dataKey={dataKey}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Scatter Chart Component
export const AgriScatterChart: React.FC<ScatterChartProps> = ({
  data,
  xDataKey,
  yDataKey,
  title,
  height = 300,
  fillColor = '#10b981',
  className,
  loading,
  error
}) => {
  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis type="number" dataKey={xDataKey} stroke="#6b7280" fontSize={12} />
          <YAxis type="number" dataKey={yDataKey} stroke="#6b7280" fontSize={12} />
          <Tooltip content={<CustomTooltip />} />
          <Scatter dataKey="value" fill={fillColor} />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Gauge Chart Component
export const AgriGaugeChart: React.FC<{
  value: number;
  max?: number;
  title?: string;
  unit?: string;
  color?: string;
  height?: number;
  className?: string;
}> = ({
  value,
  max = 100,
  title,
  unit = '',
  color = '#10b981',
  height = 200,
  className
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  const data = [{ name: 'value', value: percentage, fill: color }];

  return (
    <ChartContainer title={title} className={className}>
      <div className="flex flex-col items-center">
        <ResponsiveContainer width="100%" height={height}>
          <RadialBarChart 
            cx="50%" 
            cy="50%" 
            innerRadius="60%" 
            outerRadius="80%" 
            barSize={10} 
            data={data}
            startAngle={180}
            endAngle={0}
          >
            <RadialBar dataKey="value" cornerRadius={10} fill={color} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="text-center mt-2">
          <div className="text-2xl font-bold text-gray-800">
            {value.toFixed(1)}{unit}
          </div>
          <div className="text-sm text-gray-600">
            of {max}{unit}
          </div>
        </div>
      </div>
    </ChartContainer>
  );
};

// Multi-line Chart Component
export const AgriMultiLineChart: React.FC<{
  data: ChartDataPoint[];
  lines: Array<{
    dataKey: string;
    color: string;
    name: string;
  }>;
  title?: string;
  height?: number;
  className?: string;
  loading?: boolean;
  error?: string;
}> = ({
  data,
  lines,
  title,
  height = 300,
  className,
  loading,
  error
}) => {
  return (
    <ChartContainer title={title} loading={loading} error={error} className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => {
              try {
                return format(parseISO(value), 'MMM dd');
              } catch {
                return value;
              }
            }}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {lines.map((line, index) => (
            <Line
              key={index}
              type="monotone"
              dataKey={line.dataKey}
              stroke={line.color}
              strokeWidth={2}
              name={line.name}
              dot={false}
              activeDot={{ r: 6, fill: line.color }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};