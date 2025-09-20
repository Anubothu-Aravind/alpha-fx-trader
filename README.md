# AlphaFX Trader - Forex Trading Application

A comprehensive forex trading application that provides real-time data streaming, algorithmic trading, backtesting, and portfolio management capabilities.

## Features

### 🎯 Core Trading Features
- **Real-time Forex Data Streaming** - Live price feeds via WebSocket
- **Algorithmic Trading** - SMA crossover, RSI, and Bollinger Bands strategies
- **Manual Trading Interface** - User-controlled trade execution
- **Trade Blotter** - Complete trade history and analysis
- **Volume Limiting** - Automatic shutdown at $10M daily volume

### 📊 Technical Analysis
- **Simple Moving Average (SMA) Crossover** - 10/30 period crossover signals
- **Relative Strength Index (RSI)** - Momentum-based overbought/oversold detection
- **Bollinger Bands** - Volatility-based breakout/reversion signals
- **Multi-Algorithm Consensus** - Combined signal generation from all algorithms

### 📈 Analytics & Backtesting
- **Historical Backtesting** - Strategy performance validation
- **Performance Metrics** - Win rate, drawdown, and P&L analysis
- **Real-time Charts** - Price visualization with technical indicators
- **Trading Statistics** - Live dashboard with key metrics

### 🔧 Technical Highlights
- **WebSocket Real-time Updates** - Sub-second price and trade updates
- **Local Data Storage** - SQLite database for trade history
- **Responsive Web UI** - Modern, mobile-friendly interface
- **Risk Management** - Built-in volume limits and safety controls

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 run.py
```

### Access the Application
- **Web Interface**: http://localhost:5000
- **Trading Dashboard**: Live prices, charts, and trade execution
- **Auto Trading**: Start/stop algorithmic trading with one click

## Currency Pairs Supported
- EUR/USD (Euro/US Dollar)
- GBP/USD (British Pound/US Dollar)  
- USD/JPY (US Dollar/Japanese Yen)
- USD/CHF (US Dollar/Swiss Franc)
- AUD/USD (Australian Dollar/US Dollar)
- USD/CAD (US Dollar/Canadian Dollar)

## Architecture

### Backend (Python)
- **Flask** - Web framework and REST API
- **Flask-SocketIO** - WebSocket real-time communication
- **SQLAlchemy** - Database ORM
- **SQLite** - Local database storage
- **pandas/numpy** - Financial calculations

### Frontend (JavaScript)
- **HTML5/CSS3** - Modern responsive interface
- **Chart.js** - Real-time price charts
- **WebSocket** - Live data updates
- **Vanilla JavaScript** - No framework dependencies

## Trading Algorithms

### 1. SMA Crossover Strategy
```
BUY Signal:  Short SMA (10) crosses above Long SMA (30)
SELL Signal: Short SMA (10) crosses below Long SMA (30)
```

### 2. RSI Strategy
```
BUY Signal:  RSI ≤ 30 (Oversold)
SELL Signal: RSI ≥ 70 (Overbought)
```

### 3. Bollinger Bands Strategy
```
BUY Signal:  Price touches lower band
SELL Signal: Price touches upper band
```

### Consensus Algorithm
Trades are executed only when **2 or more algorithms agree** on the signal direction.

## Risk Management

- **Daily Volume Limit**: $10,000,000 maximum trading volume
- **Automatic Shutdown**: Trading stops when volume limit is reached
- **Position Sizing**: Fixed 1000 units per trade (configurable)
- **Real-time Monitoring**: Live tracking of exposure and limits

## API Endpoints

### Trading
- `POST /api/trade` - Execute manual trade
- `GET /api/trades` - Get trade history
- `POST /api/trading/start` - Start auto trading
- `POST /api/trading/stop` - Stop auto trading

### Data
- `GET /api/prices` - Current prices for all pairs
- `GET /api/prices/{pair}` - Current price for specific pair
- `GET /api/historical/{pair}` - Historical price data

### Analysis
- `GET /api/algorithms/signals/{pair}` - Current algorithm signals
- `POST /api/backtest` - Run backtesting analysis

## Documentation

- **[System Architecture](docs/architecture.md)** - Technical architecture overview
- **[API Design](docs/api-design.md)** - Complete API reference
- **[Trading Logic](docs/trading-logic.md)** - Algorithm implementation details
- **[Deployment Guide](docs/deployment.md)** - Installation and deployment instructions

## Screenshots

### Trading Dashboard
![Dashboard showing live prices, trading statistics, and controls]

### Price Charts with Indicators
![Real-time price charts with SMA, RSI, and Bollinger Bands]

### Trade Blotter
![Complete trade history with filtering and sorting]

### Backtesting Results
![Historical strategy performance analysis]

## Development

### Project Structure
```
alpha-fx-trader/
├── backend/          # Python Flask application
├── frontend/         # HTML/CSS/JavaScript interface
├── data/            # SQLite database storage
├── docs/            # Technical documentation
├── config/          # Configuration settings
└── tests/           # Test files (future)
```

### Configuration
Key settings can be customized in `config/settings.py`:
- Trading volume limits
- Algorithm parameters (SMA periods, RSI thresholds)
- Currency pairs to trade
- Risk management settings

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and demonstration purposes only. It uses simulated forex data and should not be used for actual trading without proper risk assessment and regulatory compliance. Trading forex involves substantial risk of loss and is not suitable for all investors.

## Support

For questions, issues, or feature requests, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for the trading community**