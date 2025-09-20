const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const http = require('http');
const path = require('path');
require('dotenv').config();

// Import our modules
const Database = require('./database/Database');
const FXDataSimulator = require('./trading/FXDataSimulator');
const TradingAlgorithms = require('./trading/TradingAlgorithms');
const TradingEngine = require('./trading/TradingEngine');

class AlphaFXTraderApp {
  constructor() {
    this.app = express();
    this.server = http.createServer(this.app);
    this.port = process.env.PORT || 3001;
    
    // Initialize components
    this.database = new Database();
    this.fxSimulator = new FXDataSimulator();
    this.algorithms = new TradingAlgorithms();
    this.tradingEngine = null;
    
    this.wss = null;
    this.clients = new Set();
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupWebSocket();
  }

  setupMiddleware() {
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.static(path.join(__dirname, '../client/build')));
    
    // Logging middleware
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });
  }

  setupRoutes() {
    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      });
    });

    // Trading status
    this.app.get('/api/trading/status', (req, res) => {
      res.json({
        isActive: this.tradingEngine ? this.tradingEngine.isActive : false,
        dailyVolume: this.tradingEngine ? this.tradingEngine.getDailyVolume() : 0,
        maxDailyVolume: this.tradingEngine ? this.tradingEngine.getMaxDailyVolume() : 0,
        volumeExceeded: this.tradingEngine ? this.tradingEngine.isVolumeExceeded() : false
      });
    });

    // Start/Stop trading
    this.app.post('/api/trading/start', async (req, res) => {
      try {
        if (this.tradingEngine && !this.tradingEngine.isActive) {
          await this.tradingEngine.start();
        }
        res.json({ message: 'Trading started', status: 'active' });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    this.app.post('/api/trading/stop', async (req, res) => {
      try {
        if (this.tradingEngine && this.tradingEngine.isActive) {
          await this.tradingEngine.stop();
        }
        res.json({ message: 'Trading stopped', status: 'inactive' });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get current prices
    this.app.get('/api/prices', (req, res) => {
      const prices = this.fxSimulator.getAllPrices();
      res.json(prices);
    });

    // Get price for specific symbol
    this.app.get('/api/prices/:symbol', (req, res) => {
      const price = this.fxSimulator.getPrice(req.params.symbol);
      if (!price) {
        return res.status(404).json({ error: 'Symbol not found' });
      }
      res.json(price);
    });

    // Get trading signals
    this.app.get('/api/signals/:symbol', (req, res) => {
      try {
        const signal = this.algorithms.getCombinedSignal(req.params.symbol);
        res.json(signal);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get trades
    this.app.get('/api/trades', async (req, res) => {
      try {
        const { symbol, limit = 100, offset = 0 } = req.query;
        const trades = await this.database.all(`
          SELECT * FROM trades 
          ${symbol ? 'WHERE symbol = ?' : ''}
          ORDER BY timestamp DESC 
          LIMIT ? OFFSET ?
        `, symbol ? [symbol, limit, offset] : [limit, offset]);
        
        res.json(trades);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get positions
    this.app.get('/api/positions', async (req, res) => {
      try {
        const positions = await this.database.all('SELECT * FROM positions WHERE quantity != 0');
        res.json(positions);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get trading statistics
    this.app.get('/api/stats', async (req, res) => {
      try {
        const today = new Date().toISOString().split('T')[0];
        const stats = await this.database.get(
          'SELECT * FROM trading_stats WHERE date = ?',
          [today]
        );
        
        res.json(stats || {
          date: today,
          total_volume: 0,
          total_trades: 0,
          total_pnl: 0,
          active_positions: 0
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Historical data for backtesting
    this.app.get('/api/historical/:symbol', (req, res) => {
      try {
        const { symbol } = req.params;
        const { startDate, endDate, interval = '1hour' } = req.query;
        
        if (!startDate || !endDate) {
          return res.status(400).json({ error: 'startDate and endDate are required' });
        }

        const data = this.fxSimulator.generateHistoricalData(symbol, startDate, endDate, interval);
        res.json(data);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Backtesting endpoint
    this.app.post('/api/backtest', async (req, res) => {
      try {
        const { symbol, startDate, endDate, algorithm, parameters } = req.body;
        
        const result = await this.runBacktest(symbol, startDate, endDate, algorithm, parameters);
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Serve React app for all other routes
    this.app.get('*', (req, res) => {
      res.sendFile(path.join(__dirname, '../client/build/index.html'));
    });
  }

  setupWebSocket() {
    this.wss = new WebSocket.Server({ server: this.server });
    
    this.wss.on('connection', (ws) => {
      console.log('New WebSocket client connected');
      this.clients.add(ws);
      
      // Send initial data
      ws.send(JSON.stringify({
        type: 'prices',
        data: this.fxSimulator.getAllPrices()
      }));
      
      ws.on('close', () => {
        console.log('WebSocket client disconnected');
        this.clients.delete(ws);
      });
      
      ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        this.clients.delete(ws);
      });
    });
    
    // Broadcast price updates to all clients
    this.fxSimulator.on('priceUpdate', (priceData) => {
      this.broadcastToClients({
        type: 'priceUpdate',
        data: priceData
      });
    });
    
    // Broadcast trade executions
    if (this.tradingEngine) {
      this.tradingEngine.on('tradeExecuted', (trade) => {
        this.broadcastToClients({
          type: 'tradeExecuted',
          data: trade
        });
      });
    }
  }

  broadcastToClients(message) {
    const messageStr = JSON.stringify(message);
    this.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(messageStr);
      }
    });
  }

  async runBacktest(symbol, startDate, endDate, algorithm, parameters = {}) {
    console.log(`Running backtest for ${symbol} from ${startDate} to ${endDate}`);
    
    // Generate historical data
    const historicalData = this.fxSimulator.generateHistoricalData(symbol, startDate, endDate, '1hour');
    
    // Create temporary algorithms instance for backtesting
    const backtestAlgorithms = new TradingAlgorithms();
    
    let trades = [];
    let balance = 100000; // Starting balance
    let position = 0;
    let positionPrice = 0;
    
    for (let i = 0; i < historicalData.length; i++) {
      const data = historicalData[i];
      
      // Add data to algorithms
      backtestAlgorithms.addPriceData(symbol, {
        bid: data.close,
        ask: data.close,
        volume: data.volume
      }, data.timestamp);
      
      // Get signal
      const signal = backtestAlgorithms.getCombinedSignal(symbol, parameters);
      
      if (signal.confidence > 0.6) {
        if (signal.signal === 'buy' && position <= 0) {
          // Buy signal
          const quantity = Math.floor(balance * 0.1 / data.close); // Use 10% of balance
          if (quantity > 0) {
            position = quantity;
            positionPrice = data.close;
            balance -= quantity * data.close;
            
            trades.push({
              timestamp: data.timestamp,
              side: 'buy',
              quantity: quantity,
              price: data.close,
              value: quantity * data.close,
              signal: signal
            });
          }
        } else if (signal.signal === 'sell' && position > 0) {
          // Sell signal
          const sellValue = position * data.close;
          const pnl = sellValue - (position * positionPrice);
          balance += sellValue;
          
          trades.push({
            timestamp: data.timestamp,
            side: 'sell',
            quantity: position,
            price: data.close,
            value: sellValue,
            pnl: pnl,
            signal: signal
          });
          
          position = 0;
          positionPrice = 0;
        }
      }
    }
    
    // Calculate final stats
    const totalTrades = trades.length;
    const profitableTrades = trades.filter(t => t.pnl && t.pnl > 0).length;
    const totalPnL = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const finalBalance = balance + (position * historicalData[historicalData.length - 1].close);
    const returnPercent = ((finalBalance - 100000) / 100000) * 100;
    
    return {
      symbol,
      startDate,
      endDate,
      algorithm,
      parameters,
      trades,
      stats: {
        totalTrades,
        profitableTrades,
        winRate: totalTrades > 0 ? (profitableTrades / totalTrades) * 100 : 0,
        totalPnL,
        startingBalance: 100000,
        finalBalance,
        returnPercent
      }
    };
  }

  async start() {
    try {
      // Connect to database
      await this.database.connect();
      
      // Start FX data simulator
      this.fxSimulator.start();
      
      // Initialize trading engine
      this.tradingEngine = new TradingEngine(this.database, this.fxSimulator, this.algorithms);
      
      // Setup WebSocket broadcasting for trade events
      this.tradingEngine.on('tradeExecuted', (trade) => {
        this.broadcastToClients({
          type: 'tradeExecuted',
          data: trade
        });
      });
      
      // Start server
      this.server.listen(this.port, () => {
        console.log(`AlphaFX Trader server running on port ${this.port}`);
        console.log(`WebSocket server running on port ${this.port}`);
        console.log(`Environment: ${process.env.NODE_ENV}`);
      });
      
    } catch (error) {
      console.error('Error starting server:', error);
      process.exit(1);
    }
  }

  async stop() {
    console.log('Shutting down AlphaFX Trader...');
    
    if (this.tradingEngine) {
      await this.tradingEngine.stop();
    }
    
    if (this.fxSimulator) {
      this.fxSimulator.stop();
    }
    
    if (this.database) {
      await this.database.close();
    }
    
    if (this.server) {
      this.server.close();
    }
  }
}

// Handle graceful shutdown
process.on('SIGTERM', async () => {
  if (global.app) {
    await global.app.stop();
  }
  process.exit(0);
});

process.on('SIGINT', async () => {
  if (global.app) {
    await global.app.stop();
  }
  process.exit(0);
});

// Start the application
if (require.main === module) {
  global.app = new AlphaFXTraderApp();
  global.app.start();
}

module.exports = AlphaFXTraderApp;