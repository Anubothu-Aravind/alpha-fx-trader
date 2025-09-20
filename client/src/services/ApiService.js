const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  static async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  static async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Health check
  static async getHealth() {
    return this.get('/health');
  }

  // Trading endpoints
  static async getTradingStatus() {
    return this.get('/trading/status');
  }

  static async startTrading() {
    return this.post('/trading/start');
  }

  static async stopTrading() {
    return this.post('/trading/stop');
  }

  // Price endpoints
  static async getPrices() {
    return this.get('/prices');
  }

  static async getPrice(symbol) {
    return this.get(`/prices/${symbol}`);
  }

  // Signal endpoints
  static async getSignals(symbol) {
    return this.get(`/signals/${symbol}`);
  }

  // Trade endpoints
  static async getTrades(symbol = null, limit = 100, offset = 0) {
    let endpoint = `/trades?limit=${limit}&offset=${offset}`;
    if (symbol) {
      endpoint += `&symbol=${symbol}`;
    }
    return this.get(endpoint);
  }

  static async getTrade(id) {
    return this.get(`/trades/${id}`);
  }

  // Position endpoints
  static async getPositions() {
    return this.get('/positions');
  }

  static async getPosition(symbol) {
    return this.get(`/positions/${symbol}`);
  }

  // Statistics endpoints
  static async getStats() {
    return this.get('/stats');
  }

  // Historical data endpoints
  static async getHistoricalData(symbol, startDate, endDate, interval = '1hour') {
    const params = new URLSearchParams({
      startDate,
      endDate,
      interval,
    });
    return this.get(`/historical/${symbol}?${params}`);
  }

  // Backtesting endpoints
  static async runBacktest(params) {
    return this.post('/backtest', params);
  }

  // Utility methods
  static formatCurrency(value, currency = 'USD', decimals = 2) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }

  static formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }

  static formatPercent(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value / 100);
  }

  static formatDateTime(timestamp) {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date(timestamp));
  }

  static formatTime(timestamp) {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(new Date(timestamp));
  }
}

export { ApiService };