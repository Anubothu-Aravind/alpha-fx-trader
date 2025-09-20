"""
Database initialization script.
Creates tables and populates with sample data for demo purposes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import uuid
from db import create_tables, SessionLocal, Trade, Position, MarketData, Strategy, Signal
import random

def init_database():
    """Initialize database with tables and sample data."""
    print("Initializing AlphaFX Trader database...")
    
    # Create all tables
    create_tables()
    print("✓ Database tables created")
    
    # Add sample data
    db = SessionLocal()
    try:
        add_sample_market_data(db)
        add_sample_trades(db)
        add_sample_strategies(db)
        add_sample_signals(db)
        db.commit()
        print("✓ Sample data added")
    except Exception as e:
        print(f"✗ Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Database initialization complete!")

def add_sample_market_data(db):
    """Add sample market data for major currency pairs."""
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"]
    base_prices = {
        "EUR/USD": 1.0850,
        "GBP/USD": 1.2650,
        "USD/JPY": 150.25,
        "AUD/USD": 0.6420,
        "USD/CAD": 1.3750
    }
    
    # Generate 30 days of hourly data
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for pair in pairs:
        base_price = base_prices[pair]
        current_price = base_price
        
        for i in range(30 * 24):  # 30 days * 24 hours
            timestamp = start_date + timedelta(hours=i)
            
            # Simulate price movement
            change = random.uniform(-0.002, 0.002)  # ±0.2% change
            current_price = current_price * (1 + change)
            
            # Create OHLC data
            open_price = current_price
            high = open_price * (1 + random.uniform(0, 0.001))
            low = open_price * (1 - random.uniform(0, 0.001))
            close = low + random.uniform(0, 1) * (high - low)
            volume = random.uniform(1000, 10000)
            
            market_data = MarketData(
                pair=pair,
                timestamp=timestamp,
                open=round(open_price, 5),
                high=round(high, 5),
                low=round(low, 5),
                close=round(close, 5),
                volume=round(volume, 2)
            )
            db.add(market_data)
            current_price = close
    
    print(f"✓ Added market data for {len(pairs)} currency pairs")

def add_sample_trades(db):
    """Add sample trade history."""
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
    actions = ["buy", "sell"]
    strategies = ["technical", "ml", "manual"]
    
    # Generate 50 sample trades
    for i in range(50):
        trade_id = str(uuid.uuid4())
        pair = random.choice(pairs)
        action = random.choice(actions)
        volume = random.uniform(0.1, 2.0)
        execution_price = random.uniform(1.0, 1.5) if "USD" in pair else random.uniform(120, 160)
        pnl = random.uniform(-100, 150)
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        
        trade = Trade(
            id=trade_id,
            pair=pair,
            action=action,
            volume=round(volume, 2),
            execution_price=round(execution_price, 5),
            status="executed",
            timestamp=timestamp,
            pnl=round(pnl, 2),
            strategy=random.choice(strategies)
        )
        db.add(trade)
    
    print("✓ Added 50 sample trades")

def add_sample_strategies(db):
    """Add sample strategy configurations."""
    strategies = [
        {
            "id": "technical_eur_usd",
            "name": "Technical Analysis EUR/USD",
            "pair": "EUR/USD",
            "enabled": True,
            "parameters": '{"sma_fast": 10, "sma_slow": 30, "rsi_period": 14, "rsi_overbought": 70, "rsi_oversold": 30}',
            "risk_parameters": '{"max_position_size": 1.0, "stop_loss_pct": 0.02, "take_profit_pct": 0.04}'
        },
        {
            "id": "ml_gbp_usd",
            "name": "ML Strategy GBP/USD",
            "pair": "GBP/USD",
            "enabled": False,
            "parameters": '{"model_type": "lstm", "lookback_window": 60, "prediction_horizon": 1}',
            "risk_parameters": '{"max_position_size": 0.5, "confidence_threshold": 0.7}'
        },
        {
            "id": "scalping_usd_jpy",
            "name": "Scalping USD/JPY",
            "pair": "USD/JPY",
            "enabled": True,
            "parameters": '{"ema_period": 5, "bollinger_period": 20, "bollinger_std": 2}',
            "risk_parameters": '{"max_position_size": 2.0, "stop_loss_pips": 10, "take_profit_pips": 15}'
        }
    ]
    
    for strategy_data in strategies:
        strategy = Strategy(**strategy_data)
        db.add(strategy)
    
    print("✓ Added sample strategy configurations")

def add_sample_signals(db):
    """Add sample trading signals."""
    pairs = ["EUR/USD", "GBP/USD", "USD/JPY"]
    signals = ["buy", "sell", "hold"]
    strategies = ["technical", "ml"]
    
    # Generate signals for the last 7 days
    for i in range(20):
        signal = Signal(
            pair=random.choice(pairs),
            signal=random.choice(signals),
            strength=random.uniform(0.3, 0.9),
            price=random.uniform(1.0, 1.5),
            timestamp=datetime.utcnow() - timedelta(hours=random.randint(0, 168)),
            strategy=random.choice(strategies),
            confidence=random.uniform(0.5, 0.95),
            indicators='{"sma_10": 1.0850, "sma_30": 1.0820, "rsi": 65.5, "macd": 0.0025}',
            executed=random.choice([True, False])
        )
        db.add(signal)
    
    print("✓ Added sample trading signals")

def reset_database():
    """Reset database by dropping and recreating all tables."""
    from db import Base, engine
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Database reset complete")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AlphaFX Trader Database Management")
    parser.add_argument("--reset", action="store_true", help="Reset database")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    
    if args.init or not (args.reset):
        init_database()