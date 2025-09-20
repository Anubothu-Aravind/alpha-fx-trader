import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class TradingAlgorithms:
    """Trading algorithms for forex analysis"""
    
    def __init__(self):
        self.name = "TradingAlgorithms"
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return [None] * len(prices)
        
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma.append(avg)
        return sma
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        gains = [max(delta, 0) for delta in deltas]
        losses = [-min(delta, 0) for delta in deltas]
        
        rsi = [None]  # First value is always None
        
        # Calculate initial RSI
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
        
        # Calculate subsequent RSI values
        for i in range(period + 1, len(prices)):
            avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands (upper, middle, lower)"""
        if len(prices) < period:
            none_list = [None] * len(prices)
            return none_list, none_list, none_list
        
        middle_band = TradingAlgorithms.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1 or middle_band[i] is None:
                upper_band.append(None)
                lower_band.append(None)
            else:
                period_prices = prices[i-period+1:i+1]
                std = np.std(period_prices)
                upper_band.append(middle_band[i] + (std_dev * std))
                lower_band.append(middle_band[i] - (std_dev * std))
        
        return upper_band, middle_band, lower_band
    
    def sma_crossover_signal(self, prices: List[float], short_period: int = 10, long_period: int = 30) -> Optional[str]:
        """Generate SMA crossover trading signals"""
        if len(prices) < long_period:
            return None
        
        short_sma = self.calculate_sma(prices, short_period)
        long_sma = self.calculate_sma(prices, long_period)
        
        # Check last two values for crossover
        if len(short_sma) < 2 or short_sma[-1] is None or short_sma[-2] is None:
            return None
        if long_sma[-1] is None or long_sma[-2] is None:
            return None
        
        # Bullish crossover (short SMA crosses above long SMA)
        if short_sma[-2] <= long_sma[-2] and short_sma[-1] > long_sma[-1]:
            return 'BUY'
        
        # Bearish crossover (short SMA crosses below long SMA)
        if short_sma[-2] >= long_sma[-2] and short_sma[-1] < long_sma[-1]:
            return 'SELL'
        
        return None
    
    def rsi_signal(self, prices: List[float], period: int = 14, oversold: int = 30, overbought: int = 70) -> Optional[str]:
        """Generate RSI trading signals"""
        rsi_values = self.calculate_rsi(prices, period)
        
        if len(rsi_values) < 2 or rsi_values[-1] is None:
            return None
        
        current_rsi = rsi_values[-1]
        
        if current_rsi <= oversold:
            return 'BUY'  # Oversold, potential buy signal
        elif current_rsi >= overbought:
            return 'SELL'  # Overbought, potential sell signal
        
        return None
    
    def bollinger_bands_signal(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Optional[str]:
        """Generate Bollinger Bands trading signals"""
        upper, middle, lower = self.calculate_bollinger_bands(prices, period, std_dev)
        
        if len(prices) < 2 or upper[-1] is None or lower[-1] is None:
            return None
        
        current_price = prices[-1]
        
        # Price touches lower band - potential buy signal
        if current_price <= lower[-1]:
            return 'BUY'
        
        # Price touches upper band - potential sell signal
        if current_price >= upper[-1]:
            return 'SELL'
        
        return None
    
    def generate_combined_signal(self, prices: List[float]) -> Dict:
        """Generate combined signal from all algorithms"""
        signals = {
            'sma': self.sma_crossover_signal(prices),
            'rsi': self.rsi_signal(prices),
            'bollinger': self.bollinger_bands_signal(prices),
            'consensus': None
        }
        
        # Simple consensus logic
        buy_signals = sum(1 for signal in signals.values() if signal == 'BUY')
        sell_signals = sum(1 for signal in signals.values() if signal == 'SELL')
        
        if buy_signals >= 2:
            signals['consensus'] = 'BUY'
        elif sell_signals >= 2:
            signals['consensus'] = 'SELL'
        
        return signals