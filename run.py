#!/usr/bin/env python3
"""
AlphaFX Trader - Simplified version with built-in libraries
Entry point for the application
"""

import sys
import os
import http.server
import socketserver
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
import random
import math

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Global data stores
current_prices = {}
price_history = {}
trades = []
trading_stats = {
    'total_volume': 0.0,
    'auto_trading_enabled': True,
    'is_running': False
}

CURRENCY_PAIRS = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD']
MAX_VOLUME = 10000000  # $10M

class TradingAlgorithms:
    """Simplified trading algorithms"""
    
    @staticmethod
    def calculate_sma(prices, period):
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas[-period:]]
        losses = [-min(delta, 0) for delta in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def generate_signals(self, prices):
        """Generate trading signals"""
        if len(prices) < 30:
            return None
        
        sma_short = self.calculate_sma(prices, 10)
        sma_long = self.calculate_sma(prices, 30)
        rsi = self.calculate_rsi(prices)
        
        signals = []
        
        # SMA crossover
        if sma_short and sma_long:
            if sma_short > sma_long:
                signals.append('BUY')
            else:
                signals.append('SELL')
        
        # RSI signals
        if rsi:
            if rsi <= 30:
                signals.append('BUY')
            elif rsi >= 70:
                signals.append('SELL')
        
        # Consensus (need 2 signals)
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count >= 2:
            return 'BUY'
        elif sell_count >= 1:  # Lower threshold for demo
            return 'SELL'
        
        return None

class ForexDataService:
    """Simplified forex data service"""
    
    def __init__(self):
        self.algorithms = TradingAlgorithms()
        self.running = False
        
        # Initialize prices
        base_prices = {
            'EUR/USD': 1.0850, 'GBP/USD': 1.2650, 'USD/JPY': 149.50,
            'USD/CHF': 0.9150, 'AUD/USD': 0.6450, 'USD/CAD': 1.3650
        }
        
        for pair in CURRENCY_PAIRS:
            current_prices[pair] = base_prices[pair]
            price_history[pair] = [base_prices[pair]] * 50  # Initialize with 50 points
    
    def start_price_updates(self):
        """Start price update thread"""
        self.running = True
        threading.Thread(target=self._update_prices, daemon=True).start()
        print("Price updates started")
    
    def _update_prices(self):
        """Update prices continuously"""
        while self.running:
            for pair in CURRENCY_PAIRS:
                # Simulate price movement
                current = current_prices[pair]
                change = random.uniform(-0.001, 0.001)
                new_price = current * (1 + change)
                
                current_prices[pair] = new_price
                price_history[pair].append(new_price)
                
                # Keep last 100 prices
                if len(price_history[pair]) > 100:
                    price_history[pair] = price_history[pair][-100:]
                
                # Check for trading signals
                if trading_stats['auto_trading_enabled'] and trading_stats['is_running']:
                    self._check_signals(pair)
            
            time.sleep(2)  # Update every 2 seconds
    
    def _check_signals(self, pair):
        """Check for trading signals"""
        signal = self.algorithms.generate_signals(price_history[pair])
        
        if signal and trading_stats['total_volume'] < MAX_VOLUME:
            self._execute_trade(pair, signal)
    
    def _execute_trade(self, pair, side):
        """Execute a trade"""
        price = current_prices[pair]
        amount = 1000.0  # Fixed amount
        value = amount * price
        
        if trading_stats['total_volume'] + value > MAX_VOLUME:
            trading_stats['auto_trading_enabled'] = False
            print(f"Volume limit reached! Auto trading disabled.")
            return
        
        trade = {
            'id': len(trades) + 1,
            'pair': pair,
            'side': side,
            'amount': amount,
            'price': price,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'algorithm': 'AUTO'
        }
        
        trades.append(trade)
        trading_stats['total_volume'] += value
        
        print(f"Trade executed: {side} {amount} {pair} at {price:.5f}")

class APIHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP API handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self._serve_file('frontend/index.html', 'text/html')
        elif self.path.startswith('/css/'):
            self._serve_file(f'frontend{self.path}', 'text/css')
        elif self.path.startswith('/js/'):
            self._serve_file(f'frontend{self.path}', 'text/javascript')
        elif self.path == '/api/prices':
            self._send_json({
                pair: {
                    'price': price,
                    'bid': price - 0.0001,
                    'ask': price + 0.0001,
                    'timestamp': datetime.now().isoformat()
                } for pair, price in current_prices.items()
            })
        elif self.path.startswith('/api/prices/'):
            pair = self.path.split('/')[-1]
            if pair in current_prices:
                price = current_prices[pair]
                self._send_json({
                    'pair': pair,
                    'price': price,
                    'bid': price - 0.0001,
                    'ask': price + 0.0001,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self._send_error(404, 'Pair not found')
        elif self.path == '/api/trades':
            self._send_json(trades[-50:])  # Last 50 trades
        elif self.path == '/api/trading/status':
            remaining = MAX_VOLUME - trading_stats['total_volume']
            self._send_json({
                'is_running': trading_stats['is_running'],
                'auto_trading_enabled': trading_stats['auto_trading_enabled'],
                'total_volume_today': trading_stats['total_volume'],
                'volume_limit': MAX_VOLUME,
                'remaining_capacity': remaining
            })
        elif self.path.startswith('/api/historical/'):
            pair = self.path.split('/')[-1].split('?')[0]
            if pair in price_history:
                history = []
                for i, price in enumerate(price_history[pair][-50:]):
                    timestamp = datetime.now() - timedelta(minutes=50-i)
                    history.append({
                        'timestamp': timestamp.isoformat(),
                        'price': price,
                        'bid': price - 0.0001,
                        'ask': price + 0.0001
                    })
                self._send_json(history)
            else:
                self._send_error(404, 'Pair not found')
        else:
            self._send_error(404, 'Not found')
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            data = {}
        
        if self.path == '/api/trade':
            self._handle_manual_trade(data)
        elif self.path == '/api/trading/start':
            trading_stats['is_running'] = True
            self._send_json({'status': 'Auto trading started'})
        elif self.path == '/api/trading/stop':
            trading_stats['is_running'] = False
            self._send_json({'status': 'Auto trading stopped'})
        elif self.path == '/api/backtest':
            self._handle_backtest(data)
        else:
            self._send_error(404, 'Not found')
    
    def _handle_manual_trade(self, data):
        """Handle manual trade execution"""
        pair = data.get('pair')
        side = data.get('side')
        amount = float(data.get('amount', 0))
        
        if not pair or not side or amount <= 0:
            self._send_error(400, 'Invalid parameters')
            return
        
        if pair not in current_prices:
            self._send_error(400, 'Invalid pair')
            return
        
        price = current_prices[pair]
        value = amount * price
        
        if trading_stats['total_volume'] + value > MAX_VOLUME:
            self._send_json({
                'status': 'error',
                'message': f'Volume limit of ${MAX_VOLUME:,} would be exceeded'
            })
            return
        
        trade = {
            'id': len(trades) + 1,
            'pair': pair,
            'side': side,
            'amount': amount,
            'price': price,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'algorithm': 'MANUAL',
            'status': 'EXECUTED'
        }
        
        trades.append(trade)
        trading_stats['total_volume'] += value
        
        self._send_json({
            'status': 'success',
            **trade
        })
    
    def _handle_backtest(self, data):
        """Handle backtesting request"""
        pair = data.get('pair', 'EUR/USD')
        days = int(data.get('days', 30))
        initial_balance = float(data.get('initial_balance', 100000))
        
        # Generate mock backtest results
        total_trades = random.randint(10, 30)
        winning_trades = random.randint(int(total_trades * 0.4), int(total_trades * 0.7))
        final_balance = initial_balance * random.uniform(0.95, 1.15)
        total_return = (final_balance - initial_balance) / initial_balance * 100
        
        result = {
            'pair': pair,
            'start_date': (datetime.now() - timedelta(days=days)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_return_pct': round(total_return, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades,
            'win_rate_pct': round(winning_trades / total_trades * 100, 2),
            'max_drawdown_pct': round(random.uniform(2, 8), 2)
        }
        
        self._send_json(result)
    
    def _serve_file(self, filepath, content_type):
        """Serve static files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self._send_error(404, 'File not found')
    
    def _send_json(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', len(json_data.encode('utf-8')))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = json.dumps({'error': message})
        self.wfile.write(error_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    """Main entry point"""
    print("Starting AlphaFX Trader (Simplified Version)...")
    
    # Start forex data service
    forex_service = ForexDataService()
    forex_service.start_price_updates()
    
    # Start HTTP server
    port = 5000
    with socketserver.TCPServer(("", port), APIHandler) as httpd:
        print(f"AlphaFX Trader started successfully!")
        print(f"Access the application at: http://localhost:{port}")
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down AlphaFX Trader...")
            forex_service.running = False
            print("AlphaFX Trader stopped.")

if __name__ == '__main__':
    main()