# Trading Logic Documentation

## Overview

The AlphaFX Trader implements sophisticated trading strategies combining technical analysis, machine learning predictions, and robust risk management. The system supports both automated and manual trading with comprehensive backtesting capabilities.

## Trading Strategy Framework

### Strategy Architecture

```
Market Data → Technical Indicators → Signal Generation → Risk Assessment → Trade Execution
     ↓              ↓                    ↓                 ↓               ↓
Historical     SMA, EMA, RSI         Buy/Sell         Position Size    Order Management
Live Rates     MACD, BB, ATR         Hold Signals     Stop/Target      Portfolio Update
```

## Technical Analysis Strategies

### 1. Simple Moving Average (SMA) Crossover

**Concept**: When a short-period moving average crosses above/below a long-period moving average, it signals a trend change.

**Implementation**:
```python
def sma_crossover_strategy(prices, fast_period=10, slow_period=30):
    fast_sma = calculate_sma(prices, fast_period)
    slow_sma = calculate_sma(prices, slow_period)
    
    signals = []
    for i in range(1, len(prices)):
        if fast_sma[i-1] <= slow_sma[i-1] and fast_sma[i] > slow_sma[i]:
            signals.append(('buy', i, fast_sma[i]))
        elif fast_sma[i-1] >= slow_sma[i-1] and fast_sma[i] < slow_sma[i]:
            signals.append(('sell', i, fast_sma[i]))
    
    return signals
```

**Parameters**:
- `fast_period`: Short-term SMA period (default: 10)
- `slow_period`: Long-term SMA period (default: 30)

**Signal Quality**:
- **Strength**: Based on distance between moving averages
- **Reliability**: Higher in trending markets, weaker in sideways markets
- **Lag**: Moderate (waits for confirmation)

**Risk Management**:
- Stop Loss: 2% from entry price
- Take Profit: 4% from entry price
- Maximum position size: 10% of capital

### 2. Relative Strength Index (RSI) Mean Reversion

**Concept**: RSI identifies overbought (>70) and oversold (<30) conditions, suggesting price reversals.

**Implementation**:
```python
def rsi_mean_reversion(prices, period=14, overbought=70, oversold=30):
    rsi_values = calculate_rsi(prices, period)
    
    signals = []
    for i, rsi in enumerate(rsi_values):
        if rsi < oversold:
            signals.append(('buy', i, prices[i]))  # Oversold - expect bounce
        elif rsi > overbought:
            signals.append(('sell', i, prices[i]))  # Overbought - expect decline
    
    return signals
```

**Parameters**:
- `period`: RSI calculation period (default: 14)
- `overbought`: Upper threshold (default: 70)
- `oversold`: Lower threshold (default: 30)

**Signal Characteristics**:
- **Timing**: Excellent for market turning points
- **False Signals**: Common in strong trends
- **Optimization**: Dynamic thresholds based on market volatility

### 3. Bollinger Bands Strategy

**Concept**: Price touching or breaking Bollinger Bands suggests continuation or reversal.

**Implementation**:
```python
def bollinger_bands_strategy(prices, period=20, std_dev=2.0):
    middle, upper, lower = calculate_bollinger_bands(prices, period, std_dev)
    
    signals = []
    for i in range(1, len(prices)):
        # Price touching lower band - potential buy
        if prices[i] <= lower[i] and prices[i-1] > lower[i-1]:
            signals.append(('buy', i, prices[i]))
        
        # Price touching upper band - potential sell
        elif prices[i] >= upper[i] and prices[i-1] < upper[i-1]:
            signals.append(('sell', i, prices[i]))
        
        # Mean reversion to middle band
        elif prices[i-1] <= middle[i-1] and prices[i] > middle[i]:
            signals.append(('buy', i, prices[i]))
        elif prices[i-1] >= middle[i-1] and prices[i] < middle[i]:
            signals.append(('sell', i, prices[i]))
    
    return signals
```

**Band Interpretation**:
- **Upper Band**: Resistance level, potential sell zone
- **Lower Band**: Support level, potential buy zone
- **Middle Band**: Dynamic support/resistance
- **Band Width**: Market volatility indicator

### 4. MACD (Moving Average Convergence Divergence)

**Concept**: MACD line crossing signal line indicates momentum changes.

**Implementation**:
```python
def macd_strategy(prices, fast=12, slow=26, signal=9):
    macd_line, signal_line, histogram = calculate_macd(prices, fast, slow, signal)
    
    signals = []
    for i in range(1, len(prices)):
        # MACD crosses above signal line - bullish
        if macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i]:
            signals.append(('buy', i, prices[i]))
        
        # MACD crosses below signal line - bearish
        elif macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i]:
            signals.append(('sell', i, prices[i]))
    
    return signals
```

**Components**:
- **MACD Line**: Fast EMA - Slow EMA
- **Signal Line**: EMA of MACD line
- **Histogram**: MACD - Signal (momentum strength)

### 5. Multi-Indicator Strategy

