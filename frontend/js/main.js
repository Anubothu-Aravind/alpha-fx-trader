// Main application logic - Simplified version
class AlphaFxApp {
    constructor() {
        this.isAutoTradingEnabled = false;
        this.tradingStats = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startDataRefresh();
    }
    
    setupEventListeners() {
        // Auto trading toggle
        const toggleTradingBtn = document.getElementById('toggle-trading');
        toggleTradingBtn.addEventListener('click', () => this.toggleAutoTrading());
        
        // Manual trade form
        const tradeForm = document.getElementById('trade-form');
        tradeForm.addEventListener('submit', (e) => this.handleManualTrade(e));
        
        // Refresh trades button
        const refreshTradesBtn = document.getElementById('refresh-trades');
        refreshTradesBtn.addEventListener('click', () => this.loadTrades());
        
        // Backtest form
        const backtestForm = document.getElementById('backtest-form');
        backtestForm.addEventListener('submit', (e) => this.runBacktest(e));
        
        // Chart controls
        const chartPairSelect = document.getElementById('chart-pair');
        chartPairSelect.addEventListener('change', (e) => this.updateChart(e.target.value));
        
        const refreshChartBtn = document.getElementById('refresh-chart');
        refreshChartBtn.addEventListener('click', () => this.updateChart(chartPairSelect.value));
        
        // Update connection status
        this.updateConnectionStatus('connected');
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `status-indicator ${status}`;
            statusElement.textContent = status === 'connected' ? 'Connected' : 'Disconnected';
        }
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadPrices(),
                this.loadTrades(),
                this.loadTradingStatus(),
                this.updateChart('EUR/USD')
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
    
    startDataRefresh() {
        // Refresh prices every 3 seconds
        setInterval(() => {
            this.loadPrices();
        }, 3000);
        
        // Refresh trading status every 10 seconds
        setInterval(() => {
            this.loadTradingStatus();
        }, 10000);
        
        // Refresh trades every 30 seconds
        setInterval(() => {
            this.loadTrades();
        }, 30000);
    }
    
    async loadPrices() {
        try {
            const response = await fetch('/api/prices');
            if (!response.ok) throw new Error('Failed to load prices');
            
            const prices = await response.json();
            this.displayPrices(prices);
            
        } catch (error) {
            console.error('Error loading prices:', error);
            this.showNotification('Failed to load prices', 'error');
        }
    }
    
    displayPrices(prices) {
        const priceGrid = document.getElementById('price-grid');
        if (!priceGrid) return;
        
        // Store old prices for change calculation
        const oldPrices = {};
        priceGrid.querySelectorAll('.price-card').forEach(card => {
            const pair = card.dataset.pair;
            const priceElement = card.querySelector('.price-value');
            if (priceElement) {
                oldPrices[pair] = parseFloat(priceElement.textContent);
            }
        });
        
        priceGrid.innerHTML = Object.keys(prices).map(pair => {
            const price = prices[pair];
            const oldPrice = oldPrices[pair];
            let changeClass = '';
            let changeText = '--';
            
            if (oldPrice && !isNaN(oldPrice)) {
                const change = price.price - oldPrice;
                const changePercent = (change / oldPrice * 100);
                changeClass = change >= 0 ? 'positive' : 'negative';
                changeText = `${change >= 0 ? '+' : ''}${changePercent.toFixed(3)}%`;
            }
            
            return `
                <div class="price-card" data-pair="${pair}">
                    <div class="price-pair">${pair}</div>
                    <div class="price-value">${price.price.toFixed(5)}</div>
                    <div class="price-bid-ask">Bid: ${price.bid.toFixed(5)} | Ask: ${price.ask.toFixed(5)}</div>
                    <div class="price-change ${changeClass}">${changeText}</div>
                </div>
            `;
        }).join('');
    }
    
    async loadTrades() {
        try {
            const response = await fetch('/api/trades');
            if (!response.ok) throw new Error('Failed to load trades');
            
            const trades = await response.json();
            this.displayTrades(trades);
            
        } catch (error) {
            console.error('Error loading trades:', error);
        }
    }
    
