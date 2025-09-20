const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

class TradingEngine extends EventEmitter {
  constructor(database, priceProvider, algorithms) {
    super();
    this.db = database;
    this.priceProvider = priceProvider;
    this.algorithms = algorithms;
    this.isActive = false;
    this.maxDailyVolume = parseFloat(process.env.MAX_TRADING_VOLUME) || 10000000; // $10M
    this.defaultPositionSize = parseFloat(process.env.DEFAULT_POSITION_SIZE) || 10000; // $10K
    this.currentDailyVolume = 0;
    this.activeOrders = new Map();
    this.riskManagement = process.env.RISK_MANAGEMENT === 'true';
    
    this.loadCurrentVolume();
  }

  async loadCurrentVolume() {
    try {
      const today = new Date().toISOString().split('T')[0];
      const stats = await this.db.get(
        'SELECT total_volume FROM trading_stats WHERE date = ?',
        [today]
      );
      this.currentDailyVolume = stats ? stats.total_volume : 0;
    } catch (error) {
      console.error('Error loading current volume:', error);
      this.currentDailyVolume = 0;
    }
  }

  async start() {
    if (this.isActive) {
      return;
    }
    
    this.isActive = true;
    console.log('Trading Engine started');
    
    // Listen for price updates
    this.priceProvider.on('priceUpdate', (priceData) => {
      this.onPriceUpdate(priceData);
    });
    
    // Check for trading opportunities every 5 seconds
    this.tradingInterval = setInterval(() => {
      this.evaluateTradingOpportunities();
    }, 5000);
    
    this.emit('started');
  }

  async stop() {
    if (!this.isActive) {
      return;
    }
    
    this.isActive = false;
    console.log('Trading Engine stopped');
    
    if (this.tradingInterval) {
      clearInterval(this.tradingInterval);
    }
    
    // Cancel pending orders
    for (const [orderId, order] of this.activeOrders) {
      await this.cancelOrder(orderId);
    }
    
    this.emit('stopped');
  }

  async onPriceUpdate(priceData) {
    // Add price data to algorithms for analysis
    this.algorithms.addPriceData(
      priceData.symbol, 
      priceData, 
      priceData.timestamp
    );
    
    // Update position PnL
    await this.updatePositionPnL(priceData.symbol, priceData.mid);
    
    // Check stop losses and take profits
    await this.checkStopOrders(priceData);
  }

  async evaluateTradingOpportunities() {
    if (!this.isActive || this.currentDailyVolume >= this.maxDailyVolume) {
      if (this.currentDailyVolume >= this.maxDailyVolume) {
        console.log(`Daily volume limit reached: $${this.currentDailyVolume.toLocaleString()}`);
        await this.stop();
      }
      return;
    }

    const symbols = this.priceProvider.getSymbols();
    
    for (const symbol of symbols) {
      try {
        await this.evaluateSymbol(symbol);
      } catch (error) {
        console.error(`Error evaluating ${symbol}:`, error);
      }
    }
  }

  async evaluateSymbol(symbol) {
    const currentPrice = this.priceProvider.getPrice(symbol);
    if (!currentPrice) {
      return;
    }

    // Get trading signals
    const signal = this.algorithms.getCombinedSignal(symbol);
    
    if (signal.confidence < 0.6) {
      return; // Not confident enough
    }

    // Check if we already have a position in this symbol
    const existingPosition = await this.db.get(
      'SELECT * FROM positions WHERE symbol = ?',
      [symbol]
    );

    // Risk management checks
    if (this.riskManagement) {
      if (!await this.passesRiskChecks(symbol, signal, existingPosition)) {
        return;
      }
    }

    // Calculate position size
    const positionSize = this.calculatePositionSize(symbol, signal.confidence);
    
    if (signal.signal === 'buy' && (!existingPosition || existingPosition.quantity <= 0)) {
      await this.executeBuy(symbol, positionSize, signal);
    } else if (signal.signal === 'sell' && (!existingPosition || existingPosition.quantity >= 0)) {
      await this.executeSell(symbol, positionSize, signal);
    }
  }

  async passesRiskChecks(symbol, signal, existingPosition) {
    // Check daily volume limit
    if (this.currentDailyVolume >= this.maxDailyVolume) {
      return false;
    }
    
    // Check if position size would be too large
    const currentPrice = this.priceProvider.getPrice(symbol);
    const positionSize = this.calculatePositionSize(symbol, signal.confidence);
    const tradeValue = positionSize * currentPrice.mid;
    
    if (tradeValue > this.maxDailyVolume * 0.1) { // Max 10% of daily limit per trade
      return false;
    }
    
    // Check if adding to existing position would create too much exposure
    if (existingPosition) {
      const currentExposure = Math.abs(existingPosition.quantity * existingPosition.avg_price);
      const newExposure = currentExposure + tradeValue;
      
      if (newExposure > this.maxDailyVolume * 0.2) { // Max 20% exposure per symbol
        return false;
      }
    }
    
    return true;
  }

  calculatePositionSize(symbol, confidence) {
    // Base position size adjusted by confidence
    let size = this.defaultPositionSize * confidence;
    
    // Ensure minimum viable trade
    const currentPrice = this.priceProvider.getPrice(symbol);
    const minTradeValue = 1000; // $1000 minimum
    const minSize = minTradeValue / currentPrice.mid;
    
    return Math.max(size, minSize);
  }

