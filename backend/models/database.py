from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    pair = Column(String(10), nullable=False)
    side = Column(String(4), nullable=False)  # BUY or SELL
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    algorithm = Column(String(50))  # SMA, RSI, BOLLINGER
    status = Column(String(20), default='EXECUTED')  # EXECUTED, PENDING, CANCELLED
    pnl = Column(Float, default=0.0)
    notes = Column(Text)

class PriceData(Base):
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True)
    pair = Column(String(10), nullable=False)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
class TradingSession(Base):
    __tablename__ = 'trading_sessions'
    
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_volume = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    auto_trading_enabled = Column(Boolean, default=True)

def create_database():
    """Create database and tables"""
    os.makedirs('/home/runner/work/alpha-fx-trader/alpha-fx-trader/data', exist_ok=True)
    engine = create_engine('sqlite:///data/trades.db', echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session"""
    engine = create_database()
    Session = sessionmaker(bind=engine)
    return Session()