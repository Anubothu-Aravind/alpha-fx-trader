import random
import time
from datetime import datetime, timedelta
from typing import Dict, List
import threading
from config.settings import Config

class ForexDataService:
    """Mock forex data service for demonstration"""
    
    def __init__(self):
        self.current_prices = {
            'EUR/USD': 1.0850,
            'GBP/USD': 1.2650,
            'USD/JPY': 149.50,
            'USD/CHF': 0.9150,
            'AUD/USD': 0.6450,
            'USD/CAD': 1.3650
        }
        
        self.price_history = {pair: [] for pair in Config.CURRENCY_PAIRS}
        self.is_streaming = False
        self.subscribers = []
        
        # Initialize with some historical data
        self._generate_initial_history()
    
    def _generate_initial_history(self):
        """Generate initial historical data"""
        for pair in Config.CURRENCY_PAIRS:
            base_price = self.current_prices[pair]
            history = []
            
            # Generate 100 historical points
            for i in range(100, 0, -1):
                timestamp = datetime.now() - timedelta(minutes=i)
                # Add some random walk to price
                change = random.uniform(-0.002, 0.002)
                price = base_price * (1 + change * (i / 100))
                
                history.append({
                    'pair': pair,
                    'bid': price - 0.0001,
                    'ask': price + 0.0001,
                    'timestamp': timestamp,
                    'price': price
                })
            
            self.price_history[pair] = history
    
    def get_current_price(self, pair: str) -> Dict:
        """Get current price for a currency pair"""
        if pair not in self.current_prices:
            return None
        
        base_price = self.current_prices[pair]
        spread = 0.0002  # 2 pips spread
        
        return {
            'pair': pair,
            'bid': base_price - spread/2,
            'ask': base_price + spread/2,
            'timestamp': datetime.now(),
            'price': base_price
        }
    
    def get_historical_data(self, pair: str, limit: int = 100) -> List[Dict]:
        """Get historical price data"""
        if pair not in self.price_history:
            return []
        
        return self.price_history[pair][-limit:]
    
    def subscribe_to_updates(self, callback):
        """Subscribe to real-time price updates"""
        self.subscribers.append(callback)
    
    def unsubscribe_from_updates(self, callback):
        """Unsubscribe from price updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def start_price_stream(self):
        """Start streaming real-time price updates"""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        threading.Thread(target=self._price_update_loop, daemon=True).start()
    
    def stop_price_stream(self):
        """Stop streaming price updates"""
        self.is_streaming = False
    
    def _price_update_loop(self):
        """Internal loop for price updates"""
        while self.is_streaming:
            try:
                for pair in Config.CURRENCY_PAIRS:
                    # Simulate price movement
                    current = self.current_prices[pair]
                    change_percent = random.uniform(-0.001, 0.001)  # Max 0.1% change
                    new_price = current * (1 + change_percent)
                    
                    self.current_prices[pair] = new_price
                    
                    # Create price update
                    price_update = {
                        'pair': pair,
                        'bid': new_price - 0.0001,
                        'ask': new_price + 0.0001,
                        'timestamp': datetime.now(),
                        'price': new_price
                    }
                    
                    # Add to history
                    self.price_history[pair].append(price_update)
                    
                    # Keep only last 1000 points
                    if len(self.price_history[pair]) > 1000:
                        self.price_history[pair] = self.price_history[pair][-1000:]
                    
                    # Notify subscribers
                    for callback in self.subscribers:
                        try:
                            callback(price_update)
                        except Exception as e:
                            print(f"Error notifying subscriber: {e}")
                
                # Update every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                print(f"Error in price update loop: {e}")
                time.sleep(5)
    
    def get_prices_for_algorithm(self, pair: str, count: int = 50) -> List[float]:
        """Get price list for algorithm calculations"""
        history = self.get_historical_data(pair, count)
        return [item['price'] for item in history]

# Global instance
forex_service = ForexDataService()