  async executeBuy(symbol, quantity, signal) {
    const priceData = this.priceProvider.getPrice(symbol);
    const price = priceData.ask; // Buy at ask price
    const value = quantity * price;
    
    // Check volume limit
    if (this.currentDailyVolume + value > this.maxDailyVolume) {
      console.log(`Buy order would exceed daily volume limit for ${symbol}`);
      return null;
    }

    const trade = {
      id: uuidv4(),
      symbol: symbol,
      side: 'buy',
      quantity: quantity,
      price: price,
      value: value,
      algorithm: 'combined',
      status: 'executed',
      timestamp: new Date(),
      signal_data: JSON.stringify(signal)
    };

    try {
      // Execute trade in database
      const result = await this.db.run(`
        INSERT INTO trades (symbol, side, quantity, price, value, algorithm, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `, [trade.symbol, trade.side, trade.quantity, trade.price, trade.value, trade.algorithm, trade.status]);

      trade.db_id = result.id;

      // Update position
      await this.updatePosition(symbol, quantity, price, false);
      
      // Update daily volume
      this.currentDailyVolume += value;
      await this.updateTradingStats();
      
      console.log(`BUY executed: ${quantity.toFixed(0)} ${symbol} @ ${price.toFixed(5)} = $${value.toFixed(2)}`);
      
      this.emit('tradeExecuted', trade);
      
      return trade;
    } catch (error) {
      console.error('Error executing buy order:', error);
      return null;
    }
  }

  async executeSell(symbol, quantity, signal) {
    const priceData = this.priceProvider.getPrice(symbol);
    const price = priceData.bid; // Sell at bid price
    const value = quantity * price;
    
    const trade = {
      id: uuidv4(),
      symbol: symbol,
      side: 'sell',
      quantity: quantity,
      price: price,
      value: value,
      algorithm: 'combined',
      status: 'executed',
      timestamp: new Date(),
      signal_data: JSON.stringify(signal)
    };

    try {
      // Execute trade in database
      const result = await this.db.run(`
        INSERT INTO trades (symbol, side, quantity, price, value, algorithm, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `, [trade.symbol, trade.side, trade.quantity, trade.price, trade.value, trade.algorithm, trade.status]);

      trade.db_id = result.id;

      // Update position
      await this.updatePosition(symbol, -quantity, price, true);
      
      // Update daily volume
      this.currentDailyVolume += value;
      await this.updateTradingStats();
      
      console.log(`SELL executed: ${quantity.toFixed(0)} ${symbol} @ ${price.toFixed(5)} = $${value.toFixed(2)}`);
      
      this.emit('tradeExecuted', trade);
      
      return trade;
    } catch (error) {
      console.error('Error executing sell order:', error);
      return null;
    }
  }

  async updatePosition(symbol, quantity, price, isClosing) {
    const currentPosition = await this.db.get(
      'SELECT * FROM positions WHERE symbol = ?',
      [symbol]
    );
    
    if (!currentPosition) {
      // Create new position
      await this.db.run(`
        INSERT INTO positions (symbol, quantity, avg_price, total_value, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
      `, [symbol, quantity, price, quantity * price]);
    } else {
      // Update existing position
      let newQuantity, newAvgPrice, newTotalValue;
      
      if (isClosing) {
        newQuantity = currentPosition.quantity + quantity; // quantity is negative for sells
        newAvgPrice = newQuantity === 0 ? 0 : currentPosition.avg_price;
        newTotalValue = newQuantity * newAvgPrice;
      } else {
        // Adding to position
        const oldValue = currentPosition.quantity * currentPosition.avg_price;
        const newValue = quantity * price;
        newTotalValue = oldValue + newValue;
        newQuantity = currentPosition.quantity + quantity;
        newAvgPrice = newQuantity !== 0 ? newTotalValue / newQuantity : 0;
      }
      
      await this.db.run(`
        UPDATE positions 
        SET quantity = ?, avg_price = ?, total_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE symbol = ?
      `, [newQuantity, newAvgPrice, newTotalValue, symbol]);
    }
  }

  async updatePositionPnL(symbol, currentPrice) {
    const position = await this.db.get(
      'SELECT * FROM positions WHERE symbol = ?',
      [symbol]
    );
    
    if (position && position.quantity !== 0) {
      const unrealizedPnL = (currentPrice - position.avg_price) * position.quantity;
      
      await this.db.run(
        'UPDATE positions SET pnl = ? WHERE symbol = ?',
        [unrealizedPnL, symbol]
      );
    }
  }

  async checkStopOrders(priceData) {
    // Implementation for stop losses and take profits
    // This would check for existing orders with stop/limit conditions
  }

  async updateTradingStats() {
    const today = new Date().toISOString().split('T')[0];
    const totalTrades = await this.db.get(
      'SELECT COUNT(*) as count FROM trades WHERE DATE(timestamp) = ?',
      [today]
    );
    
    const totalPnL = await this.db.get(`
      SELECT SUM(
        CASE 
          WHEN side = 'buy' THEN -value
          ELSE value
        END
      ) as pnl FROM trades WHERE DATE(timestamp) = ?
    `, [today]);
    
    const activePositions = await this.db.get(
      'SELECT COUNT(*) as count FROM positions WHERE quantity != 0'
    );

    await this.db.run(`
      INSERT OR REPLACE INTO trading_stats 
      (date, total_volume, total_trades, total_pnl, active_positions, updated_at)
      VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    `, [
      today,
      this.currentDailyVolume,
      totalTrades.count,
      totalPnL.pnl || 0,
      activePositions.count
    ]);
  }

  async cancelOrder(orderId) {
    const order = this.activeOrders.get(orderId);
    if (order) {
      this.activeOrders.delete(orderId);
      this.emit('orderCancelled', order);
    }
  }

  getDailyVolume() {
    return this.currentDailyVolume;
  }

  getMaxDailyVolume() {
    return this.maxDailyVolume;
  }

  isVolumeExceeded() {
    return this.currentDailyVolume >= this.maxDailyVolume;
  }
}

module.exports = TradingEngine;