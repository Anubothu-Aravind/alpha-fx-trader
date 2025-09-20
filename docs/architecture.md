# AlphaFX Trader System Architecture

## Overview

AlphaFX Trader is a comprehensive, hackathon-ready FX trading platform featuring real-time data streaming, automated trading strategies, machine learning predictions, and backtesting capabilities. The system is designed with a modern microservices architecture for scalability and maintainability.

## High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   External      │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   Data Sources  │
│                 │    │                  │    │   (APIs/Mock)   │
│  - Dashboard    │    │  - REST API      │    │                 │
│  - Trading UI   │    │  - WebSocket     │    │  - FX Rates     │
│  - Charts       │    │  - Trading Engine│    │  - News Feeds   │
│  - Analytics    │    │  - ML Strategy   │    │  - Market Data  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌─────────▼─────────┐              │
         │              │    Database       │              │
         └──────────────►│   (SQLite)       │◄─────────────┘
                        │                   │
                        │  - Trades         │
                        │  - Positions      │
                        │  - Market Data    │
                        │  - Strategies     │
                        │  - Backtest Results│
                        └───────────────────┘
```

## Component Architecture

### 1. Frontend Layer (React + TypeScript)

**Technology Stack:**
- React 18 with TypeScript
- Vite for build tooling
- Axios for HTTP requests
- CSS3 with custom styling
- Real-time updates via polling

**Key Components:**
- **Dashboard**: Main trading interface
- **Rate Display**: Live FX rate visualization
- **Trading Form**: Trade execution interface
- **Portfolio View**: Positions and P&L tracking
- **Statistics Panel**: Performance metrics

**Features:**
- Real-time rate updates (2-second polling)
- Interactive trade execution
- Portfolio monitoring
- Responsive design
- Error handling and user feedback

### 2. Backend Layer (FastAPI + Python)

**Technology Stack:**
- FastAPI for REST API
- SQLAlchemy for ORM
- SQLite for development database
- Pydantic for data validation
- AsyncIO for concurrent operations
- NumPy/Pandas for calculations

**Core Services:**

#### 2.1 API Gateway (`main.py`)
- RESTful endpoints for all operations
- Authentication and authorization
- Request/response validation
- CORS handling for frontend
- Health monitoring
- Auto-generated OpenAPI documentation

**Key Endpoints:**
```
GET  /health              - System health check
GET  /rates               - Current FX rates
GET  /rates/stream        - Real-time rate stream
POST /trade               - Execute trade
GET  /trades              - Trade history
GET  /positions           - Open positions
GET  /signals/{pair}      - Trading signals
POST /backtest            - Run backtest
GET  /stats               - Trading statistics
```

#### 2.2 Data Feeder (`data_feeder.py`)
- Real-time FX data acquisition
- Mock data generation for demo
- Rate caching and distribution
- Market event simulation
- Multiple data source support

**Features:**
- Configurable update intervals
- Realistic price movements
- Spread simulation
- Volatility modeling
- Market hours simulation

#### 2.3 Trading Engine (`trading_engine.py`)
- Core trade execution logic
- Position management
- Risk management
- Automated trading strategies
- Order management

**Key Features:**
- Multiple trading strategies (SMA, RSI, Bollinger Bands)
- Risk parameters (stop loss, take profit)
- Position sizing
- Slippage simulation
- Commission calculation
- Real-time P&L updates

#### 2.4 ML Strategy (`ml_strategy.py`)
- Machine learning prediction engine
- Feature engineering
- Model training simulation
- Prediction caching
- Performance tracking

**Supported Models:**
- LSTM (simulated)
- Random Forest (simulated)
- Transformer (simulated)
- Feature importance analysis

#### 2.5 Backtesting Engine (`backtester.py`)
- Historical strategy testing
- Performance metrics calculation
- Trade simulation
- Risk analysis
- Report generation

**Metrics Calculated:**
- Total return and percentage
- Sharpe ratio
- Maximum drawdown
- Win rate
- Profit factor
- Average win/loss

#### 2.6 Technical Analysis (`utils.py`)
- Technical indicator calculations
- Signal generation
- Pattern recognition
- Market analysis tools

**Supported Indicators:**
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI)
- MACD
- Bollinger Bands
- Stochastic Oscillator
- Average True Range (ATR)
- Williams %R

### 3. Database Layer (SQLite)

**Schema Design:**

#### Tables:
1. **trades** - All executed trades
2. **positions** - Open and closed positions
3. **market_data** - Historical OHLCV data
4. **strategies** - Strategy configurations
5. **signals** - Generated trading signals
6. **backtest_results** - Backtesting outcomes

**Key Features:**
- ACID compliance
- Relationship integrity
- Index optimization
- Automatic timestamps
- JSON field support for flexible data

### 4. Data Flow Architecture

```
External APIs → Data Feeder → Rate Cache → WebSocket/REST → Frontend
     ↓              ↓             ↓            ↓
