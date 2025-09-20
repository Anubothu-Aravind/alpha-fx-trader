import React from 'react';
import { ApiService } from '../services/ApiService';

const PriceGrid = ({ prices }) => {
  const symbols = Object.keys(prices).sort();

  if (symbols.length === 0) {
    return (
      <div className="price-grid">
        <div className="section-header">
          <h2 className="section-title">Live Prices</h2>
        </div>
        <div style={{ textAlign: 'center', padding: '2rem', color: '#a4b0be' }}>
          Connecting to price feed...
        </div>
      </div>
    );
  }

  return (
    <div className="price-grid">
      <div className="section-header">
        <h2 className="section-title">Live Prices</h2>
        <div style={{ fontSize: '0.8rem', color: '#a4b0be' }}>
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>
      
      <div className="price-cards">
        {symbols.map(symbol => {
          const price = prices[symbol];
          const changePercent = price.changePercent || 0;
          const isPositive = changePercent >= 0;
          
          return (
            <div key={symbol} className="price-card">
              <div className="price-symbol">{symbol}</div>
              
              <div className="price-values">
                <div className="price-item">
                  <span className="price-label">Bid</span>
                  <span className="price-value">{ApiService.formatNumber(price.bid, 5)}</span>
                </div>
                <div className="price-item">
                  <span className="price-label">Ask</span>
                  <span className="price-value">{ApiService.formatNumber(price.ask, 5)}</span>
                </div>
                <div className="price-item">
                  <span className="price-label">Mid</span>
                  <span className="price-value">{ApiService.formatNumber(price.mid || (price.bid + price.ask) / 2, 5)}</span>
                </div>
                <div className="price-item">
                  <span className="price-label">Spread</span>
                  <span className="price-value">{ApiService.formatNumber(price.ask - price.bid, 5)}</span>
                </div>
              </div>
              
              {changePercent !== 0 && (
                <div className={`price-change ${isPositive ? 'price-positive' : 'price-negative'}`}>
                  {isPositive ? '↗' : '↘'} {ApiService.formatPercent(Math.abs(changePercent))}
                </div>
              )}
              
              {price.volume && (
                <div className="price-item" style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
                  <span className="price-label">Volume</span>
                  <span className="price-value">{ApiService.formatNumber(price.volume, 0)}</span>
                </div>
              )}
              
              <div className="price-timestamp" style={{ 
                fontSize: '0.7rem', 
                color: '#a4b0be', 
                marginTop: '0.5rem',
                textAlign: 'center'
              }}>
                {ApiService.formatTime(price.timestamp)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PriceGrid;