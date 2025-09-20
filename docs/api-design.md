# AlphaFX Trader - API Design

## REST API Endpoints

### Price Data Endpoints

#### GET /api/prices
Get current prices for all currency pairs
```json
Response:
{
  "EUR/USD": {
    "bid": 1.08499,
    "ask": 1.08501,
    "price": 1.08500,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "GBP/USD": {
    "bid": 1.26499,
    "ask": 1.26501,
    "price": 1.26500,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### GET /api/prices/{pair}
Get current price for a specific currency pair
```json
Response:
{
  "pair": "EUR/USD",
  "bid": 1.08499,
  "ask": 1.08501,
  "price": 1.08500,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/historical/{pair}?limit=100
Get historical price data for a currency pair
```json
Response: [
  {
    "timestamp": "2024-01-15T10:29:00Z",
    "price": 1.08495,
    "bid": 1.08494,
    "ask": 1.08496
  }
]
```

### Trading Endpoints

#### POST /api/trade
Execute a manual trade
```json
Request:
{
  "pair": "EUR/USD",
  "side": "BUY",
  "amount": 10000
}

Response:
{
  "status": "success",
  "trade_id": 123,
  "pair": "EUR/USD",
  "side": "BUY",
  "amount": 10000,
  "price": 1.08501,
  "value": 108501.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /api/trades?limit=100
Get trade history
```json
Response: [
  {
    "id": 123,
    "pair": "EUR/USD",
    "side": "BUY",
    "amount": 10000,
    "price": 1.08501,
    "value": 108501.0,
    "timestamp": "2024-01-15T10:30:00Z",
    "algorithm": "SMA",
    "status": "EXECUTED",
    "pnl": 0.0
  }
]
```

### Trading Control Endpoints

#### POST /api/trading/start
Start automated trading
```json
Response:
{
  "status": "Auto trading started"
}
```

#### POST /api/trading/stop
Stop automated trading
```json
Response:
{
  "status": "Auto trading stopped"
}
```

#### GET /api/trading/status
Get trading engine status
```json
Response:
{
  "is_running": true,
  "auto_trading_enabled": true,
  "total_volume_today": 2500000.0,
  "volume_limit": 10000000.0,
  "remaining_capacity": 7500000.0,
  "session_id": 1
}
```

### Algorithm Endpoints

#### GET /api/algorithms/signals/{pair}
Get current algorithm signals and indicators
```json
Response:
{
  "pair": "EUR/USD",
  "signals": {
    "sma": "BUY",
    "rsi": null,
    "bollinger": "SELL",
    "consensus": null
  },
  "indicators": {
    "sma_short": 1.08450,
    "sma_long": 1.08400,
    "rsi": 65.5,
    "bollinger_upper": 1.08600,
    "bollinger_middle": 1.08500,
    "bollinger_lower": 1.08400,
    "current_price": 1.08500
  }
}
```

### Backtesting Endpoints

#### POST /api/backtest
Run backtesting analysis
```json
Request:
{
  "pair": "EUR/USD",
  "days": 30,
  "initial_balance": 100000,
  "multi_pair": false
}

Response:
{
  "pair": "EUR/USD",
  "start_date": "2023-12-15T00:00:00Z",
  "end_date": "2024-01-15T00:00:00Z",
  "initial_balance": 100000,
  "final_balance": 105000,
  "total_return_pct": 5.0,
  "total_trades": 25,
  "winning_trades": 15,
  "losing_trades": 10,
  "win_rate_pct": 60.0,
  "max_drawdown_pct": 3.2,
  "trades": [],
  "equity_curve": []
}
```

## WebSocket Events

### Client to Server Events

#### connect
Client connects to WebSocket server
```json
Server Response:
{
  "status": "Connected to AlphaFxTrader"
}
```

#### subscribe_prices
Subscribe to real-time price updates
```json
Client Request:
{
  "pairs": ["EUR/USD", "GBP/USD"]
}
```

### Server to Client Events

#### price_update
Real-time price update broadcast
```json
Server Broadcast:
{
  "EUR/USD": {
    "bid": 1.08499,
    "ask": 1.08501,
    "price": 1.08500,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### trade_update
Trade execution notification
```json
Server Broadcast:
{
  "trade_id": 123,
  "pair": "EUR/USD",
  "side": "BUY",
  "amount": 10000,
  "price": 1.08501,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Database Schema

### trades table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    pair VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    amount FLOAT NOT NULL,
    price FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    algorithm VARCHAR(50),
    status VARCHAR(20) DEFAULT 'EXECUTED',
    pnl FLOAT DEFAULT 0.0,
    notes TEXT
);
```

### price_data table
```sql
CREATE TABLE price_data (
    id INTEGER PRIMARY KEY,
    pair VARCHAR(10) NOT NULL,
    bid FLOAT NOT NULL,
    ask FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### trading_sessions table
```sql
CREATE TABLE trading_sessions (
    id INTEGER PRIMARY KEY,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    total_volume FLOAT DEFAULT 0.0,
    total_pnl FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    auto_trading_enabled BOOLEAN DEFAULT TRUE
);
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes
- **INVALID_PAIR**: Invalid currency pair
- **INSUFFICIENT_FUNDS**: Not enough balance
- **VOLUME_LIMIT_EXCEEDED**: Daily volume limit reached
- **TRADING_DISABLED**: Auto trading is disabled
- **PRICE_UNAVAILABLE**: Price data not available
- **VALIDATION_ERROR**: Invalid request parameters

## Rate Limiting
- REST API: 100 requests per minute per IP
- WebSocket: 1000 messages per minute per connection
- Backtest API: 5 requests per minute (computationally expensive)

## Authentication
Current version uses local deployment without authentication.
For production deployment, implement:
- JWT token authentication
- API key management
- Role-based access control
- Session management

## API Versioning
Current version: v1 (implicit)
Future versions will use URL versioning: `/api/v2/`