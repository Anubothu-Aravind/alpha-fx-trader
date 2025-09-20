"""
Pydantic models for API requests and responses.
Defines data structures for FX trading operations.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class TradeStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class FXRate(BaseModel):
    """Current FX rate for a currency pair."""
    pair: str = Field(..., description="Currency pair (e.g., EUR/USD)")
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price")
    timestamp: datetime = Field(..., description="Rate timestamp")
    
    @validator('pair')
    def validate_pair(cls, v):
        if len(v) != 7 or v[3] != '/':
            raise ValueError('Pair must be in format XXX/YYY')
        return v.upper()
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price between bid and ask."""
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        """Calculate spread between ask and bid."""
        return self.ask - self.bid

class TradeRequest(BaseModel):
    """Request to execute a trade."""
    pair: str = Field(..., description="Currency pair")
    action: TradeAction = Field(..., description="Buy or sell")
    volume: float = Field(..., gt=0, description="Trade volume")
    order_type: OrderType = Field(OrderType.MARKET, description="Order type")
    limit_price: Optional[float] = Field(None, description="Limit price for limit orders")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    
    @validator('volume')
    def validate_volume(cls, v):
        if v <= 0:
            raise ValueError('Volume must be positive')
        return v

class TradeResponse(BaseModel):
    """Response after executing a trade."""
    trade_id: str = Field(..., description="Unique trade identifier")
    status: TradeStatus = Field(..., description="Trade execution status")
    execution_price: Optional[float] = Field(None, description="Actual execution price")
    timestamp: datetime = Field(..., description="Execution timestamp")
    message: str = Field(..., description="Status message")
    slippage: Optional[float] = Field(None, description="Price slippage")

class TradeRecord(BaseModel):
    """Historical trade record."""
    id: str
    pair: str
    action: TradeAction
    volume: float
    execution_price: float
    timestamp: datetime
    pnl: Optional[float] = None
    status: TradeStatus

class PositionStatus(BaseModel):
    """Current position status."""
    pair: str
    action: TradeAction
    volume: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    timestamp: datetime
    
    @property
    def pnl_percentage(self) -> float:
        """Calculate PnL as percentage."""
        if self.action == TradeAction.BUY:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.current_price) / self.entry_price) * 100

class TechnicalIndicator(BaseModel):
    """Technical indicator value."""
    indicator: str = Field(..., description="Indicator name (SMA, EMA, RSI, etc.)")
    value: float = Field(..., description="Indicator value")
    timestamp: datetime = Field(..., description="Calculation timestamp")
    period: Optional[int] = Field(None, description="Calculation period")

class TradeSignal(BaseModel):
    """Trading signal from analysis."""
    pair: str
    signal: SignalType
    strength: float = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    price: float = Field(..., description="Price when signal generated")
    timestamp: datetime
    indicators: List[TechnicalIndicator] = Field(default_factory=list)
    strategy: str = Field("technical", description="Strategy that generated signal")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")

class BacktestRequest(BaseModel):
    """Request for backtesting."""
    pair: str = Field(..., description="Currency pair to backtest")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    strategy: str = Field("technical", description="Trading strategy to test")
    initial_capital: float = Field(10000.0, gt=0, description="Initial capital")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class BacktestResult(BaseModel):
    """Backtesting results."""
    pair: str
    start_date: datetime
    end_date: datetime
    strategy: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    profit_factor: float
    trades: List[TradeRecord] = Field(default_factory=list)
    daily_returns: List[Dict[str, Any]] = Field(default_factory=list)

class TradingStats(BaseModel):
    """Overall trading statistics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_volume: float = 0.0
    average_trade_size: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    current_positions: int = 0
    active_pairs: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class MLPrediction(BaseModel):
    """Machine learning prediction."""
    pair: str
    prediction: SignalType
    probability: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    features: Dict[str, float] = Field(default_factory=dict)
    model_version: str = "1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MarketData(BaseModel):
    """Market data point."""
    pair: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish."""
        return self.close > self.open
    
    @property
    def body_size(self) -> float:
        """Calculate candle body size."""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """Calculate upper shadow size."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """Calculate lower shadow size."""
        return min(self.open, self.close) - self.low

class StrategyConfig(BaseModel):
    """Configuration for trading strategies."""
    strategy_name: str
    pair: str
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_management: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RiskMetrics(BaseModel):
    """Risk management metrics."""
    position_size: float
    risk_per_trade: float
    max_daily_loss: float
    current_exposure: float
    available_margin: float
    margin_used: float
    leverage: float
    value_at_risk: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)