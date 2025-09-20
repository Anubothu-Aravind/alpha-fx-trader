# AlphaFX Trader - Trading Logic Flow

## Algorithm Overview

AlphaFX Trader implements three primary technical analysis algorithms for generating trading signals:

1. **Simple Moving Average (SMA) Crossover**
2. **Relative Strength Index (RSI)**
3. **Bollinger Bands**

## Algorithm Details

### 1. Simple Moving Average (SMA) Crossover

#### Logic
- **Short SMA**: 10-period moving average
- **Long SMA**: 30-period moving average
- **Bullish Signal**: Short SMA crosses above Long SMA → BUY
- **Bearish Signal**: Short SMA crosses below Long SMA → SELL

#### Implementation
```python
def sma_crossover_signal(self, prices, short_period=10, long_period=30):
    short_sma = calculate_sma(prices, short_period)
    long_sma = calculate_sma(prices, long_period)
    
    # Check for crossover
    if short_sma[-2] <= long_sma[-2] and short_sma[-1] > long_sma[-1]:
        return 'BUY'  # Bullish crossover
    elif short_sma[-2] >= long_sma[-2] and short_sma[-1] < long_sma[-1]:
        return 'SELL'  # Bearish crossover
    
    return None
```

#### Signal Conditions
- **BUY Signal**: Generated when short SMA crosses above long SMA
- **SELL Signal**: Generated when short SMA crosses below long SMA
- **No Signal**: When SMAs are parallel or no crossover occurs

### 2. Relative Strength Index (RSI)

#### Logic
- **Period**: 14-period RSI calculation
- **Oversold Level**: RSI ≤ 30 → BUY signal
- **Overbought Level**: RSI ≥ 70 → SELL signal
- **Neutral Zone**: 30 < RSI < 70 → No signal

#### Implementation
```python
def rsi_signal(self, prices, period=14, oversold=30, overbought=70):
    rsi_values = calculate_rsi(prices, period)
    current_rsi = rsi_values[-1]
    
    if current_rsi <= oversold:
        return 'BUY'  # Oversold condition
    elif current_rsi >= overbought:
        return 'SELL'  # Overbought condition
    
    return None
```

#### RSI Calculation
1. Calculate price changes (gains/losses)
2. Calculate average gains and losses over period
3. Calculate RS (Relative Strength) = Average Gain / Average Loss
4. Calculate RSI = 100 - (100 / (1 + RS))

### 3. Bollinger Bands

#### Logic
- **Period**: 20-period moving average
- **Standard Deviation**: 2 standard deviations
- **BUY Signal**: Price touches lower band (oversold)
- **SELL Signal**: Price touches upper band (overbought)

#### Implementation
```python
def bollinger_bands_signal(self, prices, period=20, std_dev=2):
    upper, middle, lower = calculate_bollinger_bands(prices, period, std_dev)
    current_price = prices[-1]
    
    if current_price <= lower[-1]:
        return 'BUY'  # Price at lower band
    elif current_price >= upper[-1]:
        return 'SELL'  # Price at upper band
    
    return None
```

## Consensus Algorithm

### Multi-Algorithm Decision Making
The system combines signals from all three algorithms to generate a consensus:

```python
def generate_combined_signal(self, prices):
    signals = {
        'sma': self.sma_crossover_signal(prices),
        'rsi': self.rsi_signal(prices),
        'bollinger': self.bollinger_bands_signal(prices),
        'consensus': None
    }
    
    # Count buy/sell signals
    buy_signals = sum(1 for signal in signals.values() if signal == 'BUY')
    sell_signals = sum(1 for signal in signals.values() if signal == 'SELL')
    
    # Generate consensus (need 2+ agreeing signals)
    if buy_signals >= 2:
        signals['consensus'] = 'BUY'
    elif sell_signals >= 2:
        signals['consensus'] = 'SELL'
    
    return signals
```

### Consensus Rules
- **BUY Consensus**: 2 or more algorithms generate BUY signals
- **SELL Consensus**: 2 or more algorithms generate SELL signals
- **No Action**: Less than 2 algorithms agree or mixed signals

## Trading Execution Flow

### 1. Price Analysis Cycle
```
1. Receive new price data
2. Update price history buffer
3. Calculate technical indicators
4. Generate individual algorithm signals
5. Determine consensus signal
6. Execute trade if consensus exists
```

