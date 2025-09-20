class TradingAlgorithms {
  constructor() {
    this.priceHistory = new Map(); // symbol -> array of prices
    this.maxHistory = 200; // Keep last 200 data points
  }

  addPriceData(symbol, price, timestamp) {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }
    
    const history = this.priceHistory.get(symbol);
    const mid = (price.bid + price.ask) / 2;
    
    history.push({
      timestamp: timestamp || new Date(),
      price: mid,
      high: mid + (price.ask - price.bid) / 2,
      low: mid - (price.ask - price.bid) / 2,
      volume: price.volume || 0
    });
    
    // Keep only recent history
    if (history.length > this.maxHistory) {
      history.splice(0, history.length - this.maxHistory);
    }
  }

  getPriceHistory(symbol, periods = null) {
    const history = this.priceHistory.get(symbol) || [];
    if (periods) {
      return history.slice(-periods);
    }
    return history;
  }

  // Simple Moving Average
  calculateSMA(symbol, period) {
    const history = this.getPriceHistory(symbol, period);
    if (history.length < period) {
      return null;
    }
    
    const sum = history.reduce((acc, item) => acc + item.price, 0);
    return sum / period;
  }

  // SMA Crossover Strategy
  getSMACrossoverSignal(symbol, shortPeriod = 10, longPeriod = 50) {
    const shortSMA = this.calculateSMA(symbol, shortPeriod);
    const longSMA = this.calculateSMA(symbol, longPeriod);
    
    if (!shortSMA || !longSMA) {
      return { signal: 'hold', confidence: 0, reason: 'insufficient_data' };
    }

    // Get previous SMAs to detect crossover
    const history = this.getPriceHistory(symbol);
    if (history.length < longPeriod + 1) {
      return { signal: 'hold', confidence: 0, reason: 'insufficient_history' };
    }

    // Calculate previous SMAs
    const prevHistory = history.slice(0, -1);
    const prevShortSum = prevHistory.slice(-shortPeriod).reduce((acc, item) => acc + item.price, 0);
    const prevLongSum = prevHistory.slice(-longPeriod).reduce((acc, item) => acc + item.price, 0);
    const prevShortSMA = prevShortSum / shortPeriod;
    const prevLongSMA = prevLongSum / longPeriod;

    // Detect crossover
    const currentCross = shortSMA > longSMA;
    const prevCross = prevShortSMA > prevLongSMA;
    
    let signal = 'hold';
    let confidence = 0;
    let reason = 'no_crossover';

    if (currentCross && !prevCross) {
      // Golden cross - bullish signal
      signal = 'buy';
      confidence = Math.min(((shortSMA - longSMA) / longSMA) * 100, 1.0);
      reason = 'golden_cross';
    } else if (!currentCross && prevCross) {
      // Death cross - bearish signal
      signal = 'sell';
      confidence = Math.min(((longSMA - shortSMA) / shortSMA) * 100, 1.0);
      reason = 'death_cross';
    }

    return {
      signal,
      confidence,
      reason,
      shortSMA,
      longSMA,
      crossover: currentCross !== prevCross
    };
  }

  // Relative Strength Index (RSI)
  calculateRSI(symbol, period = 14) {
    const history = this.getPriceHistory(symbol, period + 1);
    if (history.length < period + 1) {
      return null;
    }

    const gains = [];
    const losses = [];

    for (let i = 1; i < history.length; i++) {
      const change = history[i].price - history[i - 1].price;
      if (change > 0) {
        gains.push(change);
        losses.push(0);
      } else {
        gains.push(0);
        losses.push(Math.abs(change));
      }
    }

    const avgGain = gains.reduce((sum, gain) => sum + gain, 0) / period;
    const avgLoss = losses.reduce((sum, loss) => sum + loss, 0) / period;

    if (avgLoss === 0) {
      return 100; // All gains, RSI = 100
    }

    const rs = avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));

    return rsi;
  }

  // RSI Strategy
  getRSISignal(symbol, period = 14, overbought = 70, oversold = 30) {
    const rsi = this.calculateRSI(symbol, period);
    
    if (rsi === null) {
      return { signal: 'hold', confidence: 0, reason: 'insufficient_data', rsi: null };
    }

    let signal = 'hold';
    let confidence = 0;
    let reason = 'neutral';

    if (rsi > overbought) {
      signal = 'sell';
      confidence = Math.min((rsi - overbought) / (100 - overbought), 1.0);
      reason = 'overbought';
    } else if (rsi < oversold) {
      signal = 'buy';
      confidence = Math.min((oversold - rsi) / oversold, 1.0);
      reason = 'oversold';
    }

    return {
      signal,
      confidence,
      reason,
      rsi,
      overbought,
      oversold
    };
  }

  // Bollinger Bands
  calculateBollingerBands(symbol, period = 20, standardDeviations = 2) {
    const history = this.getPriceHistory(symbol, period);
    if (history.length < period) {
      return null;
    }

    const prices = history.map(item => item.price);
    const sma = prices.reduce((sum, price) => sum + price, 0) / period;
    
    const squaredDifferences = prices.map(price => Math.pow(price - sma, 2));
    const variance = squaredDifferences.reduce((sum, diff) => sum + diff, 0) / period;
    const stdDev = Math.sqrt(variance);

    return {
      middle: sma,
      upper: sma + (standardDeviations * stdDev),
      lower: sma - (standardDeviations * stdDev),
      bandwidth: (2 * standardDeviations * stdDev) / sma * 100
    };
  }

  // Bollinger Bands Strategy
  getBollingerBandsSignal(symbol, period = 20, standardDeviations = 2) {
    const bands = this.calculateBollingerBands(symbol, period, standardDeviations);
    const history = this.getPriceHistory(symbol, 1);
    
    if (!bands || history.length === 0) {
      return { signal: 'hold', confidence: 0, reason: 'insufficient_data', bands: null };
    }

    const currentPrice = history[history.length - 1].price;
    let signal = 'hold';
    let confidence = 0;
    let reason = 'within_bands';

    if (currentPrice > bands.upper) {
      signal = 'sell';
      confidence = Math.min((currentPrice - bands.upper) / (bands.upper - bands.middle), 1.0);
      reason = 'above_upper_band';
    } else if (currentPrice < bands.lower) {
      signal = 'buy';
      confidence = Math.min((bands.lower - currentPrice) / (bands.middle - bands.lower), 1.0);
      reason = 'below_lower_band';
    }

    return {
      signal,
      confidence,
      reason,
      bands,
      currentPrice,
      position: currentPrice > bands.upper ? 'above_upper' : 
               currentPrice < bands.lower ? 'below_lower' : 'within_bands'
    };
  }

  // Combined Signal Analysis
  getCombinedSignal(symbol, options = {}) {
    const {
      smaShort = 10,
      smaLong = 50,
      rsiPeriod = 14,
      rsiOverbought = 70,
      rsiOversold = 30,
      bbPeriod = 20,
      bbStdDev = 2
    } = options;

    const smaSignal = this.getSMACrossoverSignal(symbol, smaShort, smaLong);
    const rsiSignal = this.getRSISignal(symbol, rsiPeriod, rsiOverbought, rsiOversold);
    const bbSignal = this.getBollingerBandsSignal(symbol, bbPeriod, bbStdDev);

    const signals = [smaSignal, rsiSignal, bbSignal];
    const validSignals = signals.filter(s => s.confidence > 0);

    if (validSignals.length === 0) {
      return {
        signal: 'hold',
        confidence: 0,
        reason: 'no_valid_signals',
        components: { sma: smaSignal, rsi: rsiSignal, bb: bbSignal }
      };
    }

    // Calculate weighted average
    const buySignals = validSignals.filter(s => s.signal === 'buy');
    const sellSignals = validSignals.filter(s => s.signal === 'sell');

    let finalSignal = 'hold';
    let confidence = 0;

    if (buySignals.length > sellSignals.length) {
      finalSignal = 'buy';
      confidence = buySignals.reduce((sum, s) => sum + s.confidence, 0) / buySignals.length;
    } else if (sellSignals.length > buySignals.length) {
      finalSignal = 'sell';
      confidence = sellSignals.reduce((sum, s) => sum + s.confidence, 0) / sellSignals.length;
    }

    return {
      signal: finalSignal,
      confidence: Math.min(confidence, 1.0),
      reason: 'combined_analysis',
      components: { sma: smaSignal, rsi: rsiSignal, bb: bbSignal },
      buyCount: buySignals.length,
      sellCount: sellSignals.length,
      totalSignals: validSignals.length
    };
  }
}

module.exports = TradingAlgorithms;