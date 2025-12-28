import React from 'react';
import ArduinoSerialConnection from '@/components/ArduinoSerialConnection';

const Arduino: React.FC = () => {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Arduino Sensor Integration</h1>
        <p className="text-gray-600 mt-2">
          Connect and monitor temperature sensors directly from Arduino Nano via USB cable.
        </p>
      </div>
      
      <ArduinoSerialConnection />
    </div>
  );
};

export default Arduino;