import React from 'react';
import { ApiService } from '../services/ApiService';

const Blotter = ({ trades }) => {
  return (
    <div className="blotter">
      <div className="section-header">
        <h2 className="section-title">Trade Blotter</h2>
        <div style={{ fontSize: '0.8rem', color: '#a4b0be' }}>
          {trades.length} trades
        </div>
      </div>
      
      {trades.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#a4b0be' }}>
          No trades executed yet
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Value</th>
                <th>Algorithm</th>
                <th>PnL</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, index) => {
                const pnl = trade.pnl || 0;
                const isProfitable = pnl > 0;
                
                return (
                  <tr key={trade.id || index}>
                    <td>{ApiService.formatTime(trade.timestamp || trade.created_at)}</td>
                    <td>{trade.symbol}</td>
                    <td className={`side-${trade.side}`}>
                      {trade.side.toUpperCase()}
                    </td>
                    <td>{ApiService.formatNumber(trade.quantity, 0)}</td>
                    <td>{ApiService.formatNumber(trade.price, 5)}</td>
                    <td>{ApiService.formatCurrency(trade.value)}</td>
                    <td>{trade.algorithm || '-'}</td>
                    <td className={pnl !== 0 ? (isProfitable ? 'pnl-positive' : 'pnl-negative') : ''}>
                      {pnl !== 0 ? ApiService.formatCurrency(pnl) : '-'}
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

export default Blotter;