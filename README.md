# AlphaFX Trader

A real-time Forex trading application with algorithmic trading strategies, comprehensive risk management, and live market simulation.

![AlphaFX Trader Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![Node.js](https://img.shields.io/badge/Node.js-16%2B-green)
![React](https://img.shields.io/badge/React-18-blue)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🚀 Features

### Trading Algorithms
- **SMA Crossover Strategy**: Golden/Death cross signals with configurable periods
- **RSI Strategy**: Overbought/oversold signals with customizable thresholds  
- **Bollinger Bands Strategy**: Price band breakout detection
- **Combined Analysis**: Multi-algorithm signal aggregation with confidence weighting

### Risk Management
- **Daily Volume Limits**: Automatic trading halt at $10M volume
- **Position Sizing**: Dynamic position sizing based on signal confidence
- **Exposure Limits**: Maximum exposure per currency pair (20% of daily limit)
- **Trade Constraints**: Minimum trade value and maximum single trade limits

### Real-time Features
- **Live Price Feeds**: Simulated FX data for 6 major currency pairs
- **WebSocket Streaming**: Real-time price updates and trade notifications
- **Trade Blotter**: Live trade execution history
- **Position Monitoring**: Real-time P&L calculation and position tracking

### Backtesting
- **Historical Data Simulation**: Generate realistic OHLC data
- **Strategy Testing**: Test algorithms with historical data
- **Performance Analytics**: Win rate, total returns, and trade statistics

### User Interface
- **Modern Dashboard**: React-based responsive interface
- **Live Price Grid**: Real-time currency pair pricing with change indicators
- **Trading Controls**: Start/stop trading with volume monitoring
- **Position Management**: Open positions with P&L tracking

## 📊 Supported Currency Pairs

- EUR/USD (Euro/US Dollar)
- GBP/USD (British Pound/US Dollar)  
- USD/JPY (US Dollar/Japanese Yen)
- AUD/USD (Australian Dollar/US Dollar)
- USD/CAD (US Dollar/Canadian Dollar)
- USD/CHF (US Dollar/Swiss Franc)

## 🏗 Architecture

The application follows a modular architecture with clear separation of concerns:

- **Data Layer**: SQLite database with optimized schemas
- **Business Logic**: Trading algorithms and execution engine
- **API Layer**: RESTful endpoints with WebSocket support
- **Presentation Layer**: React SPA with real-time updates

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🚀 Quick Start

### Prerequisites
- Node.js 16.0.0 or higher
- npm 8.0.0 or higher

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader
```

2. **Install dependencies**
```bash
npm install
npm run install:client
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env file as needed
```

4. **Build and start**
```bash
npm run client:build
npm start
```

5. **Access the application**
Open your browser and navigate to `http://localhost:3001`

### Development Mode

For development with hot reloading:

```bash
# Terminal 1: Start server with auto-restart
npm run dev

# Terminal 2: Start React development server
npm run client
```

Access at `http://localhost:3000` (React dev server) or `http://localhost:3001` (full app).

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Server
PORT=3001
NODE_ENV=development

# Trading Parameters
MAX_TRADING_VOLUME=10000000    # $10M daily limit
DEFAULT_POSITION_SIZE=10000    # $10K base position
RISK_MANAGEMENT=true

# Algorithm Parameters
SMA_SHORT_PERIOD=10           # Short SMA period
SMA_LONG_PERIOD=50            # Long SMA period
RSI_PERIOD=14                 # RSI calculation period
RSI_OVERBOUGHT=70             # RSI overbought threshold
RSI_OVERSOLD=30               # RSI oversold threshold
BOLLINGER_PERIOD=20           # Bollinger bands period
BOLLINGER_STD_DEV=2           # Standard deviation multiplier

# Update Intervals
PRICE_UPDATE_INTERVAL=1000     # Price update frequency (ms)
ALGORITHM_UPDATE_INTERVAL=5000 # Signal calculation frequency (ms)
```

## 📖 API Documentation

The application provides a comprehensive REST API and WebSocket interface.

### Key Endpoints

- `GET /api/health` - Server health check
- `GET /api/prices` - Current FX prices
- `GET /api/trading/status` - Trading engine status
- `POST /api/trading/start` - Start automated trading
- `POST /api/trading/stop` - Stop automated trading
- `GET /api/trades` - Trade history
- `GET /api/positions` - Open positions
- `POST /api/backtest` - Run backtests

For complete API documentation, see [API.md](docs/API.md).

## 🤖 Trading Logic

The application implements a sophisticated multi-algorithm approach:

1. **Data Collection**: Real-time price data from FX simulator
2. **Signal Generation**: Multiple technical indicators generate signals
3. **Signal Aggregation**: Combined analysis with confidence weighting
4. **Risk Management**: Position sizing and exposure checks
5. **Trade Execution**: Automated trade execution with P&L tracking

For detailed trading logic, see [TRADING_LOGIC.md](docs/TRADING_LOGIC.md).

## 📊 Database Schema

### Core Tables

- **trades**: Trade execution history with P&L
- **positions**: Current open positions  
- **price_history**: Historical price data
- **algorithm_signals**: Generated trading signals
- **trading_stats**: Daily trading statistics

## 🧪 Testing

### Running Tests
```bash
npm test
```

### Manual Testing

1. **Start the application**
2. **Navigate to dashboard** at `http://localhost:3001`
3. **Click "Start Trading"** to begin automated trading
4. **Monitor live prices** in the price grid
5. **Watch trade executions** in the blotter
6. **Check positions** for P&L updates

### Backtesting

Test strategies with historical data:

```bash
curl -X POST http://localhost:3001/api/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "startDate": "2024-01-01",
    "endDate": "2024-01-31",
    "algorithm": "combined"
  }'
```

## 🚢 Production Deployment

### Docker Deployment

```bash
docker-compose up -d
```

### PM2 Process Manager

```bash
npm install -g pm2
pm2 start ecosystem.config.js --env production
pm2 save
```

### Reverse Proxy Setup

Configure nginx for production deployment with SSL termination.

For complete deployment guide, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

## 🔧 Development

### Project Structure

```
alpha-fx-trader/
├── server/                 # Node.js backend
│   ├── database/          # Database models and connection
│   ├── trading/           # Trading algorithms and engine
│   └── app.js             # Main server application
├── client/                # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   └── services/      # API and WebSocket services
│   └── public/
├── docs/                  # Documentation
├── config/                # Configuration files
└── data/                  # Database files (created automatically)
```

### Adding New Features

1. **New Trading Algorithm**: Add to `server/trading/TradingAlgorithms.js`
2. **New API Endpoint**: Add to `server/app.js`
3. **New UI Component**: Add to `client/src/components/`
4. **New Configuration**: Add to `.env` and update documentation

## 📚 Documentation

- [System Architecture](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Trading Logic Flow](docs/TRADING_LOGIC.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## ⚠️ Risk Disclaimer

This application is for educational and demonstration purposes. It uses simulated market data and should not be used for actual financial trading without proper risk management, regulatory compliance, and professional oversight.

**Key Points:**
- Uses simulated price data, not real market feeds
- No connection to actual brokers or exchanges  
- No real money at risk
- Algorithmic strategies may not perform as expected in real markets
- Past performance does not guarantee future results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Technical indicators implementation inspired by financial literature
- React components designed for optimal user experience
- WebSocket implementation for real-time data streaming
- SQLite for lightweight, embedded database storage

## 📞 Support

For questions or support:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the troubleshooting section in [DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

**Built with ❤️ for algorithmic trading education and demonstration.**