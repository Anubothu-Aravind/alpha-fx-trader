# Database Schema Design

## Overview

The AlphaFX Trader database is designed to efficiently store and manage trading data, market information, and system configurations. The schema uses SQLite for development and is compatible with PostgreSQL for production scaling.

## Database Architecture

### Design Principles

1. **Normalization**: Proper table relationships to avoid data redundancy
2. **Indexing**: Strategic indexes for query performance
3. **Constraints**: Data integrity through foreign keys and checks
4. **Timestamps**: Automatic tracking of record creation/updates
5. **Scalability**: Design supports future horizontal scaling

## Core Tables

### 1. trades

**Purpose**: Store all executed trade transactions

```sql
CREATE TABLE trades (
    id VARCHAR PRIMARY KEY,
    pair VARCHAR NOT NULL,
    action VARCHAR NOT NULL,      -- 'buy' or 'sell'
    volume FLOAT NOT NULL,
    order_type VARCHAR DEFAULT 'market',
    requested_price FLOAT,
    execution_price FLOAT NOT NULL,
    slippage FLOAT,
    status VARCHAR DEFAULT 'executed',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pnl FLOAT DEFAULT 0.0,
    commission FLOAT DEFAULT 0.0,
    strategy VARCHAR,
    notes TEXT,
    position_id VARCHAR,
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

-- Indexes for performance
CREATE INDEX idx_trades_pair ON trades(pair);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_strategy ON trades(strategy);
```

**Key Fields Explained:**
- `id`: UUID for unique identification
- `pair`: Currency pair (e.g., "EUR/USD")
- `action`: Trade direction (buy/sell)
- `execution_price`: Actual price at execution
- `slippage`: Difference from requested price
- `pnl`: Profit/Loss for this trade
- `position_id`: Links to related position

### 2. positions

**Purpose**: Track open and closed trading positions

```sql
CREATE TABLE positions (
    id VARCHAR PRIMARY KEY,
    pair VARCHAR NOT NULL,
    action VARCHAR NOT NULL,      -- 'buy' or 'sell'
    volume FLOAT NOT NULL,
    entry_price FLOAT NOT NULL,
    current_price FLOAT NOT NULL,
    unrealized_pnl FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    status VARCHAR DEFAULT 'open', -- 'open' or 'closed'
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    stop_loss FLOAT,
    take_profit FLOAT,
    strategy VARCHAR
);

-- Indexes
CREATE INDEX idx_positions_pair ON positions(pair);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_opened_at ON positions(opened_at);
```

**Key Relationships:**
- One position can have multiple trades (via foreign key)
- Position lifecycle: open → closed
- Real-time PnL calculation based on current market price

### 3. market_data

**Purpose**: Store historical OHLCV market data

```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair VARCHAR NOT NULL,
    timestamp DATETIME NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT DEFAULT 0.0
);

-- Composite index for efficient queries
CREATE UNIQUE INDEX idx_market_data_pair_time ON market_data(pair, timestamp);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
```

**Data Granularity:**
- Hourly candles for backtesting
- Daily candles for long-term analysis
- Minute candles for short-term strategies

### 4. strategies

**Purpose**: Configuration and performance tracking for trading strategies

```sql
CREATE TABLE strategies (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    pair VARCHAR NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    parameters TEXT,              -- JSON string
    risk_parameters TEXT,         -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    performance_stats TEXT        -- JSON string
);

-- Indexes
CREATE INDEX idx_strategies_pair ON strategies(pair);
CREATE INDEX idx_strategies_enabled ON strategies(enabled);
```

**JSON Fields Structure:**

**parameters** example:
```json
{
  "sma_fast": 10,
  "sma_slow": 30,
  "rsi_period": 14,
  "rsi_overbought": 70,
  "rsi_oversold": 30
}
```

**risk_parameters** example:
```json
{
  "max_position_size": 1.0,
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.04,
  "max_daily_loss": 500.0
}
```

### 5. signals

**Purpose**: Store generated trading signals from strategies

```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair VARCHAR NOT NULL,
    signal VARCHAR NOT NULL,       -- 'buy', 'sell', 'hold'
    strength FLOAT NOT NULL,
    price FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    strategy VARCHAR NOT NULL,
    confidence FLOAT,
    indicators TEXT,               -- JSON string
    executed BOOLEAN DEFAULT FALSE
);

-- Indexes
CREATE INDEX idx_signals_pair ON signals(pair);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_strategy ON signals(strategy);
CREATE INDEX idx_signals_executed ON signals(executed);
```

**indicators** JSON example:
```json
{
  "sma_10": 1.0850,
  "sma_30": 1.0820,
  "rsi": 65.5,
  "macd": 0.0025,
  "bb_upper": 1.0875,
  "bb_lower": 1.0825
}
```

### 6. backtest_results

**Purpose**: Store backtesting results and analysis

```sql
CREATE TABLE backtest_results (
    id VARCHAR PRIMARY KEY,
    pair VARCHAR NOT NULL,
    strategy VARCHAR NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    initial_capital FLOAT NOT NULL,
    final_capital FLOAT NOT NULL,
    total_return FLOAT NOT NULL,
    max_drawdown FLOAT,
    sharpe_ratio FLOAT,
    win_rate FLOAT,
    total_trades INTEGER,
    parameters TEXT,              -- JSON string
    results_data TEXT,            -- JSON string
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_backtest_pair ON backtest_results(pair);
CREATE INDEX idx_backtest_strategy ON backtest_results(strategy);
CREATE INDEX idx_backtest_created ON backtest_results(created_at);
```