**Concept**: Combines multiple indicators for higher confidence signals.

**Implementation**:
```python
def multi_indicator_strategy(price_data, parameters):
    indicators = calculate_all_indicators(price_data, parameters)
    
    for i in range(len(price_data)):
        votes = []
        
        # SMA vote
        if indicators['sma_fast'][i] > indicators['sma_slow'][i]:
            votes.append(1)  # Bullish
        else:
            votes.append(-1)  # Bearish
        
        # RSI vote
        if indicators['rsi'][i] < 30:
            votes.append(1)  # Oversold
        elif indicators['rsi'][i] > 70:
            votes.append(-1)  # Overbought
        
        # MACD vote
        if indicators['macd_line'][i] > indicators['macd_signal'][i]:
            votes.append(1)  # Bullish momentum
        else:
            votes.append(-1)  # Bearish momentum
        
        # Generate signal based on consensus
        total_vote = sum(votes)
        if total_vote >= 2:
            yield ('buy', i, calculate_strength(votes))
        elif total_vote <= -2:
            yield ('sell', i, calculate_strength(votes))
```

**Voting System**:
- Each indicator contributes one vote (+1 bullish, -1 bearish)
- Minimum 2 votes required for signal generation
- Signal strength based on consensus level

## Machine Learning Strategy

### ML Framework Architecture

```
Feature Engineering → Model Training → Prediction → Signal Generation → Risk Assessment
        ↓                  ↓            ↓              ↓                ↓
Price History        LSTM/RF/SVM    Probability    Buy/Sell/Hold    Position Sizing
Technical Indicators   Validation    Confidence     Signal Strength   Risk Controls
Market Sentiment      Optimization   Uncertainty    Timing Score      Portfolio Balance
```

### Feature Engineering

**Price Features**:
- Price momentum (multiple timeframes)
- Volatility measures
- Support/resistance levels
- Candlestick patterns

**Technical Features**:
- Normalized indicator values
- Indicator crossovers
- Divergence patterns
- Multi-timeframe confirmation

**Market Structure Features**:
- Trend strength
- Market regime classification
- Volume profile
- Time-based patterns

**Implementation**:
```python
def engineer_features(price_data, lookback_window=60):
    features = []
    
    # Price momentum features
    for period in [5, 10, 20]:
        momentum = (price_data['close'] / price_data['close'].shift(period) - 1)
        features.append(momentum)
    
    # Volatility features
    returns = price_data['close'].pct_change()
    volatility = returns.rolling(20).std()
    features.append(volatility)
    
    # Technical indicator features
    indicators = calculate_all_indicators(price_data)
    for indicator_name, values in indicators.items():
        normalized_values = normalize_indicator(values)
        features.append(normalized_values)
    
    return np.column_stack(features)
```

### Model Architecture

**LSTM Model (Simulated)**:
- Input: 60-period lookback window
- Hidden layers: 2 LSTM layers (50, 25 units)
- Output: 3 classes (Buy, Sell, Hold)
- Dropout: 0.2 for regularization

**Random Forest (Simulated)**:
- Features: 20 engineered features
- Trees: 100 estimators
- Max depth: 10
- Feature importance tracking

**Ensemble Approach**:
- Combines multiple model predictions
- Weighted voting based on recent performance
- Confidence scoring for each prediction

### Prediction Logic

```python
def generate_ml_prediction(features, models):
    predictions = []
    confidences = []
    
    for model in models:
        prediction = model.predict(features)
        confidence = model.predict_proba(features).max()
        predictions.append(prediction)
        confidences.append(confidence)
    
    # Ensemble prediction
    ensemble_prediction = weighted_vote(predictions, confidences)
    ensemble_confidence = calculate_ensemble_confidence(confidences)
    
    return ensemble_prediction, ensemble_confidence
```

**Signal Generation from ML**:
- Probability threshold: 0.7 for signal generation
- Confidence threshold: 0.6 for execution
- Signal strength: probability * confidence
- Hold signals for low-confidence predictions

## Risk Management System

### Position Sizing

**Capital Allocation Model**:
```python
def calculate_position_size(capital, signal_strength, risk_per_trade=0.02):
    # Base position size (2% risk per trade)
    base_risk = capital * risk_per_trade
    
    # Adjust based on signal strength
    adjusted_risk = base_risk * signal_strength
    
    # Calculate position size based on stop loss
    stop_loss_distance = calculate_stop_loss_distance()
    position_size = adjusted_risk / stop_loss_distance
    
    return min(position_size, capital * 0.1)  # Max 10% of capital
```

**Risk Parameters**:
- Maximum position size: 10% of capital
- Risk per trade: 2% of capital
- Maximum daily loss: 5% of capital
- Maximum open positions: 5 per pair

### Stop Loss and Take Profit

