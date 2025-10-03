import React from 'react';

interface LiveStreamCardProps {
  data: any;
}

const LiveStreamCard: React.FC<LiveStreamCardProps> = ({ data }) => {
  return (
    <div className="live-stream-card">
      <h2>Live Sensor Stream</h2>
      
      <div className="sensor-grid">
        {data?.sensors?.map((sensor: any) => (
          <div key={sensor.id} className="sensor-item">
            <div className="sensor-name">{sensor.name}</div>
            <div className="sensor-value">{sensor.value} {sensor.unit}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LiveStreamCard;
