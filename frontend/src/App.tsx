import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './index.css';

// Types
interface FXRate {
  pair: string;
  bid: number;
  ask: number;
  timestamp: string;
  spread?: number;
  change?: number;
}

interface Trade {
  id: string;
  pair: string;
  action: string;
  volume: number;
  execution_price: number;
  timestamp: string;
  pnl?: number;
  status: string;
}

interface TradingStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  current_positions: number;
  active_pairs: string[];
}

interface Position {
  id: string;
  pair: string;
  action: string;
  volume: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  status: string;
  opened_at: string;
}

// API Configuration
const API_BASE = 'http://localhost:8000';

// Utility functions
const formatCurrency = (value: number, decimals: number = 5): string => {
  return value.toFixed(decimals);
};

const formatPnL = (value: number): string => {
  const formatted = value.toFixed(2);
  return value >= 0 ? `+$${formatted}` : `-$${Math.abs(value).toFixed(2)}`;
};

// Components
const RateCard: React.FC<{ rate: FXRate }> = ({ rate }) => {
  const midPrice = (rate.bid + rate.ask) / 2;
  const spread = rate.ask - rate.bid;
  const changeClass = (rate.change || 0) >= 0 ? 'rate-up' : 'rate-down';
  
  return (
    <div className="rate-item">
      <div className="rate-pair">{rate.pair}</div>
      <div className={`rate-price ${changeClass}`}>
        {formatCurrency(midPrice)}
      </div>
      <div className="rate-details">
        <div>Bid: {formatCurrency(rate.bid)}</div>
        <div>Ask: {formatCurrency(rate.ask)}</div>
        <div>Spread: {formatCurrency(spread, 6)}</div>
      </div>
      {rate.change !== undefined && (
        <div className={`rate-change ${changeClass}`}>
          {rate.change >= 0 ? '+' : ''}{(rate.change * 100).toFixed(3)}%
        </div>
      )}
    </div>
  );
};

