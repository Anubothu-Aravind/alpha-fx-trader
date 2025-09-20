# AlphaFX Trader - Trading Logic Flow

## Overview

The AlphaFX Trader implements a sophisticated algorithmic trading system that combines multiple technical indicators to generate buy/sell signals with automated execution and risk management.

## Trading Algorithm Components

### 1. Simple Moving Average (SMA) Crossover Strategy

**Logic:**
- Calculates short-period SMA (default: 10 periods)
- Calculates long-period SMA (default: 50 periods)
- Detects crossover events between the two SMAs

**Signals:**
- **Golden Cross**: Short SMA crosses above Long SMA → BUY signal
- **Death Cross**: Short SMA crosses below Long SMA → SELL signal
- **Hold**: No crossover detected → HOLD signal

**Confidence Calculation:**
```javascript
confidence = Math.min(((shortSMA - longSMA) / longSMA) * 100, 1.0)
```

**Implementation Flow:**
```
1. Maintain price history buffer (max 200 data points)
2. Calculate current and previous SMA values
3. Compare current vs previous to detect crossover
4. Generate signal with confidence based on SMA divergence
```

### 2. Relative Strength Index (RSI) Strategy

**Logic:**
- Calculates RSI over specified period (default: 14)
- Uses average gains vs average losses formula
- Identifies overbought/oversold conditions

**Signals:**
- **RSI > 70**: Overbought condition → SELL signal
- **RSI < 30**: Oversold condition → BUY signal
- **30 ≤ RSI ≤ 70**: Neutral → HOLD signal

**RSI Calculation:**
```javascript
RS = Average Gains / Average Losses
RSI = 100 - (100 / (1 + RS))
```

**Confidence Calculation:**
- For overbought: `(RSI - 70) / (100 - 70)`
- For oversold: `(30 - RSI) / 30`

### 3. Bollinger Bands Strategy

**Logic:**
- Calculates moving average (middle band)
- Calculates standard deviation
- Creates upper and lower bands at ±2 standard deviations

**Signals:**
- **Price > Upper Band**: Overbought → SELL signal
- **Price < Lower Band**: Oversold → BUY signal
- **Lower Band ≤ Price ≤ Upper Band**: Within range → HOLD signal

**Band Calculation:**
```javascript
Middle Band = SMA(20 periods)
Upper Band = Middle Band + (2 * Standard Deviation)
Lower Band = Middle Band - (2 * Standard Deviation)
```

### 4. Combined Signal Analysis

**Signal Aggregation Logic:**
```
1. Calculate individual signals from all algorithms
2. Filter signals with confidence > 0
3. Separate into BUY and SELL signals
4. Apply voting mechanism:
   - If BUY signals > SELL signals → BUY
   - If SELL signals > BUY signals → SELL
   - Otherwise → HOLD
5. Calculate weighted confidence average
```

**Combined Confidence:**
```javascript
finalConfidence = averageConfidence(validSignals) // capped at 1.0
```

## Trading Execution Flow

### 1. Price Data Processing
```
FX Simulator generates price update
↓
Add to algorithm price history buffer
↓
Trigger algorithm analysis
↓
Update position P&L calculations
```

### 2. Signal Generation
```
Every 5 seconds:
↓
For each currency pair:
  ↓
  Get combined trading signal
  ↓
  Check signal confidence (must be > 0.6)
  ↓
  Proceed to execution evaluation
```

### 3. Risk Management Checks
```
Before executing any trade:
↓
Check daily volume limit ($10M)
↓
Validate position size limits
↓
Check symbol exposure limits
↓
Verify trade value constraints
```

**Risk Limits:**
- Maximum daily volume: $10,000,000
- Maximum single trade: 10% of daily limit
- Maximum symbol exposure: 20% of daily limit
- Minimum trade value: $1,000

### 4. Trade Execution Logic
```
Signal received with sufficient confidence
↓
Calculate position size based on:
  - Base position size ($10,000)
  - Signal confidence multiplier
  - Risk management constraints
↓
Check existing position:
  - BUY: Execute if no position or short position
  - SELL: Execute if no position or long position
↓
Execute trade:
  - BUY at ASK price
  - SELL at BID price
↓
Update database records:
  - Insert trade record
  - Update position record
  - Update daily statistics
↓
Broadcast trade execution event
```

### 5. Position Management
```
Price update received
↓
Update unrealized P&L for all positions:
  PnL = (Current Price - Average Price) × Quantity
↓
Store updated P&L in database
↓
Check for stop-loss triggers (future enhancement)
```

### 6. Volume Limit Enforcement
```
Before each trade execution:
↓
Check: Current Daily Volume + Trade Value ≤ $10M
↓
If exceeded:
  - Stop trading engine
  - Log volume limit reached
  - Prevent further trades until next day
```

## Algorithm Parameter Configuration

### Default Parameters
```javascript
SMA Crossover:
- Short Period: 10 (configurable via SMA_SHORT_PERIOD)
- Long Period: 50 (configurable via SMA_LONG_PERIOD)

RSI:
- Period: 14 (configurable via RSI_PERIOD)
- Overbought: 70 (configurable via RSI_OVERBOUGHT)
- Oversold: 30 (configurable via RSI_OVERSOLD)

Bollinger Bands:
- Period: 20 (configurable via BOLLINGER_PERIOD)
- Standard Deviations: 2 (configurable via BOLLINGER_STD_DEV)

Execution:
- Minimum Confidence: 0.6 (hardcoded)
- Update Interval: 5 seconds (configurable via ALGORITHM_UPDATE_INTERVAL)
```

## Data Requirements

### Historical Data Buffer
```javascript
Price History per Symbol:
- Maximum 200 data points
- Rolling buffer (FIFO when full)
- Each data point contains:
  - timestamp
  - price (mid-price)
  - high, low (for volatility)
  - volume
```

### Signal Storage
```javascript
Algorithm Signals Table:
- timestamp: When signal was generated
- symbol: Currency pair
- algorithm: Which algorithm generated signal
- signal: buy/sell/hold
- confidence: Signal strength (0-1)
- parameters: JSON of algorithm parameters used
```

## Performance Optimizations

### 1. Efficient Calculations
- Use sliding window calculations for moving averages
- Cache intermediate results where possible
- Limit historical data retention to minimum required

### 2. Database Optimizations
- Index frequently queried columns
- Batch database operations
- Use prepared statements

### 3. Memory Management
- Circular buffers for price history
- Garbage collection friendly data structures
- Event-driven architecture to minimize polling

## Error Handling

### Algorithm Errors
```javascript
try {
  signal = algorithms.getCombinedSignal(symbol);
} catch (error) {
  console.error(`Error evaluating ${symbol}:`, error);
  // Continue with next symbol, don't stop entire process
}
```

### Execution Errors
```javascript
try {
  await executeTrade(tradeDetails);
} catch (error) {
  console.error('Trade execution failed:', error);
  // Log error but don't stop trading engine
}
```

### Database Errors
```javascript
try {
  await database.operation();
} catch (error) {
  console.error('Database operation failed:', error);
  // Implement retry logic or graceful degradation
}
```

## Future Enhancements

1. **Stop-Loss/Take-Profit Orders**
2. **More Advanced Algorithms** (MACD, Stochastic)
3. **Machine Learning Integration**
4. **News Event Processing**
5. **Multi-Timeframe Analysis**
6. **Portfolio-Level Risk Management**
7. **Real External Data Sources**
8. **Advanced Order Types** (Limit, Market, Stop)