# AlphaFX Trader - Deployment Guide

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Node.js**: Version 16.0.0 or higher
- **npm**: Version 8.0.0 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: 100MB free disk space
- **Network**: Internet connection for package installation

### Development Tools (Optional)
- **Git**: For version control
- **PM2**: For production process management
- **nginx**: For reverse proxy (production)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader
```

### 2. Install Dependencies
```bash
# Install server dependencies
npm install

# Install client dependencies
npm run install:client
```

### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Environment Variables:**
```bash
# Server Configuration
NODE_ENV=development
PORT=3001

# Database
DB_PATH=./data/trades.db

# Trading Configuration
MAX_TRADING_VOLUME=10000000
DEFAULT_POSITION_SIZE=10000
RISK_MANAGEMENT=true

# Data Source (leave empty for simulator)
ALPHA_VANTAGE_API_KEY=
FX_DATA_SOURCE=simulator

# Algorithm Parameters
SMA_SHORT_PERIOD=10
SMA_LONG_PERIOD=50
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
BOLLINGER_PERIOD=20
BOLLINGER_STD_DEV=2

# Update Intervals (milliseconds)
PRICE_UPDATE_INTERVAL=1000
ALGORITHM_UPDATE_INTERVAL=5000
```

### 4. Build Client Application
```bash
npm run client:build
```

## Running the Application

### Development Mode
```bash
# Start server only
npm run dev

# Start client development server (separate terminal)
npm run client
```

### Production Mode
```bash
# Build and start
npm run build
npm start
```

### Using PM2 (Recommended for Production)
```bash
# Install PM2 globally
npm install -g pm2

# Create PM2 configuration
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'alpha-fx-trader',
    script: 'server/app.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'development'
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 3001
    }
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js --env production

# Save PM2 configuration
pm2 save
pm2 startup
```

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy client package files
COPY client/package*.json ./client/
RUN cd client && npm ci --only=production

# Copy source code
COPY . .

# Build client
RUN npm run client:build

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 3001

# Start application
CMD ["npm", "start"]
```

### 2. Create docker-compose.yml
```yaml
version: '3.8'

services:
  alpha-fx-trader:
    build: .
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - NODE_ENV=production
      - PORT=3001
      - DB_PATH=/app/data/trades.db
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - alpha-fx-trader
    restart: unless-stopped
```

### 3. Build and Run
```bash
docker-compose up -d
```

## Nginx Reverse Proxy Setup

### 1. Install nginx
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. Configure nginx
Create `/etc/nginx/sites-available/alpha-fx-trader`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.pem;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Proxy to Node.js application
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable site
```bash
sudo ln -s /etc/nginx/sites-available/alpha-fx-trader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Database Setup

### Automatic Setup
The application automatically creates the SQLite database and tables on first run.

### Manual Database Operations
```bash
# Access SQLite database
sqlite3 data/trades.db

# View tables
.tables

# View trade history
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

# View current positions
SELECT * FROM positions WHERE quantity != 0;

# View trading statistics
SELECT * FROM trading_stats ORDER BY date DESC;
```

### Backup Database
```bash
# Create backup
cp data/trades.db data/trades_backup_$(date +%Y%m%d_%H%M%S).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
cp data/trades.db "$BACKUP_DIR/trades_$(date +%Y%m%d_%H%M%S).db"
find $BACKUP_DIR -name "trades_*.db" -mtime +7 -delete
```

## Monitoring and Logging

### Application Logs
```bash
# View PM2 logs
pm2 logs alpha-fx-trader

# View application logs (if using custom logging)
tail -f logs/app.log
tail -f logs/trading.log
tail -f logs/error.log
```

### Health Monitoring
```bash
# Check application health
curl http://localhost:3001/api/health

# Check trading status
curl http://localhost:3001/api/trading/status

# Monitor database size
du -sh data/trades.db
```

### System Monitoring Script
```bash
#!/bin/bash
# monitor.sh

