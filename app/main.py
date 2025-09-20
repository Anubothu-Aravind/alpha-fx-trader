"""
FastAPI entrypoint for AlphaFxTrader backend.
Provides REST API for FX trading operations, live data streaming, and backtesting.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio
import json
from typing import List, Optional
from datetime import datetime

from models import (
    TradeRequest, TradeResponse, BacktestRequest, BacktestResult,
    FXRate, TradeSignal, PositionStatus, TradingStats
)
from data_feeder import FXDataFeeder
from trading_engine import TradingEngine
from ml_strategy import MLStrategy
from backtester import Backtester
from db import get_db_session, Trade, Position
from db_init import init_database

app = FastAPI(
    title="AlphaFX Trader API",
    description="Real-time FX trading platform with ML-powered strategies",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
data_feeder = FXDataFeeder()
trading_engine = TradingEngine()
ml_strategy = MLStrategy()
backtester = Backtester()

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks."""
    init_database()
    # Start data feeder in background
    asyncio.create_task(data_feeder.start_streaming())

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "AlphaFX Trader API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "data_feeder_active": data_feeder.is_active(),
        "trading_engine_status": trading_engine.get_status()
    }

@app.get("/rates/stream")
async def stream_rates():
    """Stream live FX rates via Server-Sent Events."""
    async def event_stream():
        while True:
            try:
                rates = await data_feeder.get_current_rates()
                for rate in rates:
                    data = {
                        "timestamp": rate.timestamp.isoformat(),
                        "pair": rate.pair,
                        "bid": rate.bid,
                        "ask": rate.ask,
                        "spread": rate.ask - rate.bid
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )

@app.get("/rates/{pair}")
async def get_rate(pair: str):
    """Get current rate for a specific currency pair."""
    try:
        rate = await data_feeder.get_rate(pair.upper())
        if not rate:
            raise HTTPException(status_code=404, detail=f"Rate for {pair} not found")
        return rate
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rates")
async def get_all_rates():
    """Get current rates for all available currency pairs."""
    try:
        rates = await data_feeder.get_current_rates()
        return rates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trade", response_model=TradeResponse)
async def execute_trade(trade_request: TradeRequest, db=Depends(get_db_session)):
    """Execute a trade order."""
    try:
        # Validate trade request
        current_rate = await data_feeder.get_rate(trade_request.pair)
        if not current_rate:
            raise HTTPException(status_code=400, detail=f"Rate for {trade_request.pair} not available")
        
        # Execute trade through trading engine
        trade_result = await trading_engine.execute_trade(
            pair=trade_request.pair,
            action=trade_request.action,
            volume=trade_request.volume,
            rate=current_rate,
            db=db
        )
        
        return TradeResponse(
            trade_id=trade_result.id,
            status="executed",
            execution_price=trade_result.execution_price,
            timestamp=trade_result.timestamp,
            message="Trade executed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades")
async def get_trades(limit: int = 50, db=Depends(get_db_session)):
    """Get recent trades history."""
    try:
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
        return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/positions")
async def get_positions(db=Depends(get_db_session)):
    """Get current open positions."""
    try:
        positions = db.query(Position).filter(Position.status == "open").all()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signals/{pair}")
async def get_trading_signals(pair: str, strategy: str = "technical"):
    """Get trading signals for a currency pair."""
    try:
        if strategy == "ml":
            signals = await ml_strategy.get_signals(pair.upper())
        else:
            signals = await trading_engine.get_technical_signals(pair.upper())
        
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backtest", response_model=BacktestResult)
async def run_backtest(backtest_request: BacktestRequest):
    """Run backtesting on historical data."""
    try:
        result = await backtester.run_backtest(
            pair=backtest_request.pair,
            start_date=backtest_request.start_date,
            end_date=backtest_request.end_date,
            strategy=backtest_request.strategy,
            initial_capital=backtest_request.initial_capital
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_trading_stats(db=Depends(get_db_session)):
    """Get overall trading statistics."""
    try:
        stats = await trading_engine.get_trading_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/start/{pair}")
async def start_auto_trading(pair: str, strategy: str = "technical"):
    """Start automated trading for a currency pair."""
    try:
        success = await trading_engine.start_auto_trading(pair.upper(), strategy)
        if success:
            return {"status": "started", "pair": pair, "strategy": strategy}
        else:
            raise HTTPException(status_code=400, detail="Failed to start auto trading")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/stop/{pair}")
async def stop_auto_trading(pair: str):
    """Stop automated trading for a currency pair."""
    try:
        success = await trading_engine.stop_auto_trading(pair.upper())
        if success:
            return {"status": "stopped", "pair": pair}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop auto trading")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)