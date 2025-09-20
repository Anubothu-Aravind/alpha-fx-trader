"""
Live FX data feeder with mock data generation.
Provides real-time currency exchange rates via REST API or mock data.
"""

import asyncio
import aiohttp
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import logging

from models import FXRate

logger = logging.getLogger(__name__)

@dataclass
class FXDataConfig:
    """Configuration for FX data source."""
    use_mock_data: bool = True
    api_key: Optional[str] = None
    api_url: str = "https://api.exchangerate-api.com/v4/latest/USD"
    update_interval: int = 1  # seconds
    supported_pairs: List[str] = None
    
    def __post_init__(self):
        if self.supported_pairs is None:
            self.supported_pairs = [
                "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
                "USD/CHF", "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY"
            ]

class FXDataFeeder:
    """Live FX data feeder with multiple data sources."""
    
    def __init__(self, config: Optional[FXDataConfig] = None):
        self.config = config or FXDataConfig()
        self.current_rates: Dict[str, FXRate] = {}
        self.is_streaming = False
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Initialize with base rates for mock data
        self.base_rates = {
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2650,
            "USD/JPY": 150.25,
            "AUD/USD": 0.6420,
            "USD/CAD": 1.3750,
            "USD/CHF": 0.8890,
            "NZD/USD": 0.5980,
            "EUR/GBP": 0.8580,
            "EUR/JPY": 163.15,
            "GBP/JPY": 190.25
        }
        
        # Initialize current rates
        for pair in self.config.supported_pairs:
            if pair in self.base_rates:
                base_rate = self.base_rates[pair]
                spread = base_rate * 0.0002  # 2 pips spread
                self.current_rates[pair] = FXRate(
                    pair=pair,
                    bid=base_rate - spread/2,
                    ask=base_rate + spread/2,
                    timestamp=datetime.utcnow()
                )
    
    async def start_streaming(self):
        """Start streaming FX data."""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        logger.info("Starting FX data streaming...")
        
        if not self.config.use_mock_data:
            self._session = aiohttp.ClientSession()
        
        # Start background task for data updates
        asyncio.create_task(self._stream_data())
    
    async def stop_streaming(self):
        """Stop streaming FX data."""
        self.is_streaming = False
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("FX data streaming stopped")
    
    async def _stream_data(self):
        """Background task for streaming data updates."""
        while self.is_streaming:
            try:
                if self.config.use_mock_data:
                    await self._update_mock_data()
                else:
                    await self._fetch_live_data()
                
                await asyncio.sleep(self.config.update_interval)
            except Exception as e:
                logger.error(f"Error in data streaming: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _update_mock_data(self):
        """Update mock FX data with realistic price movements."""
        for pair in self.config.supported_pairs:
            if pair not in self.current_rates:
                continue
            
            current_rate = self.current_rates[pair]
            mid_price = current_rate.mid_price
            
            # Simulate realistic price movement (±0.1% typical)
            change_percent = random.gauss(0, 0.001)  # Normal distribution
            new_mid_price = mid_price * (1 + change_percent)
            
            # Add some market microstructure noise
            spread_factor = random.uniform(0.8, 1.5)  # Variable spreads
            base_spread = new_mid_price * 0.0002  # Base 2 pips
            spread = base_spread * spread_factor
            
            # Create new rate
            new_rate = FXRate(
                pair=pair,
                bid=round(new_mid_price - spread/2, 5),
                ask=round(new_mid_price + spread/2, 5),
                timestamp=datetime.utcnow()
            )
            
            self.current_rates[pair] = new_rate
    
    async def _fetch_live_data(self):
        """Fetch live data from external API."""
        if not self._session:
            return
        
        try:
            async with self._session.get(self.config.api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self._process_api_data(data)
                else:
                    logger.warning(f"API request failed with status {response.status}")
                    # Fall back to mock data
                    await self._update_mock_data()
        except Exception as e:
            logger.error(f"Error fetching live data: {e}")
            # Fall back to mock data
            await self._update_mock_data()
    
    async def _process_api_data(self, data: dict):
        """Process data from external API."""
        # This is a simplified example - real implementation would depend on API format
        base_currency = data.get("base", "USD")
        rates = data.get("rates", {})
        timestamp = datetime.utcnow()
        
        # Convert to our supported pairs format
        for pair in self.config.supported_pairs:
            try:
                base_curr, quote_curr = pair.split("/")
                
                # Calculate cross rates if needed
                if base_curr == base_currency:
                    rate = rates.get(quote_curr)
                elif quote_curr == base_currency:
                    rate = 1.0 / rates.get(base_curr) if rates.get(base_curr) else None
                else:
                    # Cross rate calculation
                    base_rate = rates.get(base_curr)
                    quote_rate = rates.get(quote_curr)
                    rate = base_rate / quote_rate if base_rate and quote_rate else None
                
                if rate:
                    spread = rate * 0.0002
                    self.current_rates[pair] = FXRate(
                        pair=pair,
                        bid=round(rate - spread/2, 5),
                        ask=round(rate + spread/2, 5),
                        timestamp=timestamp
                    )
            except (ValueError, KeyError, TypeError):
                # Skip invalid pairs or missing data
                continue
    
    async def get_rate(self, pair: str) -> Optional[FXRate]:
        """Get current rate for a specific currency pair."""
        return self.current_rates.get(pair.upper())
    
    async def get_current_rates(self) -> List[FXRate]:
        """Get all current rates."""
        return list(self.current_rates.values())
    
    async def get_historical_rates(self, pair: str, hours: int = 24) -> List[FXRate]:
        """Get historical rates (mock implementation)."""
        # In a real implementation, this would fetch from database or external API
        current_rate = await self.get_rate(pair)
        if not current_rate:
            return []
        
        historical_rates = []
        base_price = current_rate.mid_price
        
        # Generate mock historical data
        for i in range(hours):
            timestamp = datetime.utcnow() - timedelta(hours=hours-i)
            
            # Simulate price walk
            change = random.gauss(0, 0.001)
            price = base_price * (1 + change)
            spread = price * 0.0002
            
            rate = FXRate(
                pair=pair,
                bid=round(price - spread/2, 5),
                ask=round(price + spread/2, 5),
                timestamp=timestamp
            )
            historical_rates.append(rate)
        
        return historical_rates
    
    def is_active(self) -> bool:
        """Check if data feeder is active."""
        return self.is_streaming
    
    def get_supported_pairs(self) -> List[str]:
        """Get list of supported currency pairs."""
        return self.config.supported_pairs.copy()
    
    async def get_market_status(self) -> Dict[str, any]:
        """Get market status and statistics."""
        total_pairs = len(self.config.supported_pairs)
        active_pairs = len(self.current_rates)
        
        # Calculate average spread
        spreads = [rate.spread for rate in self.current_rates.values()]
        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        
        # Calculate last update times
        last_updates = [rate.timestamp for rate in self.current_rates.values()]
        latest_update = max(last_updates) if last_updates else None
        
        return {
            "is_streaming": self.is_streaming,
            "total_pairs": total_pairs,
            "active_pairs": active_pairs,
            "average_spread": round(avg_spread, 6),
            "latest_update": latest_update.isoformat() if latest_update else None,
            "data_source": "mock" if self.config.use_mock_data else "live",
            "update_interval": self.config.update_interval
        }
    
    async def simulate_market_event(self, event_type: str = "volatility"):
        """Simulate market events for testing (mock data only)."""
        if not self.config.use_mock_data:
            return
        
        if event_type == "volatility":
            # Increase volatility temporarily
            for pair in self.current_rates:
                current_rate = self.current_rates[pair]
                mid_price = current_rate.mid_price
                
                # Large price movement
                change = random.gauss(0, 0.01)  # 1% volatility
                new_mid_price = mid_price * (1 + change)
                
                # Wider spreads during volatility
                spread = new_mid_price * 0.0008  # 8 pips spread
                
                self.current_rates[pair] = FXRate(
                    pair=pair,
                    bid=round(new_mid_price - spread/2, 5),
                    ask=round(new_mid_price + spread/2, 5),
                    timestamp=datetime.utcnow()
                )
        
        elif event_type == "gap":
            # Simulate weekend gap
            for pair in self.current_rates:
                current_rate = self.current_rates[pair]
                mid_price = current_rate.mid_price
                
                # Gap up or down
                gap = random.choice([-0.005, 0.005])  # ±0.5% gap
                new_mid_price = mid_price * (1 + gap)
                
                spread = new_mid_price * 0.0003  # Normal spread
                
                self.current_rates[pair] = FXRate(
                    pair=pair,
                    bid=round(new_mid_price - spread/2, 5),
                    ask=round(new_mid_price + spread/2, 5),
                    timestamp=datetime.utcnow()
                )

# Global instance for easy import
data_feeder = FXDataFeeder()