import React from 'react';
import CustomMap from './CustomMap';

interface FieldMapProps {
  data: {
    fields?: Array<{
      id: string;
      name: string;
      lat: number;
      lng: number;
      moisture: number;
      temp: number;
    }>;
  };
}

const FieldMap: React.FC<FieldMapProps> = ({ data }) => {
  const center: [number, number] = [27.3, 88.6];
  const zoom = 13;
  
  return (
    <div className="field-map">
      <CustomMap 
        center={center} 
        zoom={zoom} 
        fields={data?.fields || []} 
      />
    </div>
  );
};

export default FieldMap;