    displayTrades(trades) {
        const tbody = document.getElementById('trades-tbody');
        const tradeCount = document.getElementById('trade-count');
        
        if (!tbody) return;
        
        tradeCount.textContent = trades.length;
        
        if (trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No trades yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = trades.slice(-20).reverse().map(trade => {
            const time = new Date(trade.timestamp).toLocaleString();
            const sideClass = trade.side === 'BUY' ? 'side-buy' : 'side-sell';
            
            return `
                <tr>
                    <td>${time}</td>
                    <td>${trade.pair}</td>
                    <td class="${sideClass}">${trade.side}</td>
                    <td>${this.formatNumber(trade.amount)}</td>
                    <td>${trade.price.toFixed(5)}</td>
                    <td>$${this.formatNumber(trade.value, 2)}</td>
                    <td>${trade.algorithm || 'MANUAL'}</td>
                    <td>${trade.status || 'EXECUTED'}</td>
                </tr>
            `;
        }).join('');
    }
    
    async loadTradingStatus() {
        try {
            const response = await fetch('/api/trading/status');
            if (!response.ok) throw new Error('Failed to load trading status');
            
            const stats = await response.json();
            this.tradingStats = stats;
            this.updateTradingStats(stats);
            
        } catch (error) {
            console.error('Error loading trading status:', error);
        }
    }
    
    updateTradingStats(stats) {
        const elements = {
            'daily-volume': `$${this.formatNumber(stats.total_volume_today, 2)}`,
            'volume-limit': `$${this.formatNumber(stats.volume_limit, 2)}`,
            'remaining-capacity': `$${this.formatNumber(stats.remaining_capacity, 2)}`,
            'auto-trading-status': stats.auto_trading_enabled ? (stats.is_running ? 'Running' : 'Ready') : 'Disabled'
        };
        
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });
        
        // Update toggle button
        const toggleBtn = document.getElementById('toggle-trading');
        this.isAutoTradingEnabled = stats.is_running;
        
