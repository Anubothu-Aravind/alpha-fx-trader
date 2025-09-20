"""
Technical indicator utility functions for trading analysis.
Implements SMA, EMA, RSI, Bollinger Bands, MACD, and other indicators.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PriceData:
    """Price data point for calculations."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

class TechnicalIndicators:
    """Collection of technical indicator calculations."""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """
        Simple Moving Average.
        
        Args:
            prices: List of prices
            period: Moving average period
            
        Returns:
            List of SMA values (NaN for insufficient data)
        """
        if len(prices) < period:
            return [np.nan] * len(prices)
        
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(np.nan)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma_values.append(avg)
        
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """
        Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: EMA period
            
        Returns:
            List of EMA values
        """
        if not prices:
            return []
        
        ema_values = [prices[0]]  # First EMA = first price
        multiplier = 2.0 / (period + 1)
        
        for i in range(1, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Relative Strength Index.
        
        Args:
            prices: List of closing prices
            period: RSI period (default 14)
            
        Returns:
            List of RSI values (0-100)
        """
        if len(prices) <= period:
            return [np.nan] * len(prices)
        
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        # Calculate initial averages
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = [np.nan] * (period + 1)  # +1 for first price
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # Calculate RSI for remaining periods
        for i in range(period + 1, len(prices)):
            gain = gains[i-1] if gains[i-1] > 0 else 0
            loss = losses[i-1] if losses[i-1] > 0 else 0
            
            avg_gain = ((avg_gain * (period - 1)) + gain) / period
            avg_loss = ((avg_loss * (period - 1)) + loss) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, 
                       std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """
        Bollinger Bands.
        
        Args:
            prices: List of closing prices
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (middle_band, upper_band, lower_band)
        """
        if len(prices) < period:
            nan_list = [np.nan] * len(prices)
            return nan_list, nan_list, nan_list
        
        middle_band = TechnicalIndicators.sma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1 or np.isnan(middle_band[i]):
                upper_band.append(np.nan)
                lower_band.append(np.nan)
            else:
                # Calculate standard deviation for the period
                period_prices = prices[i-period+1:i+1]
                std = np.std(period_prices)
                
                upper_band.append(middle_band[i] + (std_dev * std))
                lower_band.append(middle_band[i] - (std_dev * std))
        
        return middle_band, upper_band, lower_band
    
    @staticmethod
    def macd(prices: List[float], fast_period: int = 12, 
             slow_period: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """
        MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of closing prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        if len(prices) < slow_period:
            nan_list = [np.nan] * len(prices)
            return nan_list, nan_list, nan_list
        
        fast_ema = TechnicalIndicators.ema(prices, fast_period)
        slow_ema = TechnicalIndicators.ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(prices)):
            if i < slow_period - 1:
                macd_line.append(np.nan)
            else:
                macd_line.append(fast_ema[i] - slow_ema[i])
        
        # Calculate signal line (EMA of MACD line)
        valid_macd = [x for x in macd_line if not np.isnan(x)]
        if len(valid_macd) >= signal_period:
            signal_ema = TechnicalIndicators.ema(valid_macd, signal_period)
            # Pad with NaN for alignment
            signal_line = [np.nan] * (len(prices) - len(signal_ema)) + signal_ema
        else:
            signal_line = [np.nan] * len(prices)
        
        # Calculate histogram
        histogram = []
        for i in range(len(prices)):
            if np.isnan(macd_line[i]) or np.isnan(signal_line[i]):
                histogram.append(np.nan)
            else:
                histogram.append(macd_line[i] - signal_line[i])
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def stochastic(high: List[float], low: List[float], close: List[float], 
                   k_period: int = 14, d_period: int = 3) -> Tuple[List[float], List[float]]:
        """
        Stochastic Oscillator.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of closing prices
            k_period: %K period
            d_period: %D period (SMA of %K)
            
        Returns:
            Tuple of (%K, %D)
        """
        if len(high) != len(low) != len(close) or len(close) < k_period:
            nan_list = [np.nan] * len(close)
            return nan_list, nan_list
        
        k_percent = []
        
        for i in range(len(close)):
            if i < k_period - 1:
                k_percent.append(np.nan)
            else:
                period_high = max(high[i-k_period+1:i+1])
                period_low = min(low[i-k_period+1:i+1])
                
                if period_high == period_low:
                    k_percent.append(50.0)
                else:
                    k_value = ((close[i] - period_low) / (period_high - period_low)) * 100
                    k_percent.append(k_value)
        
        # Calculate %D (SMA of %K)
        valid_k = [x for x in k_percent if not np.isnan(x)]
        if len(valid_k) >= d_period:
            d_percent_values = TechnicalIndicators.sma(valid_k, d_period)
            # Pad with NaN for alignment
            d_percent = [np.nan] * (len(close) - len(d_percent_values)) + d_percent_values
        else:
            d_percent = [np.nan] * len(close)
        
        return k_percent, d_percent
    
    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], 
            period: int = 14) -> List[float]:
        """
        Average True Range.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of closing prices
            period: ATR period
            
        Returns:
            List of ATR values
        """
        if len(high) != len(low) != len(close) or len(close) < 2:
            return [np.nan] * len(close)
        
        true_ranges = []
        
        # First TR is just high - low
        true_ranges.append(high[0] - low[0])
        
        # Calculate True Range for remaining periods
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        # Calculate ATR using EMA
        return TechnicalIndicators.ema(true_ranges, period)
    
    @staticmethod
    def williams_r(high: List[float], low: List[float], close: List[float], 
                   period: int = 14) -> List[float]:
        """
        Williams %R.
        
        Args:
            high: List of high prices
            low: List of low prices
            close: List of closing prices
            period: Calculation period
            
        Returns:
            List of Williams %R values (-100 to 0)
        """
        if len(high) != len(low) != len(close) or len(close) < period:
            return [np.nan] * len(close)
        
        williams_r = []
        
        for i in range(len(close)):
            if i < period - 1:
                williams_r.append(np.nan)
            else:
                period_high = max(high[i-period+1:i+1])
                period_low = min(low[i-period+1:i+1])
                
                if period_high == period_low:
                    williams_r.append(-50.0)
                else:
                    wr = ((period_high - close[i]) / (period_high - period_low)) * -100
                    williams_r.append(wr)
        
        return williams_r