## Entity Relationships

```
positions (1) ←→ (N) trades
    ↓
strategies (1) ←→ (N) signals
    ↓
market_data (N) ←→ (1) pair
    ↓
backtest_results (N) ←→ (1) strategy
```

### Relationship Details:

1. **Position ↔ Trade**: One position can have multiple trades (entry and exit)
2. **Strategy ↔ Signal**: Each strategy generates multiple signals over time
3. **Strategy ↔ Backtest**: Multiple backtest runs per strategy
4. **Pair Reference**: All tables reference currency pairs as strings

## Data Integrity Constraints

### Primary Key Constraints
- All tables have unique primary keys
- UUIDs used for business entities (trades, positions, strategies)
- Auto-increment integers for system entities (market_data, signals)

### Foreign Key Constraints
- `trades.position_id` → `positions.id`
- Cascade deletes for data consistency
- NULL allowed for optional relationships

### Check Constraints
```sql
-- Volume must be positive
ALTER TABLE trades ADD CONSTRAINT chk_trades_volume 
CHECK (volume > 0);

-- Action must be valid
ALTER TABLE trades ADD CONSTRAINT chk_trades_action 
CHECK (action IN ('buy', 'sell'));

-- Status must be valid
ALTER TABLE positions ADD CONSTRAINT chk_positions_status 
CHECK (status IN ('open', 'closed'));

-- OHLC data integrity
ALTER TABLE market_data ADD CONSTRAINT chk_market_data_ohlc 
CHECK (high >= low AND high >= open AND high >= close AND low <= open AND low <= close);
```

## Performance Optimization

### Indexing Strategy

1. **Primary Access Patterns**:
   - Trade history by pair and date
   - Open positions by pair
   - Market data by pair and time range
   - Signals by strategy and timestamp

2. **Composite Indexes**:
   - `(pair, timestamp)` for time-series queries
   - `(strategy, pair)` for strategy-specific queries
   - `(status, pair)` for position filtering

3. **Covering Indexes**: Include frequently accessed columns

### Query Optimization

**Common Query Patterns:**

1. **Recent Trades**:
```sql
SELECT * FROM trades 
WHERE pair = ? AND timestamp >= ? 
ORDER BY timestamp DESC 
LIMIT ?;
```

2. **Open Positions**:
```sql
SELECT * FROM positions 
WHERE status = 'open' AND pair = ?;
```

3. **Market Data Range**:
```sql
SELECT * FROM market_data 
WHERE pair = ? AND timestamp BETWEEN ? AND ? 
ORDER BY timestamp;
```

## Data Retention Policy

### Retention Rules:
- **Trades**: Keep indefinitely (audit trail)
- **Positions**: Keep indefinitely (regulatory compliance)
- **Market Data**: Keep 2 years (storage optimization)
- **Signals**: Keep 3 months (performance analysis)
- **Backtest Results**: Keep 1 year (historical analysis)

### Archival Strategy:
- Partition tables by date ranges
- Archive old market_data to separate tables
- Implement soft deletes for important records

## Security Considerations

### Data Protection:
- No sensitive personal data stored
- Account balances encrypted at rest
- Audit logs for all data modifications
- Role-based access control

### Backup Strategy:
- Daily full database backups
- Transaction log backups every 15 minutes
- Point-in-time recovery capability
- Cross-region backup replication

## Migration Strategy

### Schema Evolution:
- Version-controlled migration scripts
- Backward-compatible changes
- Testing on production replica
- Rollback procedures

### Sample Migration:
```sql
-- Migration: Add commission tracking
ALTER TABLE trades ADD COLUMN commission_rate FLOAT DEFAULT 0.0002;
UPDATE trades SET commission_rate = 0.0002 WHERE commission_rate IS NULL;

-- Create index for new column
CREATE INDEX idx_trades_commission ON trades(commission_rate);
```

## Monitoring and Maintenance

### Performance Monitoring:
- Query execution time tracking
- Index usage statistics
- Table size monitoring
- Connection pool metrics

### Maintenance Tasks:
- Regular VACUUM operations (SQLite)
- Index rebuilding schedules
- Statistics updates
- Deadlock monitoring

## Production Considerations

### PostgreSQL Migration:
```sql
-- Enhanced constraints for production
ALTER TABLE trades ADD CONSTRAINT chk_execution_price_positive 
CHECK (execution_price > 0);

-- Partitioning for large tables
CREATE TABLE trades_2024 PARTITION OF trades 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Advanced indexing
CREATE INDEX CONCURRENTLY idx_trades_pair_timestamp_desc 
ON trades (pair, timestamp DESC);
```

### Scaling Considerations:
- Read replicas for reporting
- Horizontal partitioning by pair
- Caching layer (Redis)
- Connection pooling
- Query result caching

This database design provides a solid foundation for the AlphaFX Trader system, balancing performance, integrity, and scalability requirements.