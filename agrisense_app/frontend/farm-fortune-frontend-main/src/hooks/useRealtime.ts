import { useState, useEffect } from 'react';
import axios from 'axios';

const useRealtime = () => {
  const [realtimeData, setRealtimeData] = useState<any>(null);

  useEffect(() => {
    const fetchRealtimeData = async () => {
      try {
        const response = await axios.get('/api/realtime');
        setRealtimeData(response.data);
      } catch (err) {
        console.error('Failed to fetch realtime data', err);
      }
    };

    // Fetch initially
    fetchRealtimeData();

    // Set up polling
    const intervalId = setInterval(fetchRealtimeData, 5000);

    return () => {
      clearInterval(intervalId);
    };
  }, []);

  return { realtimeData };
};

export default useRealtime;
