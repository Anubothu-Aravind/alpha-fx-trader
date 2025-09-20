const EventEmitter = require('events');

class FXDataSimulator extends EventEmitter {
  constructor() {
    super();
    this.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF'];
    this.prices = {};
    this.intervals = {};
    this.volatility = 0.001; // 0.1% volatility
    this.isRunning = false;
    
    // Initialize base prices
    this.initializePrices();
  }

  initializePrices() {
    const basePrices = {
      'EURUSD': 1.0850,
      'GBPUSD': 1.2650,
      'USDJPY': 148.50,
      'AUDUSD': 0.6850,
      'USDCAD': 1.3450,
      'USDCHF': 0.8950
    };

    this.symbols.forEach(symbol => {
      const basePrice = basePrices[symbol];
      const spread = basePrice * 0.0002; // 2 pips spread
      
      this.prices[symbol] = {
        bid: basePrice - spread / 2,
        ask: basePrice + spread / 2,
        timestamp: new Date(),
        volume: Math.random() * 1000000 + 100000
      };
    });
  }

  start() {
    if (this.isRunning) {
      return;
    }

    this.isRunning = true;
    console.log('Starting FX Data Simulator...');

    this.symbols.forEach(symbol => {
      this.intervals[symbol] = setInterval(() => {
        this.updatePrice(symbol);
      }, 1000 + Math.random() * 2000); // Update every 1-3 seconds
    });

    this.emit('started');
  }

  stop() {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    console.log('Stopping FX Data Simulator...');

    Object.values(this.intervals).forEach(interval => {
      clearInterval(interval);
    });
    this.intervals = {};

    this.emit('stopped');
  }

  updatePrice(symbol) {
    const currentPrice = this.prices[symbol];
    const mid = (currentPrice.bid + currentPrice.ask) / 2;
    
    // Generate random walk with volatility
    const change = (Math.random() - 0.5) * 2 * this.volatility * mid;
    const newMid = mid + change;
    
    // Calculate spread (typically 2-5 pips for major pairs)
    const spread = newMid * (0.0001 + Math.random() * 0.0003);
    
    const newPrice = {
      bid: newMid - spread / 2,
      ask: newMid + spread / 2,
      timestamp: new Date(),
      volume: Math.random() * 1000000 + 100000,
      change: change,
      changePercent: (change / mid) * 100
    };

    this.prices[symbol] = newPrice;
    
    // Emit price update
    this.emit('priceUpdate', {
      symbol: symbol,
      ...newPrice,
      mid: newMid,
      spread: spread
    });
  }

  getPrice(symbol) {
    return this.prices[symbol];
  }

  getAllPrices() {
    return this.prices;
  }

  getSymbols() {
    return this.symbols;
  }

  // Historical data simulation for backtesting
  generateHistoricalData(symbol, startDate, endDate, interval = '1hour') {
    const data = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    let current = new Date(start);
    let price = this.prices[symbol] ? (this.prices[symbol].bid + this.prices[symbol].ask) / 2 : 1.0;
    
    const intervalMs = this.getIntervalMilliseconds(interval);
    
    while (current <= end) {
      // Generate OHLC data
      const open = price;
      const change = (Math.random() - 0.5) * 2 * this.volatility * price;
      const close = open + change;
      
      const high = Math.max(open, close) + Math.random() * Math.abs(change) * 0.5;
      const low = Math.min(open, close) - Math.random() * Math.abs(change) * 0.5;
      
      const volume = Math.random() * 1000000 + 100000;
      
      data.push({
        timestamp: new Date(current),
        symbol: symbol,
        open: open,
        high: high,
        low: low,
        close: close,
        volume: volume
      });
      
      price = close;
      current = new Date(current.getTime() + intervalMs);
    }
    
    return data;
  }

  getIntervalMilliseconds(interval) {
    const intervals = {
      '1min': 60 * 1000,
      '5min': 5 * 60 * 1000,
      '15min': 15 * 60 * 1000,
      '30min': 30 * 60 * 1000,
      '1hour': 60 * 60 * 1000,
      '4hour': 4 * 60 * 60 * 1000,
      '1day': 24 * 60 * 60 * 1000
    };
    
    return intervals[interval] || intervals['1hour'];
  }

  // Simulate market events
  simulateNewsEvent(symbol, impact = 'medium') {
    const impacts = {
      'low': 0.002,    // 0.2% movement
      'medium': 0.005, // 0.5% movement
      'high': 0.01     // 1% movement
    };
    
    const volatilityMultiplier = impacts[impact] || impacts['medium'];
    const direction = Math.random() > 0.5 ? 1 : -1;
    
    const currentPrice = this.prices[symbol];
    const mid = (currentPrice.bid + currentPrice.ask) / 2;
    const movement = mid * volatilityMultiplier * direction;
    
    const newMid = mid + movement;
    const spread = newMid * 0.0003; // Wider spread during news
    
    this.prices[symbol] = {
      bid: newMid - spread / 2,
      ask: newMid + spread / 2,
      timestamp: new Date(),
      volume: Math.random() * 5000000 + 1000000, // Higher volume
      change: movement,
      changePercent: (movement / mid) * 100,
      newsEvent: true
    };
    
    this.emit('newsEvent', {
      symbol: symbol,
      impact: impact,
      movement: movement,
      price: this.prices[symbol]
    });
  }
}

module.exports = FXDataSimulator;