### 2. Trade Execution Process
```
1. Check consensus signal (BUY/SELL)
2. Validate trading conditions:
   - Auto trading enabled
   - Volume limit not exceeded
   - Valid price data available
3. Calculate position size (default: 1000 units)
4. Get current market price (bid/ask)
5. Create trade record
6. Execute trade
7. Update volume tracking
8. Broadcast trade notification
```

### 3. Risk Management Integration
```
1. Check daily volume limit ($10M)
2. Calculate trade value (amount × price)
3. Verify: current_volume + trade_value ≤ limit
4. If limit exceeded:
   - Reject trade
   - Disable auto trading
   - Send notification
5. If within limit:
   - Execute trade
   - Update volume counter
```

## Position Management

### Position Sizing
- **Fixed Size**: 1000 units per trade for demo purposes
- **Percentage Risk**: Future enhancement for risk-based sizing
- **Maximum Position**: No current limit (can be added)

### Trade Lifecycle
1. **Signal Generation**: Algorithm consensus triggers trade
2. **Order Placement**: Market order at current price
3. **Execution Confirmation**: Trade recorded in database
4. **Position Tracking**: Monitor unrealized P&L
5. **Position Closing**: Opposite signal triggers close

## Backtesting Logic

### Historical Simulation Process
```python
def run_backtest(self, pair, start_date, end_date, initial_balance):
    # Generate historical price data
    historical_data = generate_historical_data(pair, start_date, end_date)
    
    # Initialize backtesting variables
    balance = initial_balance
    position = 0  # No position
    trades = []
    
    # Process each price point
    for i in range(30, len(historical_data)):
        prices = extract_prices(historical_data[:i+1])
        signals = generate_combined_signal(prices)
        
        # Execute trades based on signals
        if signals['consensus'] == 'BUY' and position <= 0:
            # Close short, open long
        elif signals['consensus'] == 'SELL' and position >= 0:
            # Close long, open short
            
        # Track equity curve
        calculate_unrealized_pnl()
        
    return backtest_results
```

### Performance Metrics
- **Total Return**: (Final Balance - Initial Balance) / Initial Balance
- **Win Rate**: Winning Trades / Total Trades
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Trade Count**: Number of completed trades
- **Profit Factor**: Gross Profit / Gross Loss

## Real-Time Trading Loop

### Auto Trading Cycle
```python
def trading_loop(self):
    while is_running and auto_trading_enabled:
        for pair in CURRENCY_PAIRS:
            # Get recent price data
            prices = get_prices_for_algorithm(pair, 50)
            
            # Generate trading signals
            signals = generate_combined_signal(prices)
            
            # Execute based on consensus
            if signals['consensus'] in ['BUY', 'SELL']:
                execute_trade(pair, signals['consensus'], 1000)
                
        # Wait 30 seconds before next analysis
        sleep(30)
```

### Signal Frequency
- **Analysis Interval**: Every 30 seconds
- **Price Updates**: Every 2 seconds
- **Minimum Data**: 30 price points for analysis
- **Indicator Calculation**: Real-time with each new price

## Configuration Parameters

### Algorithm Settings
```python
# Moving Average periods
SMA_SHORT_PERIOD = 10
SMA_LONG_PERIOD = 30

# RSI settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Bollinger Bands settings
BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2
```

### Risk Management
```python
# Volume limits
MAX_TRADING_VOLUME = 10_000_000  # $10M daily limit
DEFAULT_POSITION_SIZE = 1000     # Units per trade
```

### Timing Configuration
```python
# Trading loop timing
ANALYSIS_INTERVAL = 30    # seconds
PRICE_UPDATE_INTERVAL = 2 # seconds
MINIMUM_DATA_POINTS = 30  # for analysis
```

## Signal Quality and Filtering

### Signal Validation
- **Data Quality**: Minimum 30 data points required
- **Price Validity**: Non-zero, positive prices only
- **Timestamp Validation**: Recent data within acceptable window
- **Indicator Convergence**: All indicators must calculate successfully

### False Signal Reduction
- **Consensus Requirement**: Multiple algorithms must agree
- **Minimum Movement**: Price change threshold (future enhancement)
- **Time-based Filtering**: Minimum time between signals (future enhancement)
- **Volatility Adjustment**: Signal strength based on market volatility (future enhancement)