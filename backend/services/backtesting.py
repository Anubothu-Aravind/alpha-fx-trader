from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from backend.services.trading_algorithms import TradingAlgorithms
import random

class BacktestingEngine:
    """Backtesting engine for trading strategies"""
    
    def __init__(self):
        self.algorithms = TradingAlgorithms()
    
    def generate_historical_data(self, pair: str, start_date: datetime, end_date: datetime, interval_minutes: int = 5) -> List[Dict]:
        """Generate mock historical data for backtesting"""
        data = []
        current_time = start_date
        
        # Starting price based on pair
        base_prices = {
            'EUR/USD': 1.0800,
            'GBP/USD': 1.2600,
            'USD/JPY': 148.00,
            'USD/CHF': 0.9100,
            'AUD/USD': 0.6400,
            'USD/CAD': 1.3600
        }
        
        current_price = base_prices.get(pair, 1.0000)
        
        while current_time <= end_date:
            # Simulate realistic price movement
            change_percent = random.normalvariate(0, 0.002)  # Normal distribution, 0.2% std dev
            current_price *= (1 + change_percent)
            
            # Add some trend and volatility
            trend = random.uniform(-0.0005, 0.0005)
            current_price *= (1 + trend)
            
            data.append({
                'timestamp': current_time,
                'pair': pair,
                'open': current_price,
                'high': current_price * (1 + abs(random.normalvariate(0, 0.001))),
                'low': current_price * (1 - abs(random.normalvariate(0, 0.001))),
                'close': current_price,
                'volume': random.randint(1000, 10000)
            })
            
            current_time += timedelta(minutes=interval_minutes)
        
        return data
    
    def run_backtest(self, pair: str, start_date: datetime, end_date: datetime, 
                     initial_balance: float = 100000, position_size: float = 10000) -> Dict:
        """Run backtest for a specific pair and date range"""
        
        # Generate historical data
        historical_data = self.generate_historical_data(pair, start_date, end_date)
        
        if len(historical_data) < 50:
            return {'error': 'Insufficient historical data'}
        
        # Initialize backtest variables
        balance = initial_balance
        position = 0  # 0 = no position, 1 = long, -1 = short
        entry_price = 0
        trades = []
        equity_curve = []
        
        # Extract prices for algorithm calculations
        prices = [candle['close'] for candle in historical_data]
        
        for i in range(30, len(historical_data)):  # Start after enough data for indicators
            current_candle = historical_data[i]
            current_price = current_candle['close']
            current_time = current_candle['timestamp']
            
            # Get price history up to current point
            price_history = prices[:i+1]
            
            # Generate trading signals
            signals = self.algorithms.generate_combined_signal(price_history)
            signal = signals.get('consensus')
            
            # Execute trades based on signals
            if signal == 'BUY' and position <= 0:
                # Close short position if any
                if position == -1:
                    pnl = (entry_price - current_price) * position_size
                    balance += pnl
                    trades.append({
                        'timestamp': current_time,
                        'type': 'CLOSE_SHORT',
                        'price': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })
                
                # Open long position
                if balance >= position_size * current_price * 0.1:  # 10x leverage simulation
                    position = 1
                    entry_price = current_price
                    trades.append({
                        'timestamp': current_time,
                        'type': 'BUY',
                        'price': current_price,
                        'pnl': 0,
                        'balance': balance
                    })
            
            elif signal == 'SELL' and position >= 0:
                # Close long position if any
                if position == 1:
                    pnl = (current_price - entry_price) * position_size
                    balance += pnl
                    trades.append({
                        'timestamp': current_time,
                        'type': 'CLOSE_LONG',
                        'price': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })
                
                # Open short position
                if balance >= position_size * current_price * 0.1:  # 10x leverage simulation
                    position = -1
                    entry_price = current_price
                    trades.append({
                        'timestamp': current_time,
                        'type': 'SELL',
                        'price': current_price,
                        'pnl': 0,
                        'balance': balance
                    })
            
            # Calculate current equity (mark-to-market)
            current_equity = balance
            if position != 0:
                unrealized_pnl = (current_price - entry_price) * position * position_size
                current_equity += unrealized_pnl
            
            equity_curve.append({
                'timestamp': current_time,
                'balance': balance,
                'equity': current_equity,
                'position': position
            })
        
        # Close any remaining position
        if position != 0:
            final_price = historical_data[-1]['close']
            pnl = (final_price - entry_price) * position * position_size
            balance += pnl
            trades.append({
                'timestamp': historical_data[-1]['timestamp'],
                'type': 'CLOSE_FINAL',
                'price': final_price,
                'pnl': pnl,
                'balance': balance
            })
        
        # Calculate performance metrics
        total_return = (balance - initial_balance) / initial_balance * 100
        total_trades = len([t for t in trades if t['type'] in ['CLOSE_LONG', 'CLOSE_SHORT', 'CLOSE_FINAL']])
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades if t.get('pnl', 0) < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate max drawdown
        peak = initial_balance
        max_drawdown = 0
        for point in equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            drawdown = (peak - point['equity']) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'pair': pair,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_balance': initial_balance,
            'final_balance': balance,
            'total_return_pct': round(total_return, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': round(win_rate, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'trades': trades,
            'equity_curve': equity_curve[-100:] if len(equity_curve) > 100 else equity_curve  # Last 100 points
        }
    
    def run_multi_pair_backtest(self, pairs: List[str], start_date: datetime, end_date: datetime, 
                               initial_balance: float = 100000) -> Dict:
        """Run backtest across multiple currency pairs"""
        results = {}
        balance_per_pair = initial_balance / len(pairs)
        
        total_final_balance = 0
        total_trades = 0
        total_winning_trades = 0
        
        for pair in pairs:
            result = self.run_backtest(pair, start_date, end_date, balance_per_pair, balance_per_pair * 0.1)
            if 'error' not in result:
                results[pair] = result
                total_final_balance += result['final_balance']
                total_trades += result['total_trades']
                total_winning_trades += result['winning_trades']
        
        # Calculate combined metrics
        total_return = (total_final_balance - initial_balance) / initial_balance * 100
        combined_win_rate = (total_winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'pairs': pairs,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_balance': initial_balance,
            'final_balance': total_final_balance,
            'total_return_pct': round(total_return, 2),
            'total_trades': total_trades,
            'winning_trades': total_winning_trades,
            'combined_win_rate_pct': round(combined_win_rate, 2),
            'pair_results': results
        }

# Global instance
backtesting_engine = BacktestingEngine()