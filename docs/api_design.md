# API Design Documentation

## Overview

The AlphaFX Trader API is built with FastAPI, providing a modern, high-performance REST API with automatic OpenAPI documentation, request/response validation, and async support. The API follows RESTful principles and includes real-time data streaming capabilities.

## API Base Information

- **Base URL**: `http://localhost:8000` (development)
- **API Version**: v1.0.0
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`
- **Content Type**: `application/json`

## Authentication

Currently uses open access for hackathon demo. Production deployment should implement:
- JWT token-based authentication
- API key authentication for external integrations
- Rate limiting per user/IP
- CORS configuration for trusted domains

## API Endpoints

### 1. System Health & Status

#### GET /
**Description**: Basic health check endpoint
**Response**: Simple status message

```json
{
  "message": "AlphaFX Trader API is running"
}
```

#### GET /health
**Description**: Detailed system health information
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "data_feeder_active": true,
  "trading_engine_status": {
    "auto_trading_enabled": true,
    "active_strategies": ["EUR/USD", "GBP/USD"],
    "daily_pnl": 125.50,
    "total_trades": 45
  }
}
```

### 2. Market Data Endpoints

#### GET /rates
**Description**: Get current rates for all available currency pairs
**Response**:
```json
[
  {
    "pair": "EUR/USD",
    "bid": 1.08450,
    "ask": 1.08470,
    "timestamp": "2024-01-15T10:30:00.000Z"
  },
  {
    "pair": "GBP/USD",
    "bid": 1.26420,
    "ask": 1.26450,
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
]
```

#### GET /rates/{pair}
**Description**: Get current rate for a specific currency pair
**Parameters**:
- `pair` (path): Currency pair (e.g., EUR/USD)

**Response**:
```json
{
  "pair": "EUR/USD",
  "bid": 1.08450,
  "ask": 1.08470,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Error Response (404)**:
```json
{
  "detail": "Rate for INVALID/PAIR not found"
}
```

#### GET /rates/stream
**Description**: Server-Sent Events stream of live FX rates
**Response**: Continuous stream of rate updates
**Content-Type**: `text/plain`

Example stream data:
```
data: {"timestamp": "2024-01-15T10:30:01Z", "pair": "EUR/USD", "bid": 1.08451, "ask": 1.08471, "spread": 0.00020}

