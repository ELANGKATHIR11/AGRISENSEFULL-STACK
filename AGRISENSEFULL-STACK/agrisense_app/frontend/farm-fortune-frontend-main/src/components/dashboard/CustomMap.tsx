import React, { useRef, useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface CustomMapProps {
  center: [number, number];
  zoom: number;
  fields: Array<{
    id: string;
    name: string;
    lat: number;
    lng: number;
    moisture: number;
    temp: number;
  }>;
}

const CustomMap: React.FC<CustomMapProps> = ({ center, zoom, fields }) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mapContainerRef.current && !mapRef.current) {
      // Initialize map
      mapRef.current = L.map(mapContainerRef.current).setView(center, zoom);
      
      // Add tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(mapRef.current);
      
      // Add markers
      fields.forEach(field => {
        L.marker([field.lat, field.lng])
          .bindPopup(`
            <div>
              <h3>${field.name}</h3>
              <p>Moisture: ${field.moisture}%</p>
              <p>Temperature: ${field.temp}°C</p>
            </div>
          `)
          .addTo(mapRef.current!);
      });
    }
    
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [center, zoom, fields]);

  return <div ref={mapContainerRef} style={{ height: '100%', width: '100%' }} />;
};

export default CustomMap;
