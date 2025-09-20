import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import { WebSocketService } from './services/WebSocketService';
import { ApiService } from './services/ApiService';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [prices, setPrices] = useState({});
  const [trades, setTrades] = useState([]);
  const [positions, setPositions] = useState([]);
  const [tradingStatus, setTradingStatus] = useState({
    isActive: false,
    dailyVolume: 0,
    maxDailyVolume: 10000000,
    volumeExceeded: false
  });

  useEffect(() => {
    // Initialize WebSocket connection
    const wsService = new WebSocketService();
    
    wsService.connect();
    
    wsService.on('connected', () => {
      setIsConnected(true);
      console.log('Connected to WebSocket server');
    });
    
    wsService.on('disconnected', () => {
      setIsConnected(false);
      console.log('Disconnected from WebSocket server');
    });
    
    wsService.on('priceUpdate', (priceData) => {
      setPrices(prevPrices => ({
        ...prevPrices,
        [priceData.symbol]: priceData
      }));
    });
    
    wsService.on('prices', (allPrices) => {
      setPrices(allPrices);
    });
    
    wsService.on('tradeExecuted', (trade) => {
      setTrades(prevTrades => [trade, ...prevTrades.slice(0, 99)]);
      loadTradingStatus(); // Refresh trading status
      loadPositions(); // Refresh positions
    });

    // Load initial data
    loadInitialData();
    
    // Set up periodic data refresh
    const interval = setInterval(() => {
      loadTradingStatus();
      loadPositions();
    }, 5000);

    return () => {
      clearInterval(interval);
      wsService.disconnect();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      const [tradesData, positionsData, statusData] = await Promise.all([
        ApiService.getTrades(null, 50),
        ApiService.getPositions(),
        ApiService.getTradingStatus()
      ]);
      
      setTrades(tradesData);
      setPositions(positionsData);
      setTradingStatus(statusData);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadTradingStatus = async () => {
    try {
      const status = await ApiService.getTradingStatus();
      setTradingStatus(status);
    } catch (error) {
      console.error('Error loading trading status:', error);
    }
  };

  const loadPositions = async () => {
    try {
      const positionsData = await ApiService.getPositions();
      setPositions(positionsData);
    } catch (error) {
      console.error('Error loading positions:', error);
    }
  };

  const handleStartTrading = async () => {
    try {
      await ApiService.startTrading();
      await loadTradingStatus();
    } catch (error) {
      console.error('Error starting trading:', error);
    }
  };

  const handleStopTrading = async () => {
    try {
      await ApiService.stopTrading();
      await loadTradingStatus();
    } catch (error) {
      console.error('Error stopping trading:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AlphaFX Trader</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢' : '🔴'}
          </span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>
      
      <main className="app-main">
        <Dashboard
          prices={prices}
          trades={trades}
          positions={positions}
          tradingStatus={tradingStatus}
          onStartTrading={handleStartTrading}
          onStopTrading={handleStopTrading}
        />
      </main>
    </div>
  );
}

export default App;