data: {"timestamp": "2024-01-15T10:30:02Z", "pair": "GBP/USD", "bid": 1.26421, "ask": 1.26451, "spread": 0.00030}
```

### 3. Trading Endpoints

#### POST /trade
**Description**: Execute a trade order
**Request Body**:
```json
{
  "pair": "EUR/USD",
  "action": "buy",
  "volume": 0.5,
  "order_type": "market",
  "limit_price": null,
  "stop_loss": 1.08000,
  "take_profit": 1.09000
}
```

**Request Schema**:
- `pair` (string, required): Currency pair
- `action` (string, required): "buy" or "sell"
- `volume` (number, required): Trade volume (> 0)
- `order_type` (string, optional): "market", "limit", "stop" (default: "market")
- `limit_price` (number, optional): Price for limit orders
- `stop_loss` (number, optional): Stop loss price
- `take_profit` (number, optional): Take profit price

**Response (200)**:
```json
{
  "trade_id": "uuid-string",
  "status": "executed",
  "execution_price": 1.08465,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "message": "Trade executed successfully",
  "slippage": 0.00005
}
```

**Error Response (400)**:
```json
{
  "detail": "Insufficient capital for trade"
}
```

#### GET /trades
**Description**: Get recent trade history
**Parameters**:
- `limit` (query, optional): Maximum number of trades (default: 50, max: 100)

**Response**:
```json
[
  {
    "id": "trade-uuid",
    "pair": "EUR/USD",
    "action": "buy",
    "volume": 0.5,
    "execution_price": 1.08465,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "pnl": 25.50,
    "status": "executed",
    "strategy": "manual"
  }
]
```

### 4. Position Management

#### GET /positions
**Description**: Get current open positions
**Response**:
```json
[
  {
    "id": "position-uuid",
    "pair": "EUR/USD",
    "action": "buy",
    "volume": 0.5,
    "entry_price": 1.08465,
    "current_price": 1.08520,
    "unrealized_pnl": 27.50,
    "realized_pnl": 0.0,
    "status": "open",
    "opened_at": "2024-01-15T10:30:00.000Z",
    "stop_loss": 1.08000,
    "take_profit": 1.09000,
    "strategy": "manual"
  }
]
```

### 5. Trading Signals

#### GET /signals/{pair}
**Description**: Get trading signals for a currency pair
**Parameters**:
- `pair` (path): Currency pair
- `strategy` (query, optional): "technical" or "ml" (default: "technical")

**Response**:
```json
[
  {
    "pair": "EUR/USD",
    "signal": "buy",
    "strength": 0.75,
    "price": 1.08465,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "strategy": "sma_crossover",
    "confidence": 0.82,
    "indicators": [
      {
        "indicator": "SMA_FAST",
        "value": 1.08450,
        "timestamp": "2024-01-15T10:30:00.000Z",
        "period": 10
      },
      {
        "indicator": "SMA_SLOW",
        "value": 1.08420,
        "timestamp": "2024-01-15T10:30:00.000Z",
        "period": 30
      }
    ]
  }
]
```

### 6. Backtesting

#### POST /backtest
**Description**: Run a strategy backtest on historical data
**Request Body**:
```json
{
  "pair": "EUR/USD",
  "start_date": "2024-01-01T00:00:00.000Z",
  "end_date": "2024-01-15T00:00:00.000Z",
  "strategy": "sma_crossover",
  "initial_capital": 10000.0,
  "parameters": {
    "sma_fast": 10,
    "sma_slow": 30,
    "stop_loss_pct": 0.02
  }
}
```

**Response**:
```json
{
  "pair": "EUR/USD",
  "start_date": "2024-01-01T00:00:00.000Z",
  "end_date": "2024-01-15T00:00:00.000Z",
  "strategy": "sma_crossover",
  "initial_capital": 10000.0,
  "final_capital": 10350.75,
  "total_return": 350.75,
  "total_return_percent": 3.51,
  "max_drawdown": 125.50,
  "max_drawdown_percent": 1.26,
  "sharpe_ratio": 1.85,
  "win_rate": 0.67,
  "total_trades": 24,
  "winning_trades": 16,
  "losing_trades": 8,
  "average_win": 45.30,
  "average_loss": -22.15,
  "profit_factor": 2.04,
  "trades": [
    {
      "id": "backtest-trade-1",
      "pair": "EUR/USD",
      "action": "buy",
      "volume": 0.5,
      "execution_price": 1.08465,
      "timestamp": "2024-01-02T14:30:00.000Z",
      "pnl": 25.50,
      "status": "executed"
    }
  ],
  "daily_returns": [
    {
      "date": "2024-01-02",
      "return": 0.0025,
      "capital": 10025.0
    }
  ]
}
```

### 7. Statistics & Analytics

#### GET /stats
**Description**: Get overall trading statistics
**Response**:
```json
{
  "total_trades": 156,
  "winning_trades": 98,
  "losing_trades": 58,
  "win_rate": 0.628,
  "total_pnl": 1250.75,
  "total_volume": 75.5,
  "average_trade_size": 0.484,
  "largest_win": 125.50,
  "largest_loss": -85.25,
  "current_positions": 3,
  "active_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
  "last_updated": "2024-01-15T10:30:00.000Z"
}
```

### 8. Strategy Management

#### POST /strategy/start/{pair}
**Description**: Start automated trading for a currency pair
**Parameters**:
- `pair` (path): Currency pair
- `strategy` (query, optional): Strategy type (default: "technical")

**Response**:
```json
{
  "status": "started",
  "pair": "EUR/USD",
  "strategy": "technical"
}
```

#### POST /strategy/stop/{pair}
**Description**: Stop automated trading for a currency pair
**Parameters**:
- `pair` (path): Currency pair

**Response**:
```json
{
  "status": "stopped",
  "pair": "EUR/USD"
}
```

## Data Models

### FXRate Model
```json
{
  "pair": "string (required)",
  "bid": "number (required)",
  "ask": "number (required)",
  "timestamp": "datetime (required)"
}
```

### TradeRequest Model
```json
{
  "pair": "string (required)",
  "action": "buy|sell (required)",
  "volume": "number > 0 (required)",
  "order_type": "market|limit|stop (optional)",
  "limit_price": "number (optional)",
  "stop_loss": "number (optional)",
  "take_profit": "number (optional)"
}
```

### TradeResponse Model
```json
{
  "trade_id": "string (required)",
  "status": "executed|pending|cancelled|failed (required)",
  "execution_price": "number (optional)",
  "timestamp": "datetime (required)",
  "message": "string (required)",
  "slippage": "number (optional)"
}
```

## Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (resource doesn't exist)
- **422**: Validation Error (Pydantic validation failed)
- **500**: Internal Server Error

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "volume"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

## Rate Limiting

### Current Implementation
- No rate limiting (development/hackathon)

### Production Recommendations
- **General API**: 1000 requests/minute per IP
- **Trading Endpoints**: 100 requests/minute per user
- **Market Data**: 500 requests/minute per IP
- **Streaming**: 10 concurrent connections per IP

## WebSocket API (Future Enhancement)

### Planned Endpoints
```
WS /ws/rates - Real-time rate updates
WS /ws/trades - Trade execution notifications
WS /ws/positions - Position updates
WS /ws/signals - Real-time trading signals
```

### Message Format
```json
{
  "type": "rate_update",
  "data": {
    "pair": "EUR/USD",
    "bid": 1.08450,
    "ask": 1.08470,
    "timestamp": "2024-01-15T10:30:00.000Z"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## SDK Examples

### Python Client Example
```python
import requests
import json

class AlphaFXClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_rates(self):
        response = requests.get(f"{self.base_url}/rates")
        return response.json()
    
    def execute_trade(self, pair, action, volume):
        trade_data = {
            "pair": pair,
            "action": action,
            "volume": volume
        }
        response = requests.post(
            f"{self.base_url}/trade", 
            json=trade_data
        )
        return response.json()
    
    def get_positions(self):
        response = requests.get(f"{self.base_url}/positions")
        return response.json()

# Usage
client = AlphaFXClient()
rates = client.get_rates()
result = client.execute_trade("EUR/USD", "buy", 0.5)
```

### JavaScript Client Example
```javascript
class AlphaFXClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getRates() {
        const response = await fetch(`${this.baseUrl}/rates`);
        return response.json();
    }
    
    async executeTrade(pair, action, volume) {
        const response = await fetch(`${this.baseUrl}/trade`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pair, action, volume })
        });
        return response.json();
    }
    
    async getPositions() {
        const response = await fetch(`${this.baseUrl}/positions`);
        return response.json();
    }
}

// Usage
const client = new AlphaFXClient();
const rates = await client.getRates();
const result = await client.executeTrade('EUR/USD', 'buy', 0.5);
```

## Testing

### Unit Tests
- Model validation tests
- Endpoint functionality tests
- Error handling tests
- Business logic tests

### Integration Tests
- End-to-end API workflows
- Database interaction tests
- Real-time data streaming tests

### Load Testing
- Concurrent request handling
- Database performance under load
- Memory usage monitoring

### Test Data
The API includes sample data generation for testing:
- Mock FX rates with realistic movements
- Sample trade history
- Demo strategies and signals
- Backtesting data

## API Versioning

### Current Strategy
- Single version (v1.0.0)
- Breaking changes require new version

### Future Versioning
- URL-based versioning: `/v2/rates`
- Header-based versioning: `Accept: application/vnd.alphafx.v2+json`
- Backward compatibility support

## Security Considerations

### Input Validation
- Pydantic models for request validation
- SQL injection prevention
- XSS protection
- Rate limiting

### Data Protection
- No sensitive data in logs
- Secure database connections
- Environment variable configuration
- HTTPS enforcement (production)

This API design provides a comprehensive, scalable foundation for the AlphaFX Trader platform while maintaining simplicity for demonstration and development purposes.