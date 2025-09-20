// WebSocket connection for real-time data
class WebSocketConnection {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
                
                // Subscribe to price updates
                this.socket.emit('subscribe_prices');
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            });
            
            this.socket.on('connected', (data) => {
                console.log('Server says:', data.status);
            });
            
            this.socket.on('price_update', (data) => {
                this.handlePriceUpdate(data);
            });
            
            this.socket.on('trade_update', (data) => {
                this.handleTradeUpdate(data);
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.updateConnectionStatus('disconnected');
                this.attemptReconnect();
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket connection:', error);
            this.updateConnectionStatus('disconnected');
            this.attemptReconnect();
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            this.updateConnectionStatus('connecting');
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.log('Max reconnection attempts reached');
            this.updateConnectionStatus('disconnected');
        }
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `status-indicator ${status}`;
            
            switch (status) {
                case 'connected':
                    statusElement.textContent = 'Connected';
                    break;
                case 'connecting':
                    statusElement.textContent = 'Connecting...';
                    break;
                case 'disconnected':
                    statusElement.textContent = 'Disconnected';
                    break;
            }
        }
    }
    
    handlePriceUpdate(data) {
        // Update price display
        Object.keys(data).forEach(pair => {
            const priceData = data[pair];
            this.updatePriceDisplay(pair, priceData);
        });
        
        // Update chart if it's for the currently selected pair
        const selectedPair = document.getElementById('chart-pair').value;
        if (data[selectedPair] && window.priceChart) {
            window.priceChart.updatePrice(data[selectedPair]);
        }
    }
    
    updatePriceDisplay(pair, priceData) {
        const priceCard = document.querySelector(`[data-pair="${pair}"]`);
        if (priceCard) {
            const priceValueElement = priceCard.querySelector('.price-value');
            const bidAskElement = priceCard.querySelector('.price-bid-ask');
            const changeElement = priceCard.querySelector('.price-change');
            
            if (priceValueElement) {
                const oldPrice = parseFloat(priceValueElement.textContent);
                const newPrice = priceData.price;
                
                priceValueElement.textContent = newPrice.toFixed(5);
                
                // Update bid/ask
                if (bidAskElement) {
                    bidAskElement.textContent = `Bid: ${priceData.bid.toFixed(5)} | Ask: ${priceData.ask.toFixed(5)}`;
                }
                
                // Show price change animation
                if (!isNaN(oldPrice) && oldPrice !== newPrice) {
                    const change = newPrice - oldPrice;
                    const changePercent = (change / oldPrice * 100).toFixed(2);
                    
                    if (changeElement) {
                        changeElement.textContent = `${change >= 0 ? '+' : ''}${changePercent}%`;
                        changeElement.className = `price-change ${change >= 0 ? 'positive' : 'negative'}`;
                    }
                    
                    // Flash animation
                    priceCard.style.backgroundColor = change >= 0 ? '#dcfce7' : '#fef2f2';
                    setTimeout(() => {
                        priceCard.style.backgroundColor = '';
                    }, 500);
                }
            }
        }
    }
    
    handleTradeUpdate(data) {
        // Refresh trades table
        if (window.app && window.app.loadTrades) {
            window.app.loadTrades();
        }
        
        // Show notification
        if (window.showNotification) {
            window.showNotification(
                `Trade executed: ${data.side} ${data.amount} ${data.pair} at ${data.price}`,
                'success'
            );
        }
    }
}

// Initialize WebSocket connection when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.wsConnection = new WebSocketConnection();
});