const TradeForm: React.FC<{
  rates: FXRate[];
  onTrade: (trade: any) => void;
  loading: boolean;
}> = ({ rates, onTrade, loading }) => {
  const [formData, setFormData] = useState({
    pair: 'EUR/USD',
    action: 'buy',
    volume: '0.1',
    order_type: 'market'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onTrade({
      ...formData,
      volume: parseFloat(formData.volume)
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const availablePairs = rates.map(rate => rate.pair);

  return (
    <form className="trade-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Currency Pair</label>
        <select
          name="pair"
          value={formData.pair}
          onChange={handleInputChange}
          className="form-select"
          required
        >
          {availablePairs.map(pair => (
            <option key={pair} value={pair}>{pair}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Action</label>
        <select
          name="action"
          value={formData.action}
          onChange={handleInputChange}
          className="form-select"
          required
        >
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Volume</label>
        <input
          type="number"
          name="volume"
          value={formData.volume}
          onChange={handleInputChange}
          className="form-input"
          min="0.01"
          max="10"
          step="0.01"
          required
        />
      </div>

      <div className="form-group">
        <label className="form-label">Order Type</label>
        <select
          name="order_type"
          value={formData.order_type}
          onChange={handleInputChange}
          className="form-select"
        >
          <option value="market">Market</option>
          <option value="limit">Limit</option>
        </select>
      </div>

      <button
        type="submit"
        className={`btn ${formData.action === 'buy' ? 'btn-success' : 'btn-danger'}`}
        disabled={loading}
      >
        {loading ? 'Processing...' : `${formData.action.toUpperCase()} ${formData.pair}`}
      </button>
    </form>
  );
};

const TradesList: React.FC<{ trades: Trade[] }> = ({ trades }) => {
  return (
    <div className="trades-list">
      {trades.length === 0 ? (
        <div className="loading">No trades yet</div>
      ) : (
        trades.map(trade => (
          <div key={trade.id} className="trade-item">
            <div className="trade-info">
              <div className="trade-pair">{trade.pair}</div>
              <div className="trade-details">
                {trade.action.toUpperCase()} {trade.volume} @ {formatCurrency(trade.execution_price)}
              </div>
              <div className="trade-details">
                {new Date(trade.timestamp).toLocaleString()}
              </div>
            </div>
            {trade.pnl !== undefined && (
              <div className={`trade-pnl ${trade.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
                {formatPnL(trade.pnl)}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};

const PositionsList: React.FC<{ positions: Position[] }> = ({ positions }) => {
  return (
    <div className="trades-list">
      {positions.length === 0 ? (
        <div className="loading">No open positions</div>
      ) : (
        positions.map(position => (
          <div key={position.id} className="trade-item">
            <div className="trade-info">
              <div className="trade-pair">{position.pair}</div>
              <div className="trade-details">
                {position.action.toUpperCase()} {position.volume} @ {formatCurrency(position.entry_price)}
              </div>
              <div className="trade-details">
                Current: {formatCurrency(position.current_price)}
              </div>
            </div>
            <div className={`trade-pnl ${position.unrealized_pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
              {formatPnL(position.unrealized_pnl)}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

const TradingStats: React.FC<{ stats: TradingStats }> = ({ stats }) => {
  return (
    <div className="stats-grid">
      <div className="stat-item">
        <span className="stat-value">{stats.total_trades}</span>
        <div className="stat-label">Total Trades</div>
      </div>
      <div className="stat-item">
        <span className="stat-value">{(stats.win_rate * 100).toFixed(1)}%</span>
        <div className="stat-label">Win Rate</div>
      </div>
      <div className="stat-item">
        <span className={`stat-value ${stats.total_pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
          {formatPnL(stats.total_pnl)}
        </span>
        <div className="stat-label">Total P&L</div>
      </div>
      <div className="stat-item">
        <span className="stat-value">{stats.current_positions}</span>
        <div className="stat-label">Open Positions</div>
      </div>
    </div>
  );
};

// Main App Component
const App: React.FC = () => {
  const [rates, setRates] = useState<FXRate[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [stats, setStats] = useState<TradingStats>({
    total_trades: 0,
    winning_trades: 0,
    losing_trades: 0,
    win_rate: 0,
    total_pnl: 0,
    current_positions: 0,
    active_pairs: []
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  // Fetch initial data
  const fetchRates = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/rates`);
      const newRates = response.data;
      
      // Calculate price changes
      const updatedRates = newRates.map((newRate: FXRate) => {
        const oldRate = rates.find(r => r.pair === newRate.pair);
        if (oldRate) {
          const oldMid = (oldRate.bid + oldRate.ask) / 2;
          const newMid = (newRate.bid + newRate.ask) / 2;
          newRate.change = (newMid - oldMid) / oldMid;
        }
        return newRate;
      });
      
      setRates(updatedRates);
      setConnected(true);
    } catch (err) {
      console.error('Error fetching rates:', err);
      setConnected(false);
    }
  }, [rates]);

  const fetchTrades = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/trades?limit=20`);
      setTrades(response.data);
    } catch (err) {
      console.error('Error fetching trades:', err);
    }
  }, []);

  const fetchPositions = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/positions`);
      setPositions(response.data);
    } catch (err) {
      console.error('Error fetching positions:', err);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      setConnected(response.data.status === 'healthy');
    } catch (err) {
      setConnected(false);
    }
  }, []);

  const handleTrade = async (tradeData: any) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_BASE}/trade`, tradeData);
      setSuccess(`Trade executed successfully: ${response.data.trade_id}`);
      
      // Refresh data
      await Promise.all([fetchTrades(), fetchPositions(), fetchStats()]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute trade');
    } finally {
      setLoading(false);
    }
  };

  // Initialize data and set up polling
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        checkHealth(),
        fetchRates(),
        fetchTrades(),
        fetchPositions(),
        fetchStats()
      ]);
    };

    initializeData();

    // Set up polling for real-time updates
    const ratesInterval = setInterval(fetchRates, 2000); // Every 2 seconds
    const tradesInterval = setInterval(fetchTrades, 5000); // Every 5 seconds
    const positionsInterval = setInterval(fetchPositions, 5000); // Every 5 seconds
    const statsInterval = setInterval(fetchStats, 10000); // Every 10 seconds
    const healthInterval = setInterval(checkHealth, 30000); // Every 30 seconds

    return () => {
      clearInterval(ratesInterval);
      clearInterval(tradesInterval);
      clearInterval(positionsInterval);
      clearInterval(statsInterval);
      clearInterval(healthInterval);
    };
  }, []);

  // Clear messages after 5 seconds
  useEffect(() => {
    if (success || error) {
      const timer = setTimeout(() => {
        setSuccess(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [success, error]);

  return (
    <div className="trading-dashboard">
      <header className="dashboard-header">
        <div className="logo">
          📈 AlphaFX Trader
        </div>
        <div className="status-indicator">
          <div className={`status-dot ${connected ? '' : 'offline'}`} style={{
            backgroundColor: connected ? '#52c41a' : '#ff4d4f'
          }}></div>
          <span>{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      <main className="dashboard-content">
        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        <div className="dashboard-grid">
          <div className="card">
            <h2 className="card-title">
              💱 Live FX Rates
            </h2>
            {rates.length === 0 ? (
              <div className="loading">Loading rates...</div>
            ) : (
              <div className="rate-grid">
                {rates.map(rate => (
                  <RateCard key={rate.pair} rate={rate} />
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="card-title">
              📊 Trading Statistics
            </h2>
            <TradingStats stats={stats} />
          </div>
        </div>

        <div className="dashboard-row">
          <div className="card">
            <h2 className="card-title">
              📈 Recent Trades
            </h2>
            <TradesList trades={trades} />
          </div>

          <div className="card">
            <h2 className="card-title">
              🎯 Execute Trade
            </h2>
            <TradeForm rates={rates} onTrade={handleTrade} loading={loading} />
          </div>
        </div>

        <div className="dashboard-row">
          <div className="card">
            <h2 className="card-title">
              💼 Open Positions
            </h2>
            <PositionsList positions={positions} />
          </div>

          <div className="card">
            <h2 className="card-title">
              ⚙️ Quick Actions
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <button 
                className="btn btn-primary"
                onClick={() => {
                  fetchRates();
                  fetchTrades();
                  fetchPositions();
                  fetchStats();
                }}
              >
                🔄 Refresh Data
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => window.open(`${API_BASE}/docs`, '_blank')}
              >
                📚 API Documentation
              </button>
              <button 
                className="btn btn-primary"
                onClick={checkHealth}
              >
                🏥 Health Check
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;