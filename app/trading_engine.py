"""
Trading engine with SMA/EMA/RSI/Bollinger Bands strategies and risk management.
Handles trade execution, position management, and automated trading.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from models import (
    TradeAction, FXRate, TradeSignal, SignalType, 
    TradingStats, PositionStatus, TechnicalIndicator
)
from utils import TechnicalIndicators, SignalGenerator, PriceData, calculate_all_indicators
from db import SessionLocal, Trade, Position, MarketData, get_open_positions, calculate_portfolio_stats
from data_feeder import FXDataFeeder

logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    """Risk management parameters."""
    max_position_size: float = 1.0
    max_daily_loss: float = 500.0
    max_positions_per_pair: int = 3
    stop_loss_pct: float = 0.02  # 2%
    take_profit_pct: float = 0.04  # 4%
    max_leverage: float = 10.0
    risk_per_trade: float = 0.02  # 2% of capital per trade

@dataclass
class StrategyParameters:
    """Trading strategy parameters."""
    sma_fast: int = 10
    sma_slow: int = 30
    rsi_period: int = 14
    rsi_overbought: float = 70
    rsi_oversold: float = 30
    bb_period: int = 20
    bb_std_dev: float = 2.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    min_signal_strength: float = 0.6

class TradingEngine:
    """Core trading engine with multiple strategies and risk management."""
    
    def __init__(self, data_feeder: Optional[FXDataFeeder] = None):
        self.data_feeder = data_feeder
        self.active_strategies: Dict[str, Dict[str, Any]] = {}
        self.risk_params = RiskParameters()
        self.strategy_params = StrategyParameters()
        self.auto_trading_enabled = False
        self.daily_pnl = 0.0
        self.last_pnl_reset = datetime.utcnow().date()
        
        # Trading statistics
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'peak_capital': 10000.0  # Starting capital
        }
    
    async def execute_trade(self, pair: str, action: TradeAction, volume: float, 
                          rate: FXRate, db, strategy: str = "manual") -> Trade:
        """
        Execute a trade with risk management checks.
        
        Args:
            pair: Currency pair
            action: Buy or sell
            volume: Trade volume
            rate: Current FX rate
            db: Database session
            strategy: Strategy name
            
        Returns:
            Trade record
        """
        # Validate trade parameters
        await self._validate_trade(pair, action, volume, db)
        
        # Calculate execution price based on action
        execution_price = rate.ask if action == TradeAction.BUY else rate.bid
        slippage = abs(execution_price - rate.mid_price)
        
        # Create trade record
        trade_id = str(uuid.uuid4())
        trade = Trade(
            id=trade_id,
            pair=pair,
            action=action.value,
            volume=volume,
            execution_price=execution_price,
            slippage=slippage,
            timestamp=datetime.utcnow(),
            status="executed",
            strategy=strategy
        )
        
        # Check if this opens a new position or modifies existing one
        await self._handle_position(trade, db)
        
        # Save trade
        db.add(trade)
        db.commit()
        
        # Update statistics
        await self._update_stats(trade)
        
        logger.info(f"Trade executed: {action.value} {volume} {pair} @ {execution_price}")
        return trade
    
    async def _validate_trade(self, pair: str, action: TradeAction, volume: float, db):
        """Validate trade against risk parameters."""
        # Check daily loss limit
        if self.daily_pnl <= -self.risk_params.max_daily_loss:
            raise Exception(f"Daily loss limit exceeded: {self.daily_pnl}")
        
        # Check position limits
        open_positions = get_open_positions(db, pair)
        if len(open_positions) >= self.risk_params.max_positions_per_pair:
            raise Exception(f"Maximum positions per pair exceeded: {len(open_positions)}")
        
        # Check volume limits
        if volume > self.risk_params.max_position_size:
            raise Exception(f"Position size exceeds limit: {volume} > {self.risk_params.max_position_size}")
        
        # Check if volume is positive
        if volume <= 0:
            raise Exception("Volume must be positive")
    
    async def _handle_position(self, trade: Trade, db):
        """Handle position creation or modification."""
        # Look for existing opposite position
        opposite_action = "sell" if trade.action == "buy" else "buy"
        existing_position = db.query(Position).filter(
            Position.pair == trade.pair,
            Position.action == opposite_action,
            Position.status == "open"
        ).first()
        
        if existing_position:
            # Close or reduce existing position
            if existing_position.volume <= trade.volume:
                # Close existing position
                existing_position.status = "closed"
                existing_position.closed_at = datetime.utcnow()
                existing_position.realized_pnl = existing_position.calculate_pnl(trade.execution_price)
                
                # Create new position if trade volume is larger
                remaining_volume = trade.volume - existing_position.volume
                if remaining_volume > 0:
                    await self._create_new_position(trade, remaining_volume, db)
            else:
                # Reduce existing position
                existing_position.volume -= trade.volume
                existing_position.realized_pnl += existing_position.calculate_pnl(trade.execution_price)
        else:
            # Create new position
            await self._create_new_position(trade, trade.volume, db)
    
    async def _create_new_position(self, trade: Trade, volume: float, db):
        """Create a new position."""
        position_id = str(uuid.uuid4())
        
        # Calculate stop loss and take profit
        stop_loss, take_profit = self._calculate_stop_take_profit(
            trade.execution_price, trade.action
        )
        
        position = Position(
            id=position_id,
            pair=trade.pair,
            action=trade.action,
            volume=volume,
            entry_price=trade.execution_price,
            current_price=trade.execution_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=trade.strategy
        )
        
        trade.position_id = position_id
        db.add(position)
    
    def _calculate_stop_take_profit(self, entry_price: float, action: str) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels."""
        if action == "buy":
            stop_loss = entry_price * (1 - self.risk_params.stop_loss_pct)
            take_profit = entry_price * (1 + self.risk_params.take_profit_pct)
        else:
            stop_loss = entry_price * (1 + self.risk_params.stop_loss_pct)
            take_profit = entry_price * (1 - self.risk_params.take_profit_pct)
        
        return stop_loss, take_profit
    
    async def get_technical_signals(self, pair: str) -> List[TradeSignal]:
        """
        Generate trading signals using technical analysis.
        
        Args:
            pair: Currency pair
            
        Returns:
            List of trading signals
        """
        if not self.data_feeder:
            return []
        
        # Get historical data (mock implementation - use recent rates)
        historical_rates = await self.data_feeder.get_historical_rates(pair, hours=100)
        if len(historical_rates) < 50:
            return []
        
        # Convert to price data
        price_data = []
        for i, rate in enumerate(historical_rates):
            # Simulate OHLC from bid/ask
            high = rate.ask
            low = rate.bid
            open_price = historical_rates[i-1].mid_price if i > 0 else rate.mid_price
            close = rate.mid_price
            
            price_data.append(PriceData(
                timestamp=rate.timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close
            ))
        
        # Calculate indicators
        indicators = calculate_all_indicators(price_data)
        
        # Generate signals from different strategies
        signals = []
        current_price = historical_rates[-1].mid_price
        timestamp = datetime.utcnow()
        
        # SMA Crossover Signal
        sma_signals = SignalGenerator.sma_crossover(
            [p.close for p in price_data],
            self.strategy_params.sma_fast,
            self.strategy_params.sma_slow
        )
        if sma_signals[-1] != 'hold':
            signal_strength = self._calculate_signal_strength(indicators, 'sma')
            if signal_strength >= self.strategy_params.min_signal_strength:
                signals.append(TradeSignal(
                    pair=pair,
                    signal=SignalType.BUY if sma_signals[-1] == 'buy' else SignalType.SELL,
                    strength=signal_strength,
                    price=current_price,
                    timestamp=timestamp,
                    strategy="sma_crossover",
                    indicators=[
                        TechnicalIndicator(
                            indicator="SMA_FAST",
                            value=indicators['sma_fast'][-1],
                            timestamp=timestamp,
                            period=self.strategy_params.sma_fast
                        ),
                        TechnicalIndicator(
                            indicator="SMA_SLOW",
                            value=indicators['sma_slow'][-1],
                            timestamp=timestamp,
                            period=self.strategy_params.sma_slow
                        )
                    ]
                ))
        
        # RSI Signal
        rsi_signals = SignalGenerator.rsi_signals(
            [p.close for p in price_data],
            self.strategy_params.rsi_period,
            self.strategy_params.rsi_overbought,
            self.strategy_params.rsi_oversold
        )
        if rsi_signals[-1] != 'hold' and not any(np.isnan(indicators['rsi'])):
            signal_strength = self._calculate_signal_strength(indicators, 'rsi')
            if signal_strength >= self.strategy_params.min_signal_strength:
                signals.append(TradeSignal(
                    pair=pair,
                    signal=SignalType.BUY if rsi_signals[-1] == 'buy' else SignalType.SELL,
                    strength=signal_strength,
                    price=current_price,
                    timestamp=timestamp,
                    strategy="rsi",
                    indicators=[
                        TechnicalIndicator(
                            indicator="RSI",
                            value=indicators['rsi'][-1],
                            timestamp=timestamp,
                            period=self.strategy_params.rsi_period
                        )
                    ]
                ))
        
        # Bollinger Bands Signal
        bb_signals = SignalGenerator.bollinger_signals(
            [p.close for p in price_data],
            self.strategy_params.bb_period,
            self.strategy_params.bb_std_dev
        )
        if bb_signals[-1] != 'hold':
            signal_strength = self._calculate_signal_strength(indicators, 'bollinger')
            if signal_strength >= self.strategy_params.min_signal_strength:
                signals.append(TradeSignal(
                    pair=pair,
                    signal=SignalType.BUY if bb_signals[-1] == 'buy' else SignalType.SELL,
                    strength=signal_strength,
                    price=current_price,
                    timestamp=timestamp,
                    strategy="bollinger_bands",
                    indicators=[
                        TechnicalIndicator(
                            indicator="BB_UPPER",
                            value=indicators['bb_upper'][-1],
                            timestamp=timestamp
                        ),
                        TechnicalIndicator(
                            indicator="BB_MIDDLE",
                            value=indicators['bb_middle'][-1],
                            timestamp=timestamp
                        ),
                        TechnicalIndicator(
                            indicator="BB_LOWER",
                            value=indicators['bb_lower'][-1],
                            timestamp=timestamp
                        )
                    ]
                ))
        
        return signals
    
    def _calculate_signal_strength(self, indicators: Dict[str, List[float]], 
                                 strategy: str) -> float:
        """Calculate signal strength based on indicator values."""
        try:
            if strategy == 'sma':
                # Signal strength based on distance between SMAs
                fast_sma = indicators['sma_fast'][-1]
                slow_sma = indicators['sma_slow'][-1]
                if not (np.isnan(fast_sma) or np.isnan(slow_sma)):
                    distance = abs(fast_sma - slow_sma) / slow_sma
                    return min(distance * 100, 1.0)  # Normalize to 0-1
            
            elif strategy == 'rsi':
                # Signal strength based on RSI extreme levels
                rsi = indicators['rsi'][-1]
                if not np.isnan(rsi):
                    if rsi > 70:
                        return (rsi - 70) / 30  # 0-1 scale for overbought
                    elif rsi < 30:
                        return (30 - rsi) / 30  # 0-1 scale for oversold
            
            elif strategy == 'bollinger':
                # Signal strength based on price position relative to bands
                if all(not np.isnan(indicators[key][-1]) for key in ['bb_upper', 'bb_lower', 'bb_middle']):
                    current_close = indicators['bb_middle'][-1]  # Approximate
                    upper = indicators['bb_upper'][-1]
                    lower = indicators['bb_lower'][-1]
                    middle = indicators['bb_middle'][-1]
                    
                    if current_close > upper:
                        return min((current_close - upper) / (upper - middle), 1.0)
                    elif current_close < lower:
                        return min((lower - current_close) / (middle - lower), 1.0)
            
            return 0.6  # Default moderate strength
        except (IndexError, KeyError, TypeError):
            return 0.5
    
    async def update_positions(self, db):
        """Update all open positions with current market prices."""
        if not self.data_feeder:
            return
        
        open_positions = get_open_positions(db)
        
        for position in open_positions:
            try:
                current_rate = await self.data_feeder.get_rate(position.pair)
                if current_rate:
                    # Update position with current market price
                    market_price = current_rate.bid if position.action == "buy" else current_rate.ask
                    position.update_pnl(market_price)
                    
                    # Check for stop loss or take profit
                    if await self._check_exit_conditions(position, current_rate):
                        await self._close_position(position, current_rate, db)
                
            except Exception as e:
                logger.error(f"Error updating position {position.id}: {e}")
        
        db.commit()
    
    async def _check_exit_conditions(self, position: Position, rate: FXRate) -> bool:
        """Check if position should be closed due to stop loss or take profit."""
        market_price = rate.bid if position.action == "buy" else rate.ask
        
        if position.action == "buy":
            # Long position
            if position.stop_loss and market_price <= position.stop_loss:
                logger.info(f"Stop loss triggered for position {position.id}")
                return True
            if position.take_profit and market_price >= position.take_profit:
                logger.info(f"Take profit triggered for position {position.id}")
                return True
        else:
            # Short position
            if position.stop_loss and market_price >= position.stop_loss:
                logger.info(f"Stop loss triggered for position {position.id}")
                return True
            if position.take_profit and market_price <= position.take_profit:
                logger.info(f"Take profit triggered for position {position.id}")
                return True
        
        return False
    
    async def _close_position(self, position: Position, rate: FXRate, db):
        """Close a position at current market price."""
        market_price = rate.bid if position.action == "buy" else rate.ask
        
        # Update position
        position.status = "closed"
        position.closed_at = datetime.utcnow()
        position.current_price = market_price
        position.realized_pnl = position.calculate_pnl(market_price)
        
        # Create closing trade
        closing_trade = Trade(
            id=str(uuid.uuid4()),
            pair=position.pair,
            action="sell" if position.action == "buy" else "buy",
            volume=position.volume,
            execution_price=market_price,
            timestamp=datetime.utcnow(),
            status="executed",
            strategy="auto_close",
            position_id=position.id,
            pnl=position.realized_pnl
        )
        
        db.add(closing_trade)
        await self._update_stats(closing_trade)
    
    async def start_auto_trading(self, pair: str, strategy: str = "technical") -> bool:
        """Start automated trading for a currency pair."""
        if pair in self.active_strategies:
            return False
        
        self.active_strategies[pair] = {
            'strategy': strategy,
            'enabled': True,
            'last_signal_time': datetime.utcnow(),
            'trades_today': 0,
            'max_trades_per_day': 10
        }
        
        # Start background task for this pair
        asyncio.create_task(self._auto_trading_loop(pair))
        
        logger.info(f"Auto trading started for {pair} with {strategy} strategy")
        return True
    
    async def stop_auto_trading(self, pair: str) -> bool:
        """Stop automated trading for a currency pair."""
        if pair not in self.active_strategies:
            return False
        
        self.active_strategies[pair]['enabled'] = False
        del self.active_strategies[pair]
        
        logger.info(f"Auto trading stopped for {pair}")
        return True
    
    async def _auto_trading_loop(self, pair: str):
        """Background loop for automated trading."""
        while pair in self.active_strategies and self.active_strategies[pair]['enabled']:
            try:
                # Check daily limits
                strategy_info = self.active_strategies[pair]
                if strategy_info['trades_today'] >= strategy_info['max_trades_per_day']:
                    await asyncio.sleep(3600)  # Wait 1 hour
                    continue
                
                # Get trading signals
                signals = await self.get_technical_signals(pair)
                
                if signals:
                    # Execute strongest signal
                    best_signal = max(signals, key=lambda s: s.strength)
                    
                    if best_signal.strength >= self.strategy_params.min_signal_strength:
                        await self._execute_auto_trade(pair, best_signal)
                        strategy_info['trades_today'] += 1
                        strategy_info['last_signal_time'] = datetime.utcnow()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in auto trading loop for {pair}: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _execute_auto_trade(self, pair: str, signal: TradeSignal):
        """Execute an automated trade based on signal."""
        if not self.data_feeder:
            return
        
        try:
            # Get current rate
            current_rate = await self.data_feeder.get_rate(pair)
            if not current_rate:
                return
            
            # Calculate position size based on risk management
            position_size = self._calculate_position_size(signal.strength)
            
            # Execute trade
            db = SessionLocal()
            try:
                action = TradeAction.BUY if signal.signal == SignalType.BUY else TradeAction.SELL
                trade = await self.execute_trade(
                    pair=pair,
                    action=action,
                    volume=position_size,
                    rate=current_rate,
                    db=db,
                    strategy=f"auto_{signal.strategy}"
                )
                
                logger.info(f"Auto trade executed: {trade.id}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error executing auto trade for {pair}: {e}")
    
    def _calculate_position_size(self, signal_strength: float) -> float:
        """Calculate position size based on signal strength and risk parameters."""
        base_size = self.risk_params.max_position_size * 0.5  # Conservative base
        risk_adjusted_size = base_size * signal_strength
        
        return min(risk_adjusted_size, self.risk_params.max_position_size)
    
    async def get_trading_stats(self, db) -> TradingStats:
        """Get comprehensive trading statistics."""
        # Reset daily P&L if new day
        if datetime.utcnow().date() > self.last_pnl_reset:
            self.daily_pnl = 0.0
            self.last_pnl_reset = datetime.utcnow().date()
            # Reset daily trade counts
            for pair_info in self.active_strategies.values():
                pair_info['trades_today'] = 0
        
        # Get database statistics
        db_stats = calculate_portfolio_stats(db)
        
        # Combine with engine statistics
        stats = TradingStats(
            total_trades=db_stats['total_trades'],
            winning_trades=db_stats['winning_trades'],
            losing_trades=db_stats['losing_trades'],
            win_rate=db_stats['win_rate'],
            total_pnl=db_stats['total_pnl'],
            active_pairs=db_stats['active_pairs'],
            current_positions=db_stats['open_positions'],
            last_updated=datetime.utcnow()
        )
        
        return stats
    
    async def _update_stats(self, trade: Trade):
        """Update internal trading statistics."""
        self.stats['total_trades'] += 1
        
        if trade.pnl:
            self.stats['total_pnl'] += trade.pnl
            self.daily_pnl += trade.pnl
            
            if trade.pnl > 0:
                self.stats['winning_trades'] += 1
            else:
                self.stats['losing_trades'] += 1
                
            # Update drawdown
            if self.stats['total_pnl'] > self.stats['peak_capital']:
                self.stats['peak_capital'] = self.stats['total_pnl']
                self.stats['current_drawdown'] = 0.0
            else:
                self.stats['current_drawdown'] = self.stats['peak_capital'] - self.stats['total_pnl']
                if self.stats['current_drawdown'] > self.stats['max_drawdown']:
                    self.stats['max_drawdown'] = self.stats['current_drawdown']
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status."""
        return {
            'auto_trading_enabled': len(self.active_strategies) > 0,
            'active_strategies': list(self.active_strategies.keys()),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.stats['total_pnl'],
            'total_trades': self.stats['total_trades'],
            'current_drawdown': self.stats['current_drawdown'],
            'risk_parameters': {
                'max_position_size': self.risk_params.max_position_size,
                'max_daily_loss': self.risk_params.max_daily_loss,
                'stop_loss_pct': self.risk_params.stop_loss_pct,
                'take_profit_pct': self.risk_params.take_profit_pct
            }
        }

# Import numpy for NaN checks
import numpy as np