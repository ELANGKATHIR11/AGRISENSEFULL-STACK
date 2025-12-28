import React from 'react';
import LiveStreamCard from './LiveStreamCard';
import RecommendationCard from './RecommendationCard';
import FieldMap from './FieldMap';
import { useRecommendations } from '../../hooks/useRecommendations';
import { useRealtime } from '../../hooks/useRealtime';

const Dashboard = () => {
  const { recommendations, loading, error } = useRecommendations();
  const { realtimeData } = useRealtime();
  
  return (
    <div className="dashboard">
      {/* Main content area */}
      <div className="dashboard-main">
        <div className="dashboard-map">
          <FieldMap data={realtimeData} />
        </div>
        
        <div className="dashboard-recommendation">
          <RecommendationCard 
            recommendation={recommendations[0]} 
            loading={loading} 
            error={error} 
          />
        </div>
      </div>
      
      {/* Sidebar with live streams */}
      <div className="dashboard-sidebar">
        <LiveStreamCard data={realtimeData} />
      </div>
    </div>
  );
};

export default Dashboard;
