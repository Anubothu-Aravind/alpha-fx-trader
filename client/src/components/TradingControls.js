import React from 'react';
import { ApiService } from '../services/ApiService';

const TradingControls = ({ tradingStatus, onStart, onStop }) => {
  const {
    isActive,
    dailyVolume,
    maxDailyVolume,
    volumeExceeded
  } = tradingStatus;

  const volumePercentage = (dailyVolume / maxDailyVolume) * 100;

  return (
    <div className="trading-controls">
      <div className="section-header">
        <h2 className="section-title">Trading Controls</h2>
      </div>
      
      <div className="trading-status">
        <span className={`status-badge ${isActive ? 'status-active' : 'status-inactive'}`}>
          {isActive ? 'ACTIVE' : 'INACTIVE'}
        </span>
        
        <div className="control-buttons">
          <button
            className="btn btn-primary"
            onClick={onStart}
            disabled={isActive || volumeExceeded}
          >
            Start Trading
          </button>
          <button
            className="btn btn-danger"
            onClick={onStop}
            disabled={!isActive}
          >
            Stop Trading
          </button>
        </div>
      </div>
      
      <div className="volume-info">
        <div className="volume-metric">
          <div className="volume-label">Daily Volume</div>
          <div className={`volume-value ${volumeExceeded ? 'volume-exceeded' : ''}`}>
            {ApiService.formatCurrency(dailyVolume, 'USD', 0)}
          </div>
        </div>
        
        <div className="volume-metric">
          <div className="volume-label">Limit</div>
          <div className="volume-value">
            {ApiService.formatCurrency(maxDailyVolume, 'USD', 0)}
          </div>
        </div>
        
        <div className="volume-metric">
          <div className="volume-label">Usage</div>
          <div className={`volume-value ${volumeExceeded ? 'volume-exceeded' : ''}`}>
            {ApiService.formatPercent(volumePercentage)}
          </div>
        </div>
        
        <div className="volume-metric">
          <div className="volume-label">Remaining</div>
          <div className="volume-value">
            {ApiService.formatCurrency(Math.max(0, maxDailyVolume - dailyVolume), 'USD', 0)}
          </div>
        </div>
      </div>
      
      {volumeExceeded && (
        <div className="volume-warning">
          ⚠️ Daily volume limit exceeded. Trading has been automatically stopped.
        </div>
      )}
      
      <div className="volume-bar">
        <div 
          className="volume-progress" 
          style={{ 
            width: `${Math.min(volumePercentage, 100)}%`,
            backgroundColor: volumeExceeded ? '#ff4757' : volumePercentage > 80 ? '#ffa502' : '#2ed573'
          }}
        />
      </div>
    </div>
  );
};

export default TradingControls;