class SignalGenerator:
    """Generate trading signals from technical indicators."""
    
    @staticmethod
    def sma_crossover(prices: List[float], fast_period: int = 10, 
                     slow_period: int = 30) -> List[str]:
        """
        Generate signals from SMA crossover.
        
        Returns:
            List of signals: 'buy', 'sell', or 'hold'
        """
        fast_sma = TechnicalIndicators.sma(prices, fast_period)
        slow_sma = TechnicalIndicators.sma(prices, slow_period)
        
        signals = []
        for i in range(len(prices)):
            if i == 0 or np.isnan(fast_sma[i]) or np.isnan(slow_sma[i]):
                signals.append('hold')
            else:
                # Check for crossover
                if (fast_sma[i-1] <= slow_sma[i-1] and fast_sma[i] > slow_sma[i]):
                    signals.append('buy')
                elif (fast_sma[i-1] >= slow_sma[i-1] and fast_sma[i] < slow_sma[i]):
                    signals.append('sell')
                else:
                    signals.append('hold')
        
        return signals
    
    @staticmethod
    def rsi_signals(prices: List[float], period: int = 14, 
                   overbought: float = 70, oversold: float = 30) -> List[str]:
        """
        Generate signals from RSI levels.
        
        Returns:
            List of signals based on RSI overbought/oversold levels
        """
        rsi_values = TechnicalIndicators.rsi(prices, period)
        
        signals = []
        for i, rsi in enumerate(rsi_values):
            if np.isnan(rsi):
                signals.append('hold')
            elif rsi > overbought:
                signals.append('sell')
            elif rsi < oversold:
                signals.append('buy')
            else:
                signals.append('hold')
        
        return signals
    
    @staticmethod
    def bollinger_signals(prices: List[float], period: int = 20, 
                         std_dev: float = 2.0) -> List[str]:
        """
        Generate signals from Bollinger Bands.
        
        Returns:
            List of signals based on price position relative to bands
        """
        middle, upper, lower = TechnicalIndicators.bollinger_bands(prices, period, std_dev)
        
        signals = []
        for i in range(len(prices)):
            if i == 0 or np.isnan(upper[i]) or np.isnan(lower[i]):
                signals.append('hold')
            else:
                # Price touching upper band - potential sell
                if prices[i] >= upper[i] and prices[i-1] < upper[i-1]:
                    signals.append('sell')
                # Price touching lower band - potential buy
                elif prices[i] <= lower[i] and prices[i-1] > lower[i-1]:
                    signals.append('buy')
                # Price crossing middle band
                elif (prices[i-1] <= middle[i-1] and prices[i] > middle[i]):
                    signals.append('buy')
                elif (prices[i-1] >= middle[i-1] and prices[i] < middle[i]):
                    signals.append('sell')
                else:
                    signals.append('hold')
        
        return signals
    
    @staticmethod
    def macd_signals(prices: List[float], fast: int = 12, 
                    slow: int = 26, signal: int = 9) -> List[str]:
        """
        Generate signals from MACD crossover.
        
        Returns:
            List of signals based on MACD line and signal line crossover
        """
        macd_line, signal_line, histogram = TechnicalIndicators.macd(prices, fast, slow, signal)
        
        signals = []
        for i in range(len(prices)):
            if i == 0 or np.isnan(macd_line[i]) or np.isnan(signal_line[i]):
                signals.append('hold')
            else:
                # MACD line crosses above signal line
                if (macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i]):
                    signals.append('buy')
                # MACD line crosses below signal line
                elif (macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i]):
                    signals.append('sell')
                else:
                    signals.append('hold')
        
        return signals

