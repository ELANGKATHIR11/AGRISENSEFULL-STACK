import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Thermometer, Wifi, WifiOff } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { SerialPort } from '@/types/webserial';

interface ArduinoData {
  temperature: number | null;
  humidity: number | null;
  timestamp: string;
  device_id: string;
}

interface ConnectionStatus {
  connected: boolean;
  port: SerialPort | null;
  error: string | null;
}

export const ArduinoSerialConnection: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    port: null,
    error: null
  });
  const [arduinoData, setArduinoData] = useState<ArduinoData>({
    temperature: null,
    humidity: null,
    timestamp: '',
    device_id: 'ARDUINO_NANO_01'
  });
  const [rawData, setRawData] = useState<string>('');
  const [isReading, setIsReading] = useState(false);
  const readerRef = useRef<ReadableStreamDefaultReader<string> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check if Web Serial API is supported
  const isWebSerialSupported = 'serial' in navigator;

  const connectToArduino = async () => {
    if (!isWebSerialSupported) {
      setConnectionStatus({
        connected: false,
        port: null,
        error: 'Web Serial API not supported in this browser. Use Chrome/Edge.'
      });
      return;
    }

    try {
      // Request Arduino serial port
      interface NavigatorSerial extends Navigator {
        serial: {
          requestPort(options?: { filters?: Array<{ usbVendorId?: number }> }): Promise<SerialPort>;
        };
      }
      const port = await (navigator as NavigatorSerial).serial.requestPort({
        filters: [
          { usbVendorId: 0x2341 }, // Arduino vendor ID
          { usbVendorId: 0x1A86 }, // CH340 chip (common on Arduino clones)
          { usbVendorId: 0x0403 }, // FTDI chip
        ]
      });

      await port.open({ 
        baudRate: 115200, // Match Arduino firmware baud rate
        dataBits: 8,
        stopBits: 1,
        parity: 'none'
      });

      setConnectionStatus({
        connected: true,
        port: port,
        error: null
      });

      startReading(port);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to Arduino';
      setConnectionStatus({
        connected: false,
        port: null,
        error: errorMessage
      });
    }
  };

  const disconnectFromArduino = useCallback(async () => {
    try {
      setIsReading(false);
      
      // Cancel reading
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Close reader
      if (readerRef.current) {
        await readerRef.current.cancel();
        readerRef.current = null;
      }

      // Close port
      if (connectionStatus.port) {
        await connectionStatus.port.close();
      }

      setConnectionStatus({
        connected: false,
        port: null,
        error: null
      });
    } catch (err: unknown) {
      console.error('Error disconnecting:', err);
    }
  }, [connectionStatus.port]);

  const startReading = async (port: SerialPort) => {
    setIsReading(true);
    abortControllerRef.current = new AbortController();

    try {
      const decoder = new TextDecoderStream();
      // Type assertion to handle the stream compatibility
      port.readable!.pipeTo(decoder.writable as WritableStream<Uint8Array>);
      const reader = decoder.readable.getReader();
      readerRef.current = reader;

      // Read loop
      while (isReading && !abortControllerRef.current.signal.aborted) {
        try {
          const { value, done } = await reader.read();
          
          if (done) break;
          
          if (value) {
            setRawData(prev => prev + value);
            parseArduinoData(value.trim());
          }
        } catch (err: unknown) {
          if (err instanceof Error && err.name !== 'AbortError') {
            console.error('Read error:', err);
          }
          break;
        }
      }
    } catch (err: unknown) {
      console.error('Reading error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown reading error';
      setConnectionStatus(prev => ({
        ...prev,
        error: 'Reading error: ' + errorMessage
      }));
    }
  };

  const parseArduinoData = (data: string) => {
    try {
      // Check if data starts with "DATA:" prefix (from our Arduino firmware)
      if (data.startsWith('DATA:')) {
        const jsonStr = data.substring(5); // Remove "DATA:" prefix
        const parsedData = JSON.parse(jsonStr);
        
        // Extract temperature data
        const temperatures = parsedData.temperatures || {};
        const avgTemp = parsedData.avg_temperature;
        const humidity = parsedData.humidity;
        
        setArduinoData({
          temperature: avgTemp || temperatures.ds18b20 || temperatures.dht22 || null,
          humidity: humidity || null,
          timestamp: new Date().toISOString(),
          device_id: parsedData.device_id || 'ARDUINO_NANO_01'
        });
      } else {
        // Try to parse as simple number (for basic Arduino sketches)
        const temp = parseFloat(data);
        if (!isNaN(temp)) {
          setArduinoData(prev => ({
            ...prev,
            temperature: temp,
            timestamp: new Date().toISOString()
          }));
        }
      }
    } catch (err) {
      // If JSON parsing fails, try to extract temperature from raw text
      const tempMatch = data.match(/(\d+\.?\d*)/);
      if (tempMatch) {
        const temp = parseFloat(tempMatch[1]);
        if (!isNaN(temp) && temp > -50 && temp < 100) { // Reasonable temperature range
          setArduinoData(prev => ({
            ...prev,
            temperature: temp,
            timestamp: new Date().toISOString()
          }));
        }
      }
    }
  };

  const sendCommand = async (command: string) => {
    if (connectionStatus.port && connectionStatus.connected) {
      try {
        const writer = connectionStatus.port.writable!.getWriter();
        await writer.write(new TextEncoder().encode(command + '\n'));
        writer.releaseLock();
      } catch (err: unknown) {
        console.error('Error sending command:', err);
      }
    }
  };

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return '--';
    return new Date(timestamp).toLocaleTimeString();
  };

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (connectionStatus.connected) {
        disconnectFromArduino();
      }
    };
  }, [connectionStatus.connected, disconnectFromArduino]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Thermometer className="h-5 w-5" />
            Arduino Temperature Sensor
            {connectionStatus.connected ? (
              <Badge className="bg-green-500">
                <Wifi className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary">
                <WifiOff className="h-3 w-3 mr-1" />
                Disconnected
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isWebSerialSupported && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Web Serial API is not supported in this browser. Please use Chrome, Edge, or another Chromium-based browser.
              </AlertDescription>
            </Alert>
          )}

          {connectionStatus.error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {connectionStatus.error}
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2">
            {!connectionStatus.connected ? (
              <Button 
                onClick={connectToArduino} 
                disabled={!isWebSerialSupported}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Connect to Arduino
              </Button>
            ) : (
              <Button 
                onClick={disconnectFromArduino}
                variant="outline"
              >
                Disconnect
              </Button>
            )}
            
            {connectionStatus.connected && (
              <>
                <Button 
                  onClick={() => sendCommand('READ')}
                  variant="outline"
                  size="sm"
                >
                  Read Sensors
                </Button>
                <Button 
                  onClick={() => sendCommand('STATUS')}
                  variant="outline"
                  size="sm"
                >
                  Get Status
                </Button>
              </>
            )}
          </div>

          {/* Live Sensor Data Display */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {arduinoData.temperature !== null ? `${arduinoData.temperature.toFixed(1)}°C` : '--°C'}
                </div>
                <p className="text-xs text-muted-foreground">Temperature</p>
              </CardContent>
            </Card>

            {arduinoData.humidity !== null && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {`${arduinoData.humidity.toFixed(1)}%`}
                  </div>
                  <p className="text-xs text-muted-foreground">Humidity</p>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent className="pt-6">
                <div className="text-sm font-mono">
                  {formatTimestamp(arduinoData.timestamp)}
                </div>
                <p className="text-xs text-muted-foreground">Last Update</p>
              </CardContent>
            </Card>
          </div>

          {/* Raw Data Debug View */}
          {connectionStatus.connected && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium">Raw Serial Data (Debug)</summary>
              <pre className="mt-2 p-2 bg-gray-100 rounded text-xs max-h-32 overflow-auto font-mono">
                {rawData || 'No data received yet...'}
              </pre>
              <Button 
                onClick={() => setRawData('')}
                variant="outline"
                size="sm"
                className="mt-2"
              >
                Clear Log
              </Button>
            </details>
          )}

          {/* Setup Instructions */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-medium">Arduino Setup Instructions</summary>
            <div className="mt-2 space-y-2 text-sm">
              <p><strong>Hardware Connection:</strong></p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Connect DS18B20: VCC→5V, GND→GND, Data→Pin 2, 4.7kΩ resistor between VCC and Data</li>
                <li>Connect DHT22: VCC→5V, GND→GND, Data→Pin 3, 10kΩ resistor between VCC and Data</li>
                <li>Upload the AgriSense Arduino firmware from AGRISENSE_IoT/arduino_nano_firmware/</li>
                <li>Connect Arduino to computer via USB cable</li>
              </ul>
              <p><strong>Required Libraries:</strong> OneWire, DallasTemperature, DHT sensor library, ArduinoJson</p>
            </div>
          </details>
        </CardContent>
      </Card>
    </div>
  );
};

export default ArduinoSerialConnection;