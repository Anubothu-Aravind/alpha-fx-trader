import React from 'react';
import { ApiService } from '../services/ApiService';

const Positions = ({ positions }) => {
  const totalPnL = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const totalValue = positions.reduce((sum, pos) => sum + Math.abs(pos.total_value || 0), 0);

  return (
    <div className="positions">
      <div className="section-header">
        <h2 className="section-title">Open Positions</h2>
        <div style={{ fontSize: '0.8rem', color: '#a4b0be' }}>
          {positions.length} positions
        </div>
      </div>
      
      {positions.length > 0 && (
        <div className="position-summary" style={{ marginBottom: '1rem', padding: '0.5rem', backgroundColor: '#16213e', borderRadius: '4px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.9rem' }}>
            <div>
              <div style={{ color: '#a4b0be', fontSize: '0.8rem' }}>Total Exposure</div>
              <div style={{ color: '#ffffff', fontWeight: '600' }}>
                {ApiService.formatCurrency(totalValue)}
              </div>
            </div>
            <div>
              <div style={{ color: '#a4b0be', fontSize: '0.8rem' }}>Total PnL</div>
              <div className={totalPnL > 0 ? 'pnl-positive' : totalPnL < 0 ? 'pnl-negative' : ''} style={{ fontWeight: '600' }}>
                {ApiService.formatCurrency(totalPnL)}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {positions.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#a4b0be' }}>
          No open positions
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Avg Price</th>
                <th>Market Value</th>
                <th>PnL</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((position) => {
                const pnl = position.pnl || 0;
                const isProfitable = pnl > 0;
                const isLong = position.quantity > 0;
                
                return (
                  <tr key={position.symbol}>
                    <td style={{ fontWeight: '600', color: '#00d4ff' }}>
                      {position.symbol}
                    </td>
                    <td className={isLong ? 'side-buy' : 'side-sell'}>
                      {ApiService.formatNumber(position.quantity, 0)}
                      <span style={{ fontSize: '0.8rem', marginLeft: '0.5rem', color: '#a4b0be' }}>
                        ({isLong ? 'LONG' : 'SHORT'})
                      </span>
                    </td>
                    <td>{ApiService.formatNumber(position.avg_price, 5)}</td>
                    <td>{ApiService.formatCurrency(Math.abs(position.total_value))}</td>
                    <td className={pnl !== 0 ? (isProfitable ? 'pnl-positive' : 'pnl-negative') : ''}>
                      {ApiService.formatCurrency(pnl)}
                      {pnl !== 0 && (
                        <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                          {ApiService.formatPercent((pnl / Math.abs(position.total_value)) * 100)}
                        </div>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#a4b0be' }}>
                      {ApiService.formatTime(position.updated_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Positions;