# Check if application is running
if ! curl -s http://localhost:3001/api/health > /dev/null; then
    echo "$(date): Application is down, restarting..." >> monitor.log
    pm2 restart alpha-fx-trader
fi

# Check database size (alert if > 100MB)
DB_SIZE=$(du -m data/trades.db | cut -f1)
if [ $DB_SIZE -gt 100 ]; then
    echo "$(date): Database size is ${DB_SIZE}MB" >> monitor.log
fi

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> monitor.log
fi
```

### Cron Job Setup
```bash
# Add to crontab
crontab -e

# Add monitoring every 5 minutes
*/5 * * * * /path/to/alpha-fx-trader/monitor.sh

# Daily database backup at 2 AM
0 2 * * * /path/to/alpha-fx-trader/backup.sh
```

## Security Considerations

### 1. Network Security
```bash
# Configure firewall (UFW example)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 3001  # Block direct access to Node.js
sudo ufw enable
```

### 2. Application Security
- Use environment variables for sensitive configuration
- Implement rate limiting in production
- Add authentication for production deployment
- Use HTTPS in production
- Regular security updates

### 3. Database Security
- Restrict database file permissions
- Regular backups
- Monitor for unusual database growth
- Implement database encryption for sensitive data

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 3001
sudo lsof -i :3001

# Kill process
sudo kill -9 <PID>
```

#### Database Locked
```bash
# Check for database lock
sqlite3 data/trades.db ".timeout 10000"

# If persistent, restart application
pm2 restart alpha-fx-trader
```

#### Memory Issues
```bash
# Check memory usage
free -h
pm2 monit

# Increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=1024" npm start
```

#### WebSocket Connection Issues
```bash
# Check WebSocket connections
netstat -an | grep :3001

# Test WebSocket connectivity
wscat -c ws://localhost:3001
```

### Log Analysis
```bash
# Search for errors
grep -i error logs/*.log

# Monitor real-time logs
tail -f logs/app.log | grep -i "error\|warning"

# Count trading activity
grep "executed" logs/trading.log | wc -l
```

## Performance Tuning

### Node.js Optimization
```bash
# Production environment variables
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=1024"
export UV_THREADPOOL_SIZE=128
```

### Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_price_history_symbol_timestamp ON price_history(symbol, timestamp);

-- Regular database maintenance
VACUUM;
ANALYZE;
```

### System Optimization
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# TCP optimization
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -p
```

## Backup and Recovery

### Automated Backup Strategy
```bash
#!/bin/bash
# backup-strategy.sh

BACKUP_ROOT="/backups/alpha-fx-trader"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directories
mkdir -p $BACKUP_ROOT/{daily,weekly,monthly}

# Daily backup
cp data/trades.db "$BACKUP_ROOT/daily/trades_$DATE.db"

# Weekly backup (Sundays)
if [ $(date +%u) -eq 7 ]; then
    cp data/trades.db "$BACKUP_ROOT/weekly/trades_$DATE.db"
fi

# Monthly backup (1st of month)
if [ $(date +%d) -eq 01 ]; then
    cp data/trades.db "$BACKUP_ROOT/monthly/trades_$DATE.db"
fi

# Cleanup old backups
find "$BACKUP_ROOT/daily" -name "trades_*.db" -mtime +7 -delete
find "$BACKUP_ROOT/weekly" -name "trades_*.db" -mtime +30 -delete
find "$BACKUP_ROOT/monthly" -name "trades_*.db" -mtime +365 -delete
```

### Recovery Procedures
```bash
# Stop application
pm2 stop alpha-fx-trader

# Restore from backup
cp /backups/alpha-fx-trader/daily/trades_YYYYMMDD_HHMMSS.db data/trades.db

# Restart application
pm2 start alpha-fx-trader

# Verify restoration
curl http://localhost:3001/api/health
```