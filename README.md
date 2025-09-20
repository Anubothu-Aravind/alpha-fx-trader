# 📈 AlphaFX Trader

A comprehensive, hackathon-ready FX trading platform featuring real-time data streaming, automated trading strategies, machine learning predictions, and backtesting capabilities.

## 🚀 Features

### Backend (FastAPI)
- **Real-time FX Data**: Live currency exchange rates with mock data generation
- **Trading Engine**: Complete trade execution with position management
- **Technical Analysis**: SMA, EMA, RSI, MACD, Bollinger Bands strategies
- **Machine Learning**: ML-powered trading signal generation (simulated)
- **Backtesting**: Historical strategy performance analysis
- **Risk Management**: Stop loss, take profit, position sizing
- **REST API**: Comprehensive API with auto-generated documentation

### Frontend (React + TypeScript)
- **Live Dashboard**: Real-time FX rates and trading interface
- **Portfolio Management**: Position tracking and P&L monitoring
- **Trading Interface**: Execute trades with risk controls
- **Performance Analytics**: Trading statistics and metrics
- **Responsive Design**: Mobile-friendly interface

### Documentation
- **Architecture Guide**: Comprehensive system design
- **Database Schema**: Complete database documentation
- **API Documentation**: Detailed endpoint specifications
- **Trading Logic**: Strategy implementation details
- **Deployment Guide**: Production deployment instructions

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### 1. Backend Setup
```bash
# Clone repository
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader

# Install Python dependencies
cd app
pip install fastapi uvicorn sqlalchemy pydantic numpy aiohttp pandas

# Initialize database
python db_init.py --init

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 2. Frontend Setup
```bash
# Install Node.js dependencies
cd frontend
npm install

# Start development server
npm run dev
```

Frontend available at: http://localhost:3000

## 📊 Key Components

### Trading Strategies
- **SMA Crossover**: Moving average crossover signals
- **RSI Mean Reversion**: Overbought/oversold conditions
- **Bollinger Bands**: Price band breakout/reversion
- **MACD**: Momentum convergence/divergence
- **Multi-Indicator**: Combined signal approach
- **ML Strategy**: Machine learning predictions (simulated)

### Risk Management
- Position sizing based on capital and signal strength
- Dynamic stop loss and take profit levels
- Daily loss limits and exposure controls
- Portfolio correlation management

### Technical Indicators
- Simple/Exponential Moving Averages
- Relative Strength Index (RSI)
- MACD and signal lines
- Bollinger Bands with dynamic periods
- Average True Range (ATR)
- Stochastic Oscillator
- Williams %R

## 🗄️ Database Schema

### Core Tables
- **trades**: All executed trade transactions
- **positions**: Open and closed trading positions  
- **market_data**: Historical OHLCV data
- **strategies**: Strategy configurations
- **signals**: Generated trading signals
- **backtest_results**: Backtesting outcomes

## 🔌 API Endpoints

### Market Data
- `GET /rates` - Current FX rates
- `GET /rates/{pair}` - Specific pair rate
- `GET /rates/stream` - Real-time rate stream

### Trading
- `POST /trade` - Execute trade
- `GET /trades` - Trade history
- `GET /positions` - Open positions
- `GET /stats` - Trading statistics

### Analysis
- `GET /signals/{pair}` - Trading signals
- `POST /backtest` - Run strategy backtest
- `POST /strategy/start/{pair}` - Start auto trading
- `POST /strategy/stop/{pair}` - Stop auto trading

### System
- `GET /health` - System health check
- `GET /` - API status

## 🚀 Deployment

### Docker Deployment
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d
```

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions including:
- AWS/Azure cloud deployment
- Kubernetes configurations
- SSL/HTTPS setup
- Monitoring and logging
- Security considerations

## 📚 Documentation

- [System Architecture](docs/architecture.md) - Comprehensive system design
- [Database Design](docs/db_design.md) - Database schema and relationships
- [API Documentation](docs/api_design.md) - Complete API reference
- [Trading Logic](docs/trading_logic.md) - Strategy implementations
- [Deployment Guide](DEPLOYMENT.md) - Production deployment

## 🧪 Testing

### Backend Testing
```bash
cd app
pip install pytest pytest-asyncio httpx
pytest -v
```

### Frontend Testing  
```bash
cd frontend
npm test
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test rates endpoint
curl http://localhost:8000/rates

# Execute test trade
curl -X POST http://localhost:8000/trade \
  -H "Content-Type: application/json" \
  -d '{"pair":"EUR/USD","action":"buy","volume":0.1}'
```

## 🔒 Security Features

- Input validation on all endpoints
- SQL injection prevention
- XSS protection
- CORS configuration
- Environment variable protection
- Rate limiting (production)

## 📈 Performance

- Real-time data updates (2-second intervals)
- Efficient database indexing
- Async/await for concurrent operations
- Caching for frequent queries
- Optimized React rendering

## 🤝 Contributing

This is a hackathon-ready demonstration project. For production use:

1. Implement proper authentication
2. Add real FX data providers
3. Enhance risk management
4. Add comprehensive monitoring
5. Implement proper testing coverage

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🏆 Hackathon Features

This project is designed for hackathon demonstrations with:
- **Complete full-stack setup** in minutes
- **Live demo capabilities** with real-time updates
- **Professional UI/UX** for impressive presentations
- **Comprehensive documentation** for technical evaluation
- **Scalable architecture** for future development
- **Production-ready foundation** for continued development

Perfect for fintech hackathons, trading competitions, and educational demonstrations!