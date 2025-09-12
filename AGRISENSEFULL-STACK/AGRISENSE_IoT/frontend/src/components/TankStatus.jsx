import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8004';

function TankStatus() {
  const [sensorData, setSensorData] = useState(null);
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const sensorRes = await axios.get(`${API_BASE}/sensors/recent?limit=1`);
        if (sensorRes.data.length > 0) setSensorData(sensorRes.data[0]);
        const recoRes = await axios.get(`${API_BASE}/recommend/latest`);
        setRecommendation(recoRes.data);
      } catch (err) { console.error('Error:', err); }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className='bg-white shadow-md rounded-lg p-4 w-full max-w-lg mx-auto mt-6'>
      <h2 className='text-2xl font-bold text-green-700 mb-4'>🌱 Tank & Irrigation Status</h2>
      {sensorData ? (<p>Soil Moisture: {sensorData.soil_moisture}% | Tank: {sensorData.tank_percent}%</p>) : <p>Loading...</p>}
      {recommendation ? (<p>Recommendation: {recommendation.notes}</p>) : <p>Loading recommendation...</p>}
    </div>
  );
}

export default TankStatus;
