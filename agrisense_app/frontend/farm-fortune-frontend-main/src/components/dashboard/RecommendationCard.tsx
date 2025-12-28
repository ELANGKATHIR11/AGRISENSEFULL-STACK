import React from 'react';

interface RecommendationCardProps {
  recommendation: any;
  loading: boolean;
  error: string | null;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ 
  recommendation, 
  loading, 
  error 
}) => {
  if (loading) return <div>Loading recommendations...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div className="recommendation-card">
      <div className="recommendation-header">
        <h2>Recommended Action</h2>
        <span className="ml-badge">ML-Powered</span>
      </div>
      
      <div className="recommendation-main">
        <div className="water-amount">
          <span className="value">{recommendation?.water_liters || 0}</span>
          <span className="unit">liters</span>
        </div>
        
        <div className="actions">
          <button className="btn primary">Apply Now</button>
          <button className="btn secondary">Schedule</button>
        </div>
      </div>
      
      <div className="recommendation-tips">
        <h3>Tips</h3>
        <ul>
          {(recommendation?.tips || []).slice(0, 3).map((tip: string, index: number) => (
            <li key={index}>{tip}</li>
          ))}
        </ul>
        <button className="btn link">Why? Explain</button>
      </div>
      
      <div className="ml-status">
        {recommendation?.ml_fallback ? (
          <div className="fallback-banner">Rule-based fallback active</div>
        ) : (
          <div className="ml-active">ML model active</div>
        )}
      </div>
    </div>
  );
};

export default RecommendationCard;