        if (!stats.auto_trading_enabled) {
            toggleBtn.disabled = true;
            toggleBtn.textContent = 'Volume Limit Reached';
            toggleBtn.className = 'btn btn-secondary';
        } else if (stats.is_running) {
            toggleBtn.disabled = false;
            toggleBtn.textContent = 'Stop Auto Trading';
            toggleBtn.className = 'btn btn-danger';
        } else {
            toggleBtn.disabled = false;
            toggleBtn.textContent = 'Start Auto Trading';
            toggleBtn.className = 'btn btn-success';
        }
    }
    
    async updateChart(pair) {
        try {
            const response = await fetch(`/api/historical/${pair}?limit=50`);
            if (!response.ok) throw new Error('Failed to load chart data');
            
            const data = await response.json();
            
            // Simple chart update - just show recent prices
            const indicatorsPanel = document.getElementById('indicators-panel');
            if (indicatorsPanel && data.length > 0) {
                const recent = data.slice(-10);
                const currentPrice = recent[recent.length - 1].price;
                const sma = recent.reduce((sum, item) => sum + item.price, 0) / recent.length;
                const high = Math.max(...recent.map(item => item.price));
                const low = Math.min(...recent.map(item => item.price));
                
                indicatorsPanel.innerHTML = `
                    <div class="indicator-item">
                        <div class="indicator-label">Current Price</div>
                        <div class="indicator-value">${currentPrice.toFixed(5)}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">SMA (10)</div>
                        <div class="indicator-value">${sma.toFixed(5)}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">High (10p)</div>
                        <div class="indicator-value">${high.toFixed(5)}</div>
                    </div>
                    <div class="indicator-item">
                        <div class="indicator-label">Low (10p)</div>
                        <div class="indicator-value">${low.toFixed(5)}</div>
                    </div>
                `;
            }
            
            this.showNotification(`Chart updated for ${pair}`, 'success');
            
        } catch (error) {
            console.error('Error updating chart:', error);
            this.showNotification('Failed to update chart', 'error');
        }
    }
    
    async toggleAutoTrading() {
        try {
            const endpoint = this.isAutoTradingEnabled ? '/api/trading/stop' : '/api/trading/start';
            const response = await fetch(endpoint, { method: 'POST' });
            
            if (!response.ok) throw new Error('Failed to toggle auto trading');
            
            const result = await response.json();
            this.showNotification(result.status, 'success');
            
            // Refresh status
            setTimeout(() => this.loadTradingStatus(), 1000);
            
        } catch (error) {
            console.error('Error toggling auto trading:', error);
            this.showNotification('Failed to toggle auto trading', 'error');
        }
    }
    
    async handleManualTrade(event) {
        event.preventDefault();
        
        const tradeData = {
            pair: document.getElementById('trade-pair').value,
            side: document.getElementById('trade-side').value,
            amount: parseFloat(document.getElementById('trade-amount').value)
        };
        
        if (!tradeData.pair || !tradeData.side || !tradeData.amount) {
            this.showNotification('Please fill all required fields', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(tradeData)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification(
                    `Trade executed: ${result.side} ${result.amount} ${result.pair} at ${result.price}`,
                    'success'
                );
                
                // Refresh data
                this.loadTrades();
                this.loadTradingStatus();
                
                // Reset form
                event.target.reset();
                document.getElementById('trade-amount').value = '10000';
                
            } else {
                this.showNotification(result.message || 'Trade execution failed', 'error');
            }
            
        } catch (error) {
            console.error('Error executing trade:', error);
            this.showNotification('Trade execution failed', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async runBacktest(event) {
        event.preventDefault();
        
        const backtestData = {
            pair: document.getElementById('backtest-pair').value,
            days: parseInt(document.getElementById('backtest-days').value),
            initial_balance: parseFloat(document.getElementById('backtest-balance').value)
        };
        
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(backtestData)
            });
            
            const result = await response.json();
            
            if (result.error) {
                this.showNotification(result.error, 'error');
            } else {
                this.displayBacktestResults(result);
                this.showNotification('Backtest completed successfully', 'success');
            }
            
        } catch (error) {
            console.error('Error running backtest:', error);
            this.showNotification('Backtest failed', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayBacktestResults(results) {
        const resultsDiv = document.getElementById('backtest-results');
        if (!resultsDiv) return;
        
        const returnClass = results.total_return_pct >= 0 ? 'positive' : 'negative';
        const returnSymbol = results.total_return_pct >= 0 ? '+' : '';
        
        resultsDiv.innerHTML = `
            <h3>Backtest Results for ${results.pair}</h3>
            <div class="result-grid">
                <div class="result-item">
                    <div class="result-label">Initial Balance</div>
                    <div class="result-value">$${this.formatNumber(results.initial_balance, 2)}</div>
                </div>
                <div class="result-item">
                    <div class="result-label">Final Balance</div>
                    <div class="result-value">$${this.formatNumber(results.final_balance, 2)}</div>
                </div>
                <div class="result-item">
                    <div class="result-label">Total Return</div>
                    <div class="result-value ${returnClass}">${returnSymbol}${results.total_return_pct}%</div>
                </div>
                <div class="result-item">
                    <div class="result-label">Total Trades</div>
                    <div class="result-value">${results.total_trades}</div>
                </div>
                <div class="result-item">
                    <div class="result-label">Win Rate</div>
                    <div class="result-value">${results.win_rate_pct}%</div>
                </div>
                <div class="result-item">
                    <div class="result-label">Max Drawdown</div>
                    <div class="result-value negative">${results.max_drawdown_pct}%</div>
                </div>
            </div>
            <p><strong>Period:</strong> ${results.start_date.split('T')[0]} to ${results.end_date.split('T')[0]}</p>
        `;
        
        resultsDiv.style.display = 'block';
    }
    
    formatNumber(num, decimals = 0) {
        if (num === null || num === undefined) return 'N/A';
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div>${message}</div>
        `;
        
        container.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
        
        // Remove on click
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }
}

// Make showNotification globally available
window.showNotification = function(message, type) {
    if (window.app) {
        window.app.showNotification(message, type);
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AlphaFxApp();
});