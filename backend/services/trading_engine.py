from datetime import datetime
from typing import Dict, List, Optional
from backend.models.database import Trade, TradingSession, get_session
from backend.services.data_service import forex_service
from backend.services.trading_algorithms import TradingAlgorithms
from config.settings import Config
import threading
import time

class TradingEngine:
    """Main trading execution engine"""
    
    def __init__(self):
        self.algorithms = TradingAlgorithms()
        self.is_running = False
        self.current_session = None
        self.total_volume_today = 0.0
        self.auto_trading_enabled = True
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize or get current trading session"""
        session = get_session()
        try:
            # Check if there's an active session
            active_session = session.query(TradingSession).filter_by(is_active=True).first()
            
            if not active_session:
                # Create new session
                self.current_session = TradingSession()
                session.add(self.current_session)
                session.commit()
            else:
                self.current_session = active_session
            
            # Calculate today's volume
            self._calculate_daily_volume()
            
        except Exception as e:
            print(f"Error initializing session: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _calculate_daily_volume(self):
        """Calculate total trading volume for today"""
        session = get_session()
        try:
            today = datetime.now().date()
            trades = session.query(Trade).filter(
                Trade.timestamp >= today,
                Trade.status == 'EXECUTED'
            ).all()
            
            self.total_volume_today = sum(trade.amount * trade.price for trade in trades)
            
        except Exception as e:
            print(f"Error calculating daily volume: {e}")
        finally:
            session.close()
    
    def execute_trade(self, pair: str, side: str, amount: float, algorithm: str = None) -> Dict:
        """Execute a trade"""
        try:
            # Check if auto trading is enabled
            if not self.auto_trading_enabled:
                return {'status': 'error', 'message': 'Auto trading is disabled'}
            
            # Get current price
            price_data = forex_service.get_current_price(pair)
            if not price_data:
                return {'status': 'error', 'message': 'Price data unavailable'}
            
            # Use bid for sell, ask for buy
            price = price_data['ask'] if side == 'BUY' else price_data['bid']
            trade_value = amount * price
            
            # Check volume limit
            if self.total_volume_today + trade_value > Config.MAX_TRADING_VOLUME:
                self._disable_auto_trading()
                return {
                    'status': 'error', 
                    'message': f'Trading volume limit of ${Config.MAX_TRADING_VOLUME:,.0f} would be exceeded'
                }
            
            # Create trade record
            session = get_session()
            try:
                trade = Trade(
                    pair=pair,
                    side=side,
                    amount=amount,
                    price=price,
                    algorithm=algorithm,
                    status='EXECUTED'
                )
                
                session.add(trade)
                session.commit()
                
                # Update volume tracking
                self.total_volume_today += trade_value
                
                # Update session
                if self.current_session:
                    self.current_session.total_volume += trade_value
                    session.commit()
                
                return {
                    'status': 'success',
                    'trade_id': trade.id,
                    'pair': pair,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'value': trade_value,
                    'timestamp': trade.timestamp
                }
                
            except Exception as e:
                session.rollback()
                return {'status': 'error', 'message': f'Database error: {str(e)}'}
            finally:
                session.close()
                
        except Exception as e:
            return {'status': 'error', 'message': f'Execution error: {str(e)}'}
    
    def _disable_auto_trading(self):
        """Disable auto trading when volume limit is reached"""
        self.auto_trading_enabled = False
        session = get_session()
        try:
            if self.current_session:
                self.current_session.auto_trading_enabled = False
                session.commit()
            print(f"Auto trading disabled - volume limit of ${Config.MAX_TRADING_VOLUME:,.0f} reached")
        except Exception as e:
            print(f"Error disabling auto trading: {e}")
        finally:
            session.close()
    
    def start_auto_trading(self):
        """Start automated trading based on algorithms"""
        if self.is_running:
            return
        
        self.is_running = True
        threading.Thread(target=self._trading_loop, daemon=True).start()
        print("Auto trading started")
    
    def stop_auto_trading(self):
        """Stop automated trading"""
        self.is_running = False
        print("Auto trading stopped")
    
    def _trading_loop(self):
        """Main trading loop"""
        while self.is_running and self.auto_trading_enabled:
            try:
                for pair in Config.CURRENCY_PAIRS:
                    # Get recent prices for analysis
                    prices = forex_service.get_prices_for_algorithm(pair, 50)
                    
                    if len(prices) < 30:  # Need enough data
                        continue
                    
                    # Generate trading signals
                    signals = self.algorithms.generate_combined_signal(prices)
                    
                    # Execute based on consensus
                    if signals['consensus'] in ['BUY', 'SELL']:
                        # Use small position size for demo (1000 units)
                        amount = 1000.0
                        
                        result = self.execute_trade(
                            pair=pair,
                            side=signals['consensus'],
                            amount=amount,
                            algorithm='CONSENSUS'
                        )
                        
                        if result['status'] == 'success':
                            print(f"Executed {signals['consensus']} {amount} {pair} at {result['price']}")
                        elif 'volume limit' in result['message']:
                            print("Volume limit reached, stopping auto trading")
                            break
                
                # Wait before next analysis (30 seconds)
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        session = get_session()
        try:
            trades = session.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
            
            return [{
                'id': trade.id,
                'pair': trade.pair,
                'side': trade.side,
                'amount': trade.amount,
                'price': trade.price,
                'value': trade.amount * trade.price,
                'timestamp': trade.timestamp.isoformat(),
                'algorithm': trade.algorithm,
                'status': trade.status,
                'pnl': trade.pnl
            } for trade in trades]
            
        except Exception as e:
            print(f"Error getting trade history: {e}")
            return []
        finally:
            session.close()
    
    def get_trading_stats(self) -> Dict:
        """Get current trading statistics"""
        return {
            'is_running': self.is_running,
            'auto_trading_enabled': self.auto_trading_enabled,
            'total_volume_today': self.total_volume_today,
            'volume_limit': Config.MAX_TRADING_VOLUME,
            'remaining_capacity': Config.MAX_TRADING_VOLUME - self.total_volume_today,
            'session_id': self.current_session.id if self.current_session else None
        }

# Global instance
trading_engine = TradingEngine()