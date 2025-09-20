"""
SQLite database models and utilities using SQLAlchemy ORM.
Defines database schema for trades, positions, and market data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alphafx_trader.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Trade(Base):
    """Trade execution records."""
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True, index=True)
    pair = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # 'buy' or 'sell'
    volume = Column(Float, nullable=False)
    order_type = Column(String, default="market")
    requested_price = Column(Float)
    execution_price = Column(Float, nullable=False)
    slippage = Column(Float)
    status = Column(String, default="executed")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    pnl = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    strategy = Column(String)
    notes = Column(Text)
    
    # Relationship to position
    position_id = Column(String, ForeignKey("positions.id"))
    position = relationship("Position", back_populates="trades")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            "id": self.id,
            "pair": self.pair,
            "action": self.action,
            "volume": self.volume,
            "order_type": self.order_type,
            "execution_price": self.execution_price,
            "slippage": self.slippage,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "pnl": self.pnl,
            "commission": self.commission,
            "strategy": self.strategy
        }

class Position(Base):
    """Open/closed position records."""
    __tablename__ = "positions"
    
    id = Column(String, primary_key=True, index=True)
    pair = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # 'buy' or 'sell'
    volume = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    status = Column(String, default="open", index=True)  # 'open', 'closed'
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    strategy = Column(String)
    
    # Relationship to trades
    trades = relationship("Trade", back_populates="position")
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL based on current price."""
        if self.action == "buy":
            return (current_price - self.entry_price) * self.volume
        else:
            return (self.entry_price - current_price) * self.volume
    
    def update_pnl(self, current_price: float):
        """Update unrealized PnL and current price."""
        self.current_price = current_price
        self.unrealized_pnl = self.calculate_pnl(current_price)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            "id": self.id,
            "pair": self.pair,
            "action": self.action,
            "volume": self.volume,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "status": self.status,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "strategy": self.strategy
        }

class MarketData(Base):
    """Historical market data (OHLCV)."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert market data to dictionary."""
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }

class Strategy(Base):
    """Trading strategy configurations."""
    __tablename__ = "strategies"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pair = Column(String, nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    parameters = Column(Text)  # JSON string
    risk_parameters = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    performance_stats = Column(Text)  # JSON string
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters as dictionary."""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def set_parameters(self, params: Dict[str, Any]):
        """Set strategy parameters from dictionary."""
        self.parameters = json.dumps(params)
    
    def get_risk_parameters(self) -> Dict[str, Any]:
        """Get risk parameters as dictionary."""
        if self.risk_parameters:
            return json.loads(self.risk_parameters)
        return {}
    
    def set_risk_parameters(self, params: Dict[str, Any]):
        """Set risk parameters from dictionary."""
        self.risk_parameters = json.dumps(params)

class Signal(Base):
    """Trading signals generated by strategies."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String, nullable=False, index=True)
    signal = Column(String, nullable=False)  # 'buy', 'sell', 'hold'
    strength = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    strategy = Column(String, nullable=False)
    confidence = Column(Float)
    indicators = Column(Text)  # JSON string of technical indicators
    executed = Column(Boolean, default=False)
    
    def get_indicators(self) -> Dict[str, Any]:
        """Get indicators as dictionary."""
        if self.indicators:
            return json.loads(self.indicators)
        return {}
    
    def set_indicators(self, indicators: Dict[str, Any]):
        """Set indicators from dictionary."""
        self.indicators = json.dumps(indicators)

class BacktestResult(Base):
    """Backtesting results storage."""
    __tablename__ = "backtest_results"
    
    id = Column(String, primary_key=True, index=True)
    pair = Column(String, nullable=False, index=True)
    strategy = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    parameters = Column(Text)  # JSON string
    results_data = Column(Text)  # JSON string with detailed results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get backtest parameters as dictionary."""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def get_results_data(self) -> Dict[str, Any]:
        """Get detailed results data as dictionary."""
        if self.results_data:
            return json.loads(self.results_data)
        return {}

# Database utility functions
def get_db_session() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_trade_history(db: Session, pair: Optional[str] = None, 
                     limit: int = 100, days: int = 30) -> List[Trade]:
    """Get trade history with optional filters."""
    query = db.query(Trade)
    
    if pair:
        query = query.filter(Trade.pair == pair.upper())
    
    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Trade.timestamp >= start_date)
    
    return query.order_by(Trade.timestamp.desc()).limit(limit).all()

def get_open_positions(db: Session, pair: Optional[str] = None) -> List[Position]:
    """Get open positions with optional pair filter."""
    query = db.query(Position).filter(Position.status == "open")
    
    if pair:
        query = query.filter(Position.pair == pair.upper())
    
    return query.all()

def get_position_by_id(db: Session, position_id: str) -> Optional[Position]:
    """Get position by ID."""
    return db.query(Position).filter(Position.id == position_id).first()

def get_trade_by_id(db: Session, trade_id: str) -> Optional[Trade]:
    """Get trade by ID."""
    return db.query(Trade).filter(Trade.id == trade_id).first()

def get_market_data(db: Session, pair: str, start_date: datetime, 
                   end_date: datetime) -> List[MarketData]:
    """Get historical market data for a pair and date range."""
    return db.query(MarketData).filter(
        MarketData.pair == pair.upper(),
        MarketData.timestamp >= start_date,
        MarketData.timestamp <= end_date
    ).order_by(MarketData.timestamp).all()

def get_recent_signals(db: Session, pair: Optional[str] = None, 
                      hours: int = 24) -> List[Signal]:
    """Get recent trading signals."""
    query = db.query(Signal)
    
    if pair:
        query = query.filter(Signal.pair == pair.upper())
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(Signal.timestamp >= start_time)
    
    return query.order_by(Signal.timestamp.desc()).all()

def calculate_portfolio_stats(db: Session) -> Dict[str, Any]:
    """Calculate overall portfolio statistics."""
    # Total trades
    total_trades = db.query(Trade).count()
    
    # Winning/losing trades
    winning_trades = db.query(Trade).filter(Trade.pnl > 0).count()
    losing_trades = db.query(Trade).filter(Trade.pnl < 0).count()
    
    # Win rate
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Total PnL
    total_pnl = db.query(func.sum(Trade.pnl)).scalar() or 0
    
    # Open positions
    open_positions = db.query(Position).filter(Position.status == "open").count()
    
    # Unrealized PnL
    unrealized_pnl = db.query(func.sum(Position.unrealized_pnl)).filter(
        Position.status == "open"
    ).scalar() or 0
    
    # Active pairs
    active_pairs = db.query(Position.pair).filter(Position.status == "open").distinct().all()
    active_pairs = [pair[0] for pair in active_pairs]
    
    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "total_realized_pnl": total_pnl,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl + unrealized_pnl,
        "open_positions": open_positions,
        "active_pairs": active_pairs,
        "last_updated": datetime.utcnow()
    }