def calculate_all_indicators(price_data: List[PriceData], 
                           config: Dict[str, Any] = None) -> Dict[str, List[float]]:
    """
    Calculate all technical indicators for given price data.
    
    Args:
        price_data: List of price data points
        config: Configuration dictionary for indicator parameters
        
    Returns:
        Dictionary containing all calculated indicators
    """
    if not price_data:
        return {}
    
    # Default configuration
    default_config = {
        'sma_fast': 10,
        'sma_slow': 30,
        'ema_period': 12,
        'rsi_period': 14,
        'bb_period': 20,
        'bb_std_dev': 2.0,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'atr_period': 14,
        'stoch_k': 14,
        'stoch_d': 3
    }
    
    if config:
        default_config.update(config)
    
    # Extract price arrays
    closes = [p.close for p in price_data]
    highs = [p.high for p in price_data]
    lows = [p.low for p in price_data]
    
    # Calculate all indicators
    indicators = {
        'sma_fast': TechnicalIndicators.sma(closes, default_config['sma_fast']),
        'sma_slow': TechnicalIndicators.sma(closes, default_config['sma_slow']),
        'ema': TechnicalIndicators.ema(closes, default_config['ema_period']),
        'rsi': TechnicalIndicators.rsi(closes, default_config['rsi_period']),
        'atr': TechnicalIndicators.atr(highs, lows, closes, default_config['atr_period']),
        'williams_r': TechnicalIndicators.williams_r(highs, lows, closes)
    }
    
    # Bollinger Bands
    bb_middle, bb_upper, bb_lower = TechnicalIndicators.bollinger_bands(
        closes, default_config['bb_period'], default_config['bb_std_dev']
    )
    indicators.update({
        'bb_middle': bb_middle,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower
    })
    
    # MACD
    macd_line, signal_line, histogram = TechnicalIndicators.macd(
        closes, default_config['macd_fast'], 
        default_config['macd_slow'], default_config['macd_signal']
    )
    indicators.update({
        'macd_line': macd_line,
        'macd_signal': signal_line,
        'macd_histogram': histogram
    })
    
    # Stochastic
    stoch_k, stoch_d = TechnicalIndicators.stochastic(
        highs, lows, closes, default_config['stoch_k'], default_config['stoch_d']
    )
    indicators.update({
        'stoch_k': stoch_k,
        'stoch_d': stoch_d
    })
    
    return indicators