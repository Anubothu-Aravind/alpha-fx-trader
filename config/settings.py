import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/trades.db')
    
    # Trading settings
    MAX_TRADING_VOLUME = float(os.getenv('MAX_TRADING_VOLUME', '10000000'))  # $10M
    
    # API settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Forex API settings (using a mock service for demo)
    FOREX_API_URL = os.getenv('FOREX_API_URL', 'mock')
    FOREX_API_KEY = os.getenv('FOREX_API_KEY', '')
    
    # Trading pairs
    CURRENCY_PAIRS = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD']
    
    # Algorithm parameters
    SMA_SHORT_PERIOD = int(os.getenv('SMA_SHORT_PERIOD', '10'))
    SMA_LONG_PERIOD = int(os.getenv('SMA_LONG_PERIOD', '30'))
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    BOLLINGER_PERIOD = int(os.getenv('BOLLINGER_PERIOD', '20'))
    BOLLINGER_STD = int(os.getenv('BOLLINGER_STD', '2'))