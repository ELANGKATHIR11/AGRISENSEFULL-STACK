import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Type definitions
interface WebSocketMessage {
  channel?: string;
  payload?: unknown;
  type?: string;
  timestamp?: string;
}

interface SensorData {
  temperature?: number;
  humidity?: number;
  soilMoisture?: number;
  ph?: number;
  timestamp?: string;
}

interface AlertData {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  timestamp: string;
}

// Create React Query client with optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: unknown) => {
        const errorObj = error as { status?: number };
        if (errorObj?.status === 404 || errorObj?.status === 401) return false;
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// WebSocket context for real-time updates
interface WebSocketContextType {
  socket: WebSocket | null;
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: WebSocketMessage) => void;
  subscribe: (channel: string, callback: (data: unknown) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  url?: string;
  children: React.ReactNode;
}

export function WebSocketProvider({ 
  url = `ws://${window.location.hostname}:8004/ws`,
  children 
}: WebSocketProviderProps) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [subscribers] = useState<Map<string, Set<(data: unknown) => void>>>(new Map());

  // Initialize WebSocket connection
  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: number;

    const connect = () => {
      try {
        ws = new WebSocket(url);
        
        ws.onopen = () => {
          console.log('✅ WebSocket connected');
          setIsConnected(true);
          setSocket(ws);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WebSocketMessage;
            setLastMessage(data);
            
            // Notify channel subscribers
            if (data.channel && subscribers.has(data.channel)) {
              const channelSubs = subscribers.get(data.channel);
              channelSubs?.forEach(callback => callback(data.payload));
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('🔌 WebSocket disconnected');
          setIsConnected(false);
          setSocket(null);
          
          // Attempt to reconnect after 3 seconds
          reconnectTimeout = window.setTimeout(connect, 3000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        // Retry connection after 5 seconds
        reconnectTimeout = window.setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [url, subscribers]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, [socket]);

  const subscribe = useCallback((channel: string, callback: (data: unknown) => void) => {
    if (!subscribers.has(channel)) {
      subscribers.set(channel, new Set());
    }
    subscribers.get(channel)!.add(callback);

    // Return unsubscribe function
    return () => {
      const channelSubs = subscribers.get(channel);
      if (channelSubs) {
        channelSubs.delete(callback);
        if (channelSubs.size === 0) {
          subscribers.delete(channel);
        }
      }
    };
  }, [subscribers]);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    lastMessage,
    sendMessage,
    subscribe,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Hook to use WebSocket context
export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

// Hook for real-time sensor data
export function useLiveSensorData() {
  const { subscribe } = useWebSocket();
  const [sensorData, setSensorData] = useState<SensorData | null>(null);

  useEffect(() => {
    const unsubscribe = subscribe('sensor_data', (data) => {
      setSensorData(data as SensorData);
    });

    return unsubscribe;
  }, [subscribe]);

  return sensorData;
}

// Hook for real-time alerts
export function useLiveAlerts() {
  const { subscribe } = useWebSocket();
  const [alerts, setAlerts] = useState<AlertData[]>([]);

  useEffect(() => {
    const unsubscribe = subscribe('alerts', (data) => {
      setAlerts(prev => [data as AlertData, ...prev.slice(0, 9)]); // Keep last 10 alerts
    });

    return unsubscribe;
  }, [subscribe]);

  return alerts;
}

// Hook for tank level updates
export function useLiveTankLevel() {
  const { subscribe } = useWebSocket();
  const [tankLevel, setTankLevel] = useState<number | null>(null);

  useEffect(() => {
    const unsubscribe = subscribe('tank_level', (data) => {
      const levelData = data as { level: number };
      setTankLevel(levelData.level);
    });

    return unsubscribe;
  }, [subscribe]);

  return tankLevel;
}

// Enhanced API hooks with optimistic updates
export function useOptimisticMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
    invalidateQueries?: string[];
  }
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      // Invalidate and refetch relevant queries
      options?.invalidateQueries?.forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey: [queryKey] });
      });
      
      options?.onSuccess?.(data, variables);
    },
    onError: options?.onError,
  });
}

// Main provider component
interface AgriSenseProvidersProps {
  children: React.ReactNode;
}

export function AgriSenseProviders({ children }: AgriSenseProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        {children}
      </WebSocketProvider>
    </QueryClientProvider>
  );
}

export { queryClient };