**Dynamic Stop Loss**:
```python
def calculate_dynamic_stop_loss(entry_price, volatility, action):
    # Base stop loss: 2% of entry price
    base_stop = 0.02
    
    # Adjust based on market volatility
    volatility_adjustment = volatility * 2
    adjusted_stop = base_stop + volatility_adjustment
    
    # Calculate stop loss price
    if action == 'buy':
        stop_loss = entry_price * (1 - adjusted_stop)
    else:
        stop_loss = entry_price * (1 + adjusted_stop)
    
    return stop_loss
```

**Take Profit Targets**:
- Risk-reward ratio: 1:2 (minimum)
- Dynamic targets based on market conditions
- Partial profit taking at multiple levels

### Portfolio Risk Controls

**Exposure Limits**:
- Maximum exposure per pair: 20% of capital
- Maximum correlation exposure: 30% of capital
- Currency exposure limits by base/quote currency

**Drawdown Protection**:
- Maximum drawdown: 15% from peak
- Position reduction at 10% drawdown
- Trading halt at 15% drawdown

## Backtesting Engine

### Backtesting Framework

```python
async def run_backtest(pair, start_date, end_date, strategy, initial_capital):
    # Initialize portfolio
    portfolio = BacktestPortfolio(initial_capital)
    
    # Get historical data
    data = await get_historical_data(pair, start_date, end_date)
    
    # Generate signals
    signals = strategy.generate_signals(data)
    
    # Execute trades
    for signal in signals:
        if should_execute_signal(signal, portfolio):
            trade = execute_backtest_trade(signal, portfolio)
            portfolio.add_trade(trade)
    
    # Calculate performance metrics
    return calculate_performance_metrics(portfolio)
```

### Performance Metrics

**Return Metrics**:
- Total return: (Final Capital - Initial Capital) / Initial Capital
- Annualized return: Total return adjusted for time period
- Risk-adjusted return: Return per unit of risk

**Risk Metrics**:
- Maximum drawdown: Peak-to-trough decline
- Volatility: Standard deviation of returns
- Sharpe ratio: (Return - Risk-free rate) / Volatility
- Sortino ratio: Return / Downside deviation

**Trade Metrics**:
- Win rate: Winning trades / Total trades
- Profit factor: Gross profit / Gross loss
- Average win/loss: Mean profit/loss per winning/losing trade
- Consecutive wins/losses: Longest winning/losing streaks

### Realistic Execution Simulation

**Slippage Modeling**:
```python
def calculate_slippage(market_price, volume, market_conditions):
    base_slippage = 0.0001  # 1 pip base
    volume_impact = volume * 0.00005  # Volume impact
    volatility_impact = market_conditions.volatility * 0.0002
    
    total_slippage = base_slippage + volume_impact + volatility_impact
    return random.uniform(0.5, 1.5) * total_slippage
```

**Commission Structure**:
- Fixed commission: $0.02 per 1000 units
- Spread costs: Bid-ask spread
- Financing costs for overnight positions

## Strategy Performance Optimization

### Parameter Optimization

**Grid Search**:
```python
def optimize_strategy_parameters(strategy, data, parameter_ranges):
    best_params = None
    best_performance = -float('inf')
    
    for params in generate_parameter_combinations(parameter_ranges):
        performance = backtest_with_parameters(strategy, data, params)
        if performance.sharpe_ratio > best_performance:
            best_performance = performance.sharpe_ratio
            best_params = params
    
    return best_params, best_performance
```

**Walk-Forward Analysis**:
- Training period: 6 months
- Testing period: 1 month
- Rolling window optimization
- Out-of-sample performance validation

### Regime Detection

**Market Regime Classification**:
- Trending vs. Ranging markets
- High vs. Low volatility periods
- Bull vs. Bear market phases
- Strategy selection based on regime

**Adaptive Parameters**:
- Dynamic indicator periods
- Volatility-adjusted thresholds
- Regime-specific signal filters

## Real-Time Trading Execution

### Order Management

**Order Types**:
- Market orders: Immediate execution
- Limit orders: Price-specific execution
- Stop orders: Risk management exits
- OCO orders: One-cancels-other

**Execution Logic**:
```python
async def execute_trade(signal, current_rate):
    # Pre-trade validation
    validate_trade_parameters(signal)
    check_risk_limits(signal)
    
    # Calculate execution price
    execution_price = calculate_execution_price(current_rate, signal.action)
    
    # Execute trade
    trade = await trading_engine.execute_trade(
        pair=signal.pair,
        action=signal.action,
        volume=signal.volume,
        price=execution_price
    )
    
    # Post-trade processing
    update_positions(trade)
    log_trade_execution(trade)
    
    return trade
```

### Position Monitoring

**Real-Time Updates**:
- Mark-to-market P&L calculation
- Stop loss/take profit monitoring
- Risk metric updates
- Performance tracking

**Auto-Exit Conditions**:
- Stop loss triggers
- Take profit targets
- Time-based exits (max holding period)
- Risk limit breaches

This comprehensive trading logic framework provides the foundation for sophisticated, automated FX trading while maintaining robust risk management and performance optimization capabilities.