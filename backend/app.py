from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import json

from backend.services.data_service import forex_service
from backend.services.trading_engine import trading_engine
from backend.services.backtesting import backtesting_engine
from config.settings import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected clients
connected_clients = set()

@app.route('/')
def index():
    """Serve the main application"""
    return app.send_static_file('index.html')

@app.route('/api/prices/<pair>')
def get_price(pair):
    """Get current price for a currency pair"""
    try:
        price_data = forex_service.get_current_price(pair)
        if not price_data:
            return jsonify({'error': 'Price data not available'}), 404
        
        return jsonify({
            'pair': price_data['pair'],
            'bid': price_data['bid'],
            'ask': price_data['ask'],
            'price': price_data['price'],
            'timestamp': price_data['timestamp'].isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices')
def get_all_prices():
    """Get current prices for all currency pairs"""
    try:
        prices = {}
        for pair in Config.CURRENCY_PAIRS:
            price_data = forex_service.get_current_price(pair)
            if price_data:
                prices[pair] = {
                    'bid': price_data['bid'],
                    'ask': price_data['ask'],
                    'price': price_data['price'],
                    'timestamp': price_data['timestamp'].isoformat()
                }
        
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical/<pair>')
def get_historical_data(pair):
    """Get historical price data"""
    try:
        limit = request.args.get('limit', 100, type=int)
        data = forex_service.get_historical_data(pair, limit)
        
        formatted_data = []
        for item in data:
            formatted_data.append({
                'timestamp': item['timestamp'].isoformat(),
                'price': item['price'],
                'bid': item['bid'],
                'ask': item['ask']
            })
        
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def execute_manual_trade():
    """Execute a manual trade"""
    try:
        data = request.json
        pair = data.get('pair')
        side = data.get('side')  # BUY or SELL
        amount = float(data.get('amount', 0))
        
        if not pair or not side or amount <= 0:
            return jsonify({'error': 'Invalid trade parameters'}), 400
        
        result = trading_engine.execute_trade(pair, side, amount, 'MANUAL')
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        trades = trading_engine.get_trade_history(limit)
        return jsonify(trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/start', methods=['POST'])
def start_auto_trading():
    """Start automated trading"""
    try:
        trading_engine.start_auto_trading()
        return jsonify({'status': 'Auto trading started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/stop', methods=['POST'])
def stop_auto_trading():
    """Stop automated trading"""
    try:
        trading_engine.stop_auto_trading()
        return jsonify({'status': 'Auto trading stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/status')
def get_trading_status():
    """Get trading engine status"""
    try:
        stats = trading_engine.get_trading_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtesting"""
    try:
        data = request.json
        pair = data.get('pair', 'EUR/USD')
        days = int(data.get('days', 30))
        initial_balance = float(data.get('initial_balance', 100000))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if data.get('multi_pair', False):
            pairs = data.get('pairs', Config.CURRENCY_PAIRS[:3])  # Default to first 3 pairs
            result = backtesting_engine.run_multi_pair_backtest(pairs, start_date, end_date, initial_balance)
        else:
            result = backtesting_engine.run_backtest(pair, start_date, end_date, initial_balance)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/algorithms/signals/<pair>')
def get_algorithm_signals(pair):
    """Get current algorithm signals for a pair"""
    try:
        prices = forex_service.get_prices_for_algorithm(pair, 50)
        if len(prices) < 30:
            return jsonify({'error': 'Insufficient price data'}), 400
        
        signals = trading_engine.algorithms.generate_combined_signal(prices)
        
        # Get indicator values for display
        sma_short = trading_engine.algorithms.calculate_sma(prices, Config.SMA_SHORT_PERIOD)
        sma_long = trading_engine.algorithms.calculate_sma(prices, Config.SMA_LONG_PERIOD)
        rsi = trading_engine.algorithms.calculate_rsi(prices, Config.RSI_PERIOD)
        bb_upper, bb_middle, bb_lower = trading_engine.algorithms.calculate_bollinger_bands(prices)
        
        return jsonify({
            'pair': pair,
            'signals': signals,
            'indicators': {
                'sma_short': sma_short[-1] if sma_short and sma_short[-1] else None,
                'sma_long': sma_long[-1] if sma_long and sma_long[-1] else None,
                'rsi': rsi[-1] if rsi and rsi[-1] else None,
                'bollinger_upper': bb_upper[-1] if bb_upper and bb_upper[-1] else None,
                'bollinger_middle': bb_middle[-1] if bb_middle and bb_middle[-1] else None,
                'bollinger_lower': bb_lower[-1] if bb_lower and bb_lower[-1] else None,
                'current_price': prices[-1] if prices else None
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'Connected to AlphaFxTrader'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    print(f'Client disconnected: {request.sid}')

@socketio.on('subscribe_prices')
def handle_subscribe_prices(data):
    """Subscribe client to price updates"""
    print(f'Client {request.sid} subscribed to price updates')
    # Send current prices immediately
    prices = {}
    for pair in Config.CURRENCY_PAIRS:
        price_data = forex_service.get_current_price(pair)
        if price_data:
            prices[pair] = {
                'bid': price_data['bid'],
                'ask': price_data['ask'],
                'price': price_data['price'],
                'timestamp': price_data['timestamp'].isoformat()
            }
    
    emit('price_update', prices)

def broadcast_price_update(price_data):
    """Broadcast price update to all connected clients"""
    if connected_clients:
        socketio.emit('price_update', {
            price_data['pair']: {
                'bid': price_data['bid'],
                'ask': price_data['ask'],
                'price': price_data['price'],
                'timestamp': price_data['timestamp'].isoformat()
            }
        })

def broadcast_trade_update(trade_data):
    """Broadcast trade update to all connected clients"""
    if connected_clients:
        socketio.emit('trade_update', trade_data)

# Subscribe to forex service updates
forex_service.subscribe_to_updates(broadcast_price_update)

if __name__ == '__main__':
    # Initialize database
    from backend.models.database import create_database
    create_database()
    
    # Start forex data stream
    forex_service.start_price_stream()
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)