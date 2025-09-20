"""
Backtesting engine for trading strategies.
Tests strategy performance on historical data with realistic execution simulation.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import logging

from models import (
    BacktestRequest, BacktestResult, TradeRecord, TradeAction, 
    SignalType, MarketData as MarketDataModel
)
from utils import calculate_all_indicators, PriceData, SignalGenerator
from db import SessionLocal, MarketData

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Trade record for backtesting."""
    timestamp: datetime
    pair: str
    action: TradeAction
    volume: float
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: float = 0.0
    commission: float = 0.0
    strategy_signal: str = ""
    trade_id: str = ""
    
    def __post_init__(self):
        if not self.trade_id:
            self.trade_id = str(uuid.uuid4())

@dataclass
class BacktestPosition:
    """Position tracking for backtesting."""
    pair: str
    action: TradeAction
    volume: float
    entry_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_hours: int = 168  # 1 week default
    trade_id: str = ""
    
    def __post_init__(self):
        if not self.trade_id:
            self.trade_id = str(uuid.uuid4())
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate current P&L for the position."""
        if self.action == TradeAction.BUY:
            return (current_price - self.entry_price) * self.volume
        else:
            return (self.entry_price - current_price) * self.volume
    
    def should_exit(self, current_price: float, current_time: datetime) -> Tuple[bool, str]:
        """Check if position should be exited."""
        # Check stop loss
        if self.stop_loss:
            if self.action == TradeAction.BUY and current_price <= self.stop_loss:
                return True, "stop_loss"
            elif self.action == TradeAction.SELL and current_price >= self.stop_loss:
                return True, "stop_loss"
        
        # Check take profit
        if self.take_profit:
            if self.action == TradeAction.BUY and current_price >= self.take_profit:
                return True, "take_profit"
            elif self.action == TradeAction.SELL and current_price <= self.take_profit:
                return True, "take_profit"
        
        # Check max holding time
        holding_time = current_time - self.entry_time
        if holding_time.total_seconds() > self.max_holding_hours * 3600:
            return True, "max_holding_time"
        
        return False, ""

class StrategyEngine:
    """Strategy execution engine for backtesting."""
    
    @staticmethod
    def get_signals(strategy: str, price_data: List[PriceData], 
                   parameters: Dict[str, Any]) -> List[Tuple[datetime, SignalType, float, str]]:
        """
        Get trading signals from strategy.
        
        Returns:
            List of (timestamp, signal, strength, reason) tuples
        """
        if len(price_data) < 50:
            return []
        
        closes = [p.close for p in price_data]
        highs = [p.high for p in price_data]
        lows = [p.low for p in price_data]
        timestamps = [p.timestamp for p in price_data]
        
        signals = []
        
        if strategy == "sma_crossover":
            # SMA Crossover strategy
            fast_period = parameters.get('sma_fast', 10)
            slow_period = parameters.get('sma_slow', 30)
            
            sma_signals = SignalGenerator.sma_crossover(closes, fast_period, slow_period)
            
            for i, signal in enumerate(sma_signals):
                if signal != 'hold' and i < len(timestamps):
                    signal_type = SignalType.BUY if signal == 'buy' else SignalType.SELL
                    strength = 0.7  # Default strength for SMA crossover
                    signals.append((timestamps[i], signal_type, strength, "sma_crossover"))
        
        elif strategy == "rsi_mean_reversion":
            # RSI Mean Reversion strategy
            rsi_period = parameters.get('rsi_period', 14)
            overbought = parameters.get('rsi_overbought', 70)
            oversold = parameters.get('rsi_oversold', 30)
            
            rsi_signals = SignalGenerator.rsi_signals(closes, rsi_period, overbought, oversold)
            
            for i, signal in enumerate(rsi_signals):
                if signal != 'hold' and i < len(timestamps):
                    signal_type = SignalType.BUY if signal == 'buy' else SignalType.SELL
                    strength = 0.6  # RSI signals are medium strength
                    signals.append((timestamps[i], signal_type, strength, "rsi_mean_reversion"))
        
        elif strategy == "bollinger_bands":
            # Bollinger Bands strategy
            bb_period = parameters.get('bb_period', 20)
            bb_std = parameters.get('bb_std_dev', 2.0)
            
            bb_signals = SignalGenerator.bollinger_signals(closes, bb_period, bb_std)
            
            for i, signal in enumerate(bb_signals):
                if signal != 'hold' and i < len(timestamps):
                    signal_type = SignalType.BUY if signal == 'buy' else SignalType.SELL
                    strength = 0.65
                    signals.append((timestamps[i], signal_type, strength, "bollinger_bands"))
        
        elif strategy == "macd":
            # MACD strategy
            fast_period = parameters.get('macd_fast', 12)
            slow_period = parameters.get('macd_slow', 26)
            signal_period = parameters.get('macd_signal', 9)
            
            macd_signals = SignalGenerator.macd_signals(closes, fast_period, slow_period, signal_period)
            
            for i, signal in enumerate(macd_signals):
                if signal != 'hold' and i < len(timestamps):
                    signal_type = SignalType.BUY if signal == 'buy' else SignalType.SELL
                    strength = 0.7
                    signals.append((timestamps[i], signal_type, strength, "macd"))
        
        elif strategy == "multi_indicator":
            # Combined multi-indicator strategy
            indicators = calculate_all_indicators(price_data, parameters)
            
            for i in range(max(30, len(price_data) - 100), len(price_data)):  # Skip early periods
                if i >= len(timestamps):
                    break
                
                signal_votes = []
                
                # SMA vote
                if (i > 0 and not np.isnan(indicators['sma_fast'][i]) and 
                    not np.isnan(indicators['sma_slow'][i])):
                    if indicators['sma_fast'][i] > indicators['sma_slow'][i]:
                        signal_votes.append(1)  # Bullish
                    else:
                        signal_votes.append(-1)  # Bearish
                
                # RSI vote
                if not np.isnan(indicators['rsi'][i]):
                    rsi_val = indicators['rsi'][i]
                    if rsi_val < 30:
                        signal_votes.append(1)  # Oversold - buy
                    elif rsi_val > 70:
                        signal_votes.append(-1)  # Overbought - sell
                
                # MACD vote
                if (not np.isnan(indicators['macd_line'][i]) and 
                    not np.isnan(indicators['macd_signal'][i])):
                    if indicators['macd_line'][i] > indicators['macd_signal'][i]:
                        signal_votes.append(1)
                    else:
                        signal_votes.append(-1)
                
                # Determine final signal
                if len(signal_votes) >= 2:
                    total_vote = sum(signal_votes)
                    if total_vote >= 2:
                        strength = min(len([v for v in signal_votes if v > 0]) / len(signal_votes), 0.9)
                        signals.append((timestamps[i], SignalType.BUY, strength, "multi_indicator"))
                    elif total_vote <= -2:
                        strength = min(len([v for v in signal_votes if v < 0]) / len(signal_votes), 0.9)
                        signals.append((timestamps[i], SignalType.SELL, strength, "multi_indicator"))
        
        return signals

class Backtester:
    """Backtesting engine for trading strategies."""
    
    def __init__(self):
        self.commission_rate = 0.0002  # 0.02% commission
        self.spread_cost = 0.0001  # 0.01% spread cost
        self.slippage_factor = 0.0001  # 0.01% slippage
    
    async def run_backtest(self, pair: str, start_date: datetime, end_date: datetime,
                          strategy: str, initial_capital: float = 10000,
                          parameters: Optional[Dict[str, Any]] = None) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            pair: Currency pair to backtest
            start_date: Start date for backtest
            end_date: End date for backtest
            strategy: Strategy name
            initial_capital: Starting capital
            parameters: Strategy parameters
            
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest for {pair} from {start_date} to {end_date}")
        
        if parameters is None:
            parameters = self._get_default_parameters(strategy)
        
        # Get historical data
        historical_data = await self._get_historical_data(pair, start_date, end_date)
        
        if len(historical_data) < 50:
            logger.warning(f"Insufficient data for backtesting {pair}")
            return self._create_empty_result(pair, start_date, end_date, strategy, initial_capital)
        
        # Run simulation
        result = await self._simulate_trading(
            pair, historical_data, strategy, initial_capital, parameters
        )
        
        logger.info(f"Backtest completed for {pair}. Return: {result.total_return_percent:.2f}%")
        return result
    
    def _get_default_parameters(self, strategy: str) -> Dict[str, Any]:
        """Get default parameters for strategy."""
        defaults = {
            "sma_crossover": {
                "sma_fast": 10,
                "sma_slow": 30,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.04
            },
            "rsi_mean_reversion": {
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "stop_loss_pct": 0.015,
                "take_profit_pct": 0.03
            },
            "bollinger_bands": {
                "bb_period": 20,
                "bb_std_dev": 2.0,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.04
            },
            "macd": {
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.05
            },
            "multi_indicator": {
                "sma_fast": 10,
                "sma_slow": 30,
                "rsi_period": 14,
                "bb_period": 20,
                "bb_std_dev": 2.0,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.04
            }
        }
        
        return defaults.get(strategy, defaults["sma_crossover"])
    
    async def _get_historical_data(self, pair: str, start_date: datetime, 
                                 end_date: datetime) -> List[PriceData]:
        """Get historical market data."""
        db = SessionLocal()
        try:
            # Try to get data from database
            data = db.query(MarketData).filter(
                MarketData.pair == pair,
                MarketData.timestamp >= start_date,
                MarketData.timestamp <= end_date
            ).order_by(MarketData.timestamp).all()
            
            if data:
                return [PriceData(
                    timestamp=d.timestamp,
                    open=d.open,
                    high=d.high,
                    low=d.low,
                    close=d.close,
                    volume=d.volume
                ) for d in data]
            else:
                # Generate mock data if no real data available
                return self._generate_mock_data(pair, start_date, end_date)
                
        finally:
            db.close()
    
    def _generate_mock_data(self, pair: str, start_date: datetime, 
                           end_date: datetime) -> List[PriceData]:
        """Generate mock historical data for backtesting."""
        base_prices = {
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2650,
            "USD/JPY": 150.25,
            "AUD/USD": 0.6420,
            "USD/CAD": 1.3750
        }
        
        base_price = base_prices.get(pair, 1.0000)
        current_price = base_price
        
        data = []
        current_time = start_date
        
        while current_time < end_date:
            # Simulate realistic price movement
            daily_volatility = 0.01  # 1% daily volatility
            hourly_volatility = daily_volatility / np.sqrt(24)
            
            # Random walk with slight mean reversion
            change = np.random.normal(0, hourly_volatility)
            mean_reversion = -0.001 * (current_price - base_price) / base_price
            change += mean_reversion
            
            # Add some trend and regime changes
            if np.random.random() < 0.001:  # 0.1% chance of trend change
                trend_change = np.random.normal(0, 0.005)
                change += trend_change
            
            new_price = current_price * (1 + change)
            
            # Create OHLC data
            high = new_price * (1 + abs(np.random.normal(0, hourly_volatility/2)))
            low = new_price * (1 - abs(np.random.normal(0, hourly_volatility/2)))
            open_price = current_price
            close = new_price
            volume = np.random.uniform(1000, 5000)
            
            data.append(PriceData(
                timestamp=current_time,
                open=round(open_price, 5),
                high=round(max(high, open_price, close), 5),
                low=round(min(low, open_price, close), 5),
                close=round(close, 5),
                volume=round(volume, 2)
            ))
            
            current_price = close
            current_time += timedelta(hours=1)
        
        return data
    
    async def _simulate_trading(self, pair: str, historical_data: List[PriceData],
                               strategy: str, initial_capital: float,
                               parameters: Dict[str, Any]) -> BacktestResult:
        """Simulate trading based on strategy signals."""
        capital = initial_capital
        positions: List[BacktestPosition] = []
        completed_trades: List[BacktestTrade] = []
        daily_returns = []
        
        # Track performance metrics
        max_capital = initial_capital
        max_drawdown = 0.0
        daily_pnl_history = []
        
        # Get trading signals
        signals = StrategyEngine.get_signals(strategy, historical_data, parameters)
        signal_index = 0
        
        # Risk management parameters
        max_position_size = parameters.get('max_position_size', 0.1)  # 10% of capital
        stop_loss_pct = parameters.get('stop_loss_pct', 0.02)
        take_profit_pct = parameters.get('take_profit_pct', 0.04)
        
        # Simulate trading day by day
        current_day = historical_data[0].timestamp.date()
        daily_start_capital = capital
        
        for i, data_point in enumerate(historical_data):
            current_time = data_point.timestamp
            current_price = data_point.close
            
            # Track daily returns
            if data_point.timestamp.date() != current_day:
                daily_return = (capital - daily_start_capital) / daily_start_capital
                daily_returns.append({
                    "date": current_day.isoformat(),
                    "return": daily_return,
                    "capital": capital
                })
                daily_pnl_history.append(capital - initial_capital)
                
                current_day = data_point.timestamp.date()
                daily_start_capital = capital
            
            # Update max capital and drawdown
            if capital > max_capital:
                max_capital = capital
            
            current_drawdown = (max_capital - capital) / max_capital
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
            
            # Check for position exits
            positions_to_remove = []
            for pos_idx, position in enumerate(positions):
                should_exit, reason = position.should_exit(current_price, current_time)
                
                if should_exit:
                    # Close position
                    exit_price = self._calculate_exit_price(current_price, position.action)
                    trade = self._close_position(position, exit_price, current_time, reason)
                    completed_trades.append(trade)
                    capital += trade.pnl - trade.commission
                    positions_to_remove.append(pos_idx)
            
            # Remove closed positions
            for idx in reversed(positions_to_remove):
                positions.pop(idx)
            
            # Check for new signals
            while (signal_index < len(signals) and 
                   signals[signal_index][0] <= current_time):
                
                signal_time, signal_type, strength, reason = signals[signal_index]
                
                # Calculate position size
                position_size = self._calculate_position_size(
                    capital, current_price, max_position_size, strength
                )
                
                if position_size > 0:
                    # Check if we can afford this position
                    position_value = position_size * current_price
                    if position_value <= capital * 0.95:  # Keep 5% cash buffer
                        
                        # Create new position
                        entry_price = self._calculate_entry_price(current_price, signal_type)
                        
                        # Calculate stop loss and take profit
                        if signal_type == SignalType.BUY:
                            stop_loss = entry_price * (1 - stop_loss_pct)
                            take_profit = entry_price * (1 + take_profit_pct)
                            action = TradeAction.BUY
                        else:
                            stop_loss = entry_price * (1 + stop_loss_pct)
                            take_profit = entry_price * (1 - take_profit_pct)
                            action = TradeAction.SELL
                        
                        position = BacktestPosition(
                            pair=pair,
                            action=action,
                            volume=position_size,
                            entry_price=entry_price,
                            entry_time=current_time,
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        
                        positions.append(position)
                        
                        # Deduct costs
                        commission = position_value * self.commission_rate
                        capital -= commission
                
                signal_index += 1
        
        # Close any remaining positions at end of backtest
        final_price = historical_data[-1].close
        final_time = historical_data[-1].timestamp
        
        for position in positions:
            exit_price = self._calculate_exit_price(final_price, position.action)
            trade = self._close_position(position, exit_price, final_time, "backtest_end")
            completed_trades.append(trade)
            capital += trade.pnl - trade.commission
        
        # Calculate final metrics
        total_return = capital - initial_capital
        total_return_percent = (total_return / initial_capital) * 100
        
        # Calculate additional metrics
        winning_trades = [t for t in completed_trades if t.pnl > 0]
        losing_trades = [t for t in completed_trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Calculate Sharpe ratio
        if daily_pnl_history:
            daily_returns_pct = [(pnl / initial_capital) for pnl in daily_pnl_history]
            if len(daily_returns_pct) > 1:
                returns_std = np.std(daily_returns_pct)
                avg_return = np.mean(daily_returns_pct)
                sharpe_ratio = (avg_return / returns_std * np.sqrt(252)) if returns_std > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Convert trades to TradeRecord format
        trade_records = []
        for trade in completed_trades:
            trade_records.append(TradeRecord(
                id=trade.trade_id,
                pair=trade.pair,
                action=trade.action,
                volume=trade.volume,
                execution_price=trade.exit_price or trade.entry_price,
                timestamp=trade.exit_timestamp or trade.timestamp,
                pnl=trade.pnl,
                status="executed"
            ))
        
        return BacktestResult(
            pair=pair,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            initial_capital=initial_capital,
            final_capital=capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=max_drawdown * initial_capital,
            max_drawdown_percent=max_drawdown * 100,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=len(completed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            average_win=avg_win,
            average_loss=avg_loss,
            profit_factor=profit_factor,
            trades=trade_records,
            daily_returns=daily_returns
        )
    
    def _calculate_position_size(self, capital: float, price: float, 
                               max_position_pct: float, signal_strength: float) -> float:
        """Calculate position size based on capital and signal strength."""
        max_position_value = capital * max_position_pct
        base_size = max_position_value / price
        
        # Adjust size based on signal strength
        adjusted_size = base_size * signal_strength
        
        return adjusted_size
    
    def _calculate_entry_price(self, market_price: float, signal_type: SignalType) -> float:
        """Calculate realistic entry price including spread and slippage."""
        spread = market_price * self.spread_cost
        slippage = market_price * self.slippage_factor * np.random.uniform(0.5, 1.5)
        
        if signal_type == SignalType.BUY:
            return market_price + spread/2 + slippage
        else:
            return market_price - spread/2 - slippage
    
    def _calculate_exit_price(self, market_price: float, position_action: TradeAction) -> float:
        """Calculate realistic exit price including spread and slippage."""
        spread = market_price * self.spread_cost
        slippage = market_price * self.slippage_factor * np.random.uniform(0.5, 1.5)
        
        if position_action == TradeAction.BUY:  # Selling to close long
            return market_price - spread/2 - slippage
        else:  # Buying to close short
            return market_price + spread/2 + slippage
    
    def _close_position(self, position: BacktestPosition, exit_price: float,
                       exit_time: datetime, reason: str) -> BacktestTrade:
        """Close a position and create trade record."""
        pnl = position.calculate_pnl(exit_price)
        position_value = position.volume * exit_price
        commission = position_value * self.commission_rate
        
        trade = BacktestTrade(
            timestamp=position.entry_time,
            pair=position.pair,
            action=position.action,
            volume=position.volume,
            entry_price=position.entry_price,
            exit_price=exit_price,
            exit_timestamp=exit_time,
            pnl=pnl,
            commission=commission,
            strategy_signal=reason,
            trade_id=position.trade_id
        )
        
        return trade
    
    def _create_empty_result(self, pair: str, start_date: datetime, end_date: datetime,
                           strategy: str, initial_capital: float) -> BacktestResult:
        """Create empty backtest result when insufficient data."""
        return BacktestResult(
            pair=pair,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            total_return=0.0,
            total_return_percent=0.0,
            max_drawdown=0.0,
            max_drawdown_percent=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=0.0,
            trades=[],
            daily_returns=[]
        )