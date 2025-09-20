// Price Chart with Technical Indicators
class PriceChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
        this.currentPair = 'EUR/USD';
        this.priceData = [];
        this.indicators = {};
        
        this.initChart();
    }
    
    initChart() {
        const ctx = this.canvas.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price',
                    data: [],
                    borderColor: '#2a5298',
                    backgroundColor: 'rgba(42, 82, 152, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }, {
                    label: 'SMA Short',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0
                }, {
                    label: 'SMA Long',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0
                }, {
                    label: 'Bollinger Upper',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    borderDash: [5, 5]
                }, {
                    label: 'Bollinger Lower',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    pointRadius: 0,
                    borderDash: [5, 5]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    async loadHistoricalData(pair) {
        try {
            this.currentPair = pair;
            const response = await fetch(`/api/historical/${pair}?limit=50`);
            
            if (!response.ok) {
                throw new Error('Failed to load historical data');
            }
            
            const data = await response.json();
            this.priceData = data;
            
            this.updateChart();
            await this.loadIndicators();
            
        } catch (error) {
            console.error('Error loading historical data:', error);
            window.showNotification && window.showNotification('Failed to load chart data', 'error');
        }
    }
    
    async loadIndicators() {
        try {
            const response = await fetch(`/api/algorithms/signals/${this.currentPair}`);
            
            if (!response.ok) {
                throw new Error('Failed to load indicators');
            }
            
            const data = await response.json();
            this.indicators = data.indicators;
            
            this.updateIndicatorsDisplay();
            
        } catch (error) {
            console.error('Error loading indicators:', error);
        }
    }
    
    updateChart() {
        if (!this.chart || !this.priceData.length) return;
        
        const labels = this.priceData.map(item => {
            const date = new Date(item.timestamp);
            return date.toLocaleTimeString();
        });
        
        const prices = this.priceData.map(item => item.price);
        
        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = prices;
        
        // Calculate simple indicators for display
        if (prices.length >= 30) {
            const smaShort = this.calculateSMA(prices, 10);
            const smaLong = this.calculateSMA(prices, 30);
            const bollinger = this.calculateBollingerBands(prices, 20);
            
            this.chart.data.datasets[1].data = smaShort;
            this.chart.data.datasets[2].data = smaLong;
            this.chart.data.datasets[3].data = bollinger.upper;
            this.chart.data.datasets[4].data = bollinger.lower;
        }
        
        this.chart.update('none');
    }
    
    updatePrice(priceData) {
        if (!this.chart || this.currentPair !== priceData.pair) return;
        
        // Add new price point
        const time = new Date().toLocaleTimeString();
        this.chart.data.labels.push(time);
        this.chart.data.datasets[0].data.push(priceData.price);
        
        // Keep only last 50 points
        if (this.chart.data.labels.length > 50) {
            this.chart.data.labels.shift();
            this.chart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        this.chart.update('none');
    }
    
    calculateSMA(prices, period) {
        const sma = [];
        for (let i = 0; i < prices.length; i++) {
            if (i < period - 1) {
                sma.push(null);
            } else {
                const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
                sma.push(sum / period);
            }
        }
        return sma;
    }
    
    calculateBollingerBands(prices, period, stdDev = 2) {
        const sma = this.calculateSMA(prices, period);
        const upper = [];
        const lower = [];
        
        for (let i = 0; i < prices.length; i++) {
            if (i < period - 1 || sma[i] === null) {
                upper.push(null);
                lower.push(null);
            } else {
                const periodPrices = prices.slice(i - period + 1, i + 1);
                const mean = sma[i];
                const variance = periodPrices.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / period;
                const std = Math.sqrt(variance);
                
                upper.push(mean + (stdDev * std));
                lower.push(mean - (stdDev * std));
            }
        }
        
        return { upper, lower };
    }
    
    updateIndicatorsDisplay() {
        const indicatorsPanel = document.getElementById('indicators-panel');
        if (!indicatorsPanel || !this.indicators) return;
        
        const indicators = [
            { label: 'SMA Short', value: this.indicators.sma_short, format: 'price' },
            { label: 'SMA Long', value: this.indicators.sma_long, format: 'price' },
            { label: 'RSI', value: this.indicators.rsi, format: 'percent' },
            { label: 'BB Upper', value: this.indicators.bollinger_upper, format: 'price' },
            { label: 'BB Middle', value: this.indicators.bollinger_middle, format: 'price' },
            { label: 'BB Lower', value: this.indicators.bollinger_lower, format: 'price' },
            { label: 'Current Price', value: this.indicators.current_price, format: 'price' }
        ];
        
        indicatorsPanel.innerHTML = indicators.map(indicator => {
            let formattedValue = 'N/A';
            if (indicator.value !== null && indicator.value !== undefined) {
                if (indicator.format === 'price') {
                    formattedValue = indicator.value.toFixed(5);
                } else if (indicator.format === 'percent') {
                    formattedValue = indicator.value.toFixed(2) + '%';
                }
            }
            
            return `
                <div class="indicator-item">
                    <div class="indicator-label">${indicator.label}</div>
                    <div class="indicator-value">${formattedValue}</div>
                </div>
            `;
        }).join('');
    }
    
    changePair(pair) {
        this.loadHistoricalData(pair);
    }
}

// Initialize chart when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.priceChart = new PriceChart('price-chart');
    
    // Chart pair selector
    const chartPairSelect = document.getElementById('chart-pair');
    chartPairSelect.addEventListener('change', (e) => {
        window.priceChart.changePair(e.target.value);
    });
    
    // Refresh chart button
    const refreshChartBtn = document.getElementById('refresh-chart');
    refreshChartBtn.addEventListener('click', () => {
        const selectedPair = chartPairSelect.value;
        window.priceChart.loadHistoricalData(selectedPair);
    });
    
    // Load initial chart data
    window.priceChart.loadHistoricalData('EUR/USD');
});