# AlphaFX Trader - API Design

## Base URL
```
http://localhost:3001/api
```

## Authentication
Currently, the API does not require authentication. In a production environment, consider implementing JWT tokens or API keys.

## Response Format
All API responses follow this structure:
```json
{
  "data": {},      // Response data (varies by endpoint)
  "error": "...",  // Error message (only present on errors)
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

## Endpoints

### Health Check
```http
GET /api/health
```
Returns server health status and version information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "version": "1.0.0"
}
```

### Trading Control

#### Get Trading Status
```http
GET /api/trading/status
```
Returns current trading engine status and volume information.

**Response:**
```json
{
  "isActive": false,
  "dailyVolume": 0,
  "maxDailyVolume": 10000000,
  "volumeExceeded": false
}
```

#### Start Trading
```http
POST /api/trading/start
```
Starts the automated trading engine.

**Response:**
```json
{
  "message": "Trading started",
  "status": "active"
}
```

#### Stop Trading
```http
POST /api/trading/stop
```
Stops the automated trading engine.

**Response:**
```json
{
  "message": "Trading stopped",
  "status": "inactive"
}
```

### Price Data

#### Get All Prices
```http
GET /api/prices
```
Returns current prices for all currency pairs.

**Response:**
```json
{
  "EURUSD": {
    "bid": 1.0850,
    "ask": 1.0852,
    "timestamp": "2025-01-01T00:00:00.000Z",
    "volume": 1000000,
    "change": 0.0002,
    "changePercent": 0.0185
  },
  "GBPUSD": {
    "bid": 1.2650,
    "ask": 1.2652,
    "timestamp": "2025-01-01T00:00:00.000Z",
    "volume": 850000,
    "change": -0.0001,
    "changePercent": -0.0079
  }
}
```

#### Get Price for Symbol
```http
GET /api/prices/{symbol}
```
Returns current price for a specific currency pair.

**Parameters:**
- `symbol` (path): Currency pair symbol (e.g., EURUSD)

**Response:**
```json
{
  "bid": 1.0850,
  "ask": 1.0852,
  "timestamp": "2025-01-01T00:00:00.000Z",
  "volume": 1000000,
  "change": 0.0002,
  "changePercent": 0.0185
}
```

### Trading Signals

#### Get Signals for Symbol
```http
GET /api/signals/{symbol}
```
Returns current trading signals for a currency pair.

**Parameters:**
- `symbol` (path): Currency pair symbol

**Response:**
```json
{
  "signal": "buy",
  "confidence": 0.75,
  "reason": "combined_analysis",
  "components": {
    "sma": {
      "signal": "buy",
      "confidence": 0.8,
      "reason": "golden_cross",
      "shortSMA": 1.0851,
      "longSMA": 1.0849
    },
    "rsi": {
      "signal": "hold",
      "confidence": 0,
      "reason": "neutral",
      "rsi": 45.2
    },
    "bb": {
      "signal": "buy",
      "confidence": 0.7,
      "reason": "below_lower_band"
    }
  }
}
```

### Trades

#### Get Trades
```http
GET /api/trades?symbol={symbol}&limit={limit}&offset={offset}
```
Returns trade history with optional filtering and pagination.

**Query Parameters:**
- `symbol` (optional): Filter by currency pair
- `limit` (optional): Number of trades to return (default: 100, max: 1000)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2025-01-01T00:00:00.000Z",
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 10000,
    "price": 1.0851,
    "value": 10851.00,
    "algorithm": "combined",
    "status": "executed",
    "pnl": 25.50
  }
]
```

### Positions

#### Get All Positions
```http
GET /api/positions
```
Returns all open positions.

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "EURUSD",
    "quantity": 10000,
    "avg_price": 1.0851,
    "total_value": 10851.00,
    "pnl": 25.50,
    "updated_at": "2025-01-01T00:00:00.000Z"
  }
]
```

### Statistics

#### Get Trading Statistics
```http
GET /api/stats
```
Returns daily trading statistics.

**Response:**
```json
{
  "date": "2025-01-01",
  "total_volume": 50000.00,
  "total_trades": 5,
  "total_pnl": 125.75,
  "active_positions": 3,
  "updated_at": "2025-01-01T00:00:00.000Z"
}
```

### Historical Data

#### Get Historical Data
```http
GET /api/historical/{symbol}?startDate={start}&endDate={end}&interval={interval}
```
Returns historical OHLC data for backtesting.

**Parameters:**
- `symbol` (path): Currency pair symbol
- `startDate` (query): Start date (ISO 8601 format)
- `endDate` (query): End date (ISO 8601 format)
- `interval` (query): Data interval (1min, 5min, 15min, 30min, 1hour, 4hour, 1day)

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00.000Z",
    "symbol": "EURUSD",
    "open": 1.0850,
    "high": 1.0855,
    "low": 1.0848,
    "close": 1.0852,
    "volume": 1000000
  }
]
```

### Backtesting

#### Run Backtest
```http
POST /api/backtest
```
Executes a backtest with specified parameters.

**Request Body:**
```json
{
  "symbol": "EURUSD",
  "startDate": "2025-01-01",
  "endDate": "2025-01-31",
  "algorithm": "combined",
  "parameters": {
    "smaShort": 10,
    "smaLong": 50,
    "rsiPeriod": 14,
    "rsiOverbought": 70,
    "rsiOversold": 30
  }
}
```

**Response:**
```json
{
  "symbol": "EURUSD",
  "startDate": "2025-01-01",
  "endDate": "2025-01-31",
  "algorithm": "combined",
  "trades": [...],
  "stats": {
    "totalTrades": 25,
    "profitableTrades": 15,
    "winRate": 60.0,
    "totalPnL": 1250.75,
    "startingBalance": 100000,
    "finalBalance": 101250.75,
    "returnPercent": 1.25
  }
}
```

## WebSocket Events

The application provides real-time updates via WebSocket connection at the same base URL.

### Connection
```javascript
const ws = new WebSocket('ws://localhost:3001');
```

### Events

#### Price Updates
```json
{
  "type": "priceUpdate",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0850,
    "ask": 1.0852,
    "timestamp": "2025-01-01T00:00:00.000Z"
  }
}
```

#### Trade Executed
```json
{
  "type": "tradeExecuted",
  "data": {
    "id": "uuid",
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 10000,
    "price": 1.0851,
    "value": 10851.00,
    "algorithm": "combined"
  }
}
```

#### Initial Prices
```json
{
  "type": "prices",
  "data": {
    "EURUSD": {...},
    "GBPUSD": {...}
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (invalid endpoint or resource)
- `500`: Internal Server Error

Error responses include a descriptive message:
```json
{
  "error": "Symbol not found"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting based on IP address or API key.