Historical DB ← Trading Engine ← Signals ← Strategy Engine
     ↓              ↓
Backtester ← Performance Analytics
```

## Strategy Framework

### 1. Technical Analysis Strategies
- **SMA Crossover**: Fast/slow moving average crossovers
- **RSI Mean Reversion**: Overbought/oversold signals
- **Bollinger Bands**: Price band breakouts
- **MACD**: Moving average convergence divergence
- **Multi-Indicator**: Combined signal approach

### 2. Machine Learning Strategies
- **Feature Engineering**: Price, volume, technical indicators
- **Model Training**: Supervised learning approach
- **Prediction Generation**: Real-time inference
- **Performance Tracking**: Accuracy monitoring

### 3. Risk Management
- **Position Sizing**: Capital-based allocation
- **Stop Loss/Take Profit**: Automatic exit rules
- **Daily Loss Limits**: Risk control
- **Correlation Management**: Portfolio diversification

## Real-time Data Pipeline

```
Market Data Source
       ↓
Data Normalization
       ↓
Rate Calculation (Bid/Ask/Spread)
       ↓
Price Change Detection
       ↓
Rate Cache Update
       ↓
Client Notification (WebSocket/HTTP)
       ↓
Frontend Update
```

## Deployment Architecture

### Development Environment
- Local SQLite database
- Mock data generation
- Hot reloading for frontend
- FastAPI auto-reload

### Production Considerations
- PostgreSQL/MySQL database
- Redis for caching
- Load balancer
- Container orchestration
- Monitoring and logging
- Backup strategies

## Security Architecture

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control
- API rate limiting
- Input validation
- SQL injection prevention

### Data Protection
- Database encryption
- Secure communication (HTTPS)
- Environment variable management
- Audit logging
- PII protection

## Monitoring & Observability

### Key Metrics
- Trade execution latency
- Data feed reliability
- Strategy performance
- System resource usage
- Error rates

### Logging Strategy
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARN, ERROR)
- Centralized log aggregation
- Performance monitoring
- Alert systems

## Scalability Considerations

### Horizontal Scaling
- Microservice decomposition
- Database sharding
- Caching layers
- Message queues
- Load balancing

### Performance Optimization
- Database indexing
- Query optimization
- Caching strategies
- Asynchronous processing
- Connection pooling

## Technology Choices Rationale

### Frontend: React + TypeScript
- **Pros**: Modern, component-based, type safety, large ecosystem
- **Use Case**: Interactive dashboards, real-time updates

### Backend: FastAPI + Python
- **Pros**: High performance, automatic API docs, async support
- **Use Case**: REST APIs, data processing, ML integration

### Database: SQLite (Dev) / PostgreSQL (Prod)
- **Pros**: Embedded (SQLite), ACID compliance, SQL support
- **Use Case**: Transactional data, relationships, querying

### Real-time: HTTP Polling (WebSocket for production)
- **Pros**: Simple implementation, reliable
- **Use Case**: Live data updates, trade notifications

## Future Enhancements

### Phase 2 Features
- WebSocket implementation
- Advanced charting (TradingView integration)
- Portfolio optimization
- News sentiment analysis
- Social trading features

### Phase 3 Features
- Multi-asset support (Crypto, Stocks, Commodities)
- Advanced ML models (Deep Learning)
- Cloud deployment (AWS/Azure)
- Mobile application
- Regulatory compliance features

This architecture provides a solid foundation for a professional FX trading platform while maintaining simplicity for hackathon demonstration purposes.