# AlphaFX Trader - Deployment Guide

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM
- **Storage**: 1GB free space
- **Network**: Internet connection for package installation

### Required Software
```bash
# Python 3.8+
python3 --version

# pip (Python package manager)
pip3 --version

# Git (for cloning repository)
git --version
```

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt
```

### 4. Initialize Database
The database will be automatically created when you first run the application.

## Running the Application

### Development Mode
```bash
# Run with Python
python3 run.py

# Alternative: Run Flask directly
python3 -m backend.app
```

### Production Mode
```bash
# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key

# Run application
python3 run.py
```

### Application Access
Once started, access the application at:
- **Web Interface**: http://localhost:5000
- **API Documentation**: Available in this document
- **WebSocket Endpoint**: ws://localhost:5000/socket.io/

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```bash
# Database configuration
DATABASE_URL=sqlite:///data/trades.db

# Trading settings
MAX_TRADING_VOLUME=10000000
SECRET_KEY=your-secret-key-here

# Algorithm parameters
SMA_SHORT_PERIOD=10
SMA_LONG_PERIOD=30
RSI_PERIOD=14
BOLLINGER_PERIOD=20
BOLLINGER_STD=2

# Development settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### Configuration Options

#### Trading Parameters
- `MAX_TRADING_VOLUME`: Daily trading volume limit (default: $10M)
- `SMA_SHORT_PERIOD`: Short moving average period (default: 10)
- `SMA_LONG_PERIOD`: Long moving average period (default: 30)
- `RSI_PERIOD`: RSI calculation period (default: 14)

#### System Settings
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_DEBUG`: Enable debug mode (development only)

## Directory Structure

```
alpha-fx-trader/
├── backend/                 # Backend application
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   ├── api/               # API routes and handlers
│   └── app.py             # Main Flask application
├── frontend/               # Frontend application
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript modules
│   ├── static/            # Static assets
│   └── index.html         # Main HTML file
├── data/                   # Database and data files
│   └── trades.db          # SQLite database (auto-created)
├── docs/                   # Documentation
├── tests/                  # Test files
├── config/                # Configuration files
├── requirements.txt        # Python dependencies
├── run.py                 # Application entry point
└── README.md              # Project readme
```

## Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Run application
CMD ["python3", "run.py"]
```

### 2. Build Docker Image
```bash
docker build -t alpha-fx-trader .
```

### 3. Run Docker Container
```bash
docker run -d \
  --name alpha-fx-trader \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  alpha-fx-trader
```

### 4. Docker Compose (Optional)
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  alpha-fx-trader:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key
      - MAX_TRADING_VOLUME=10000000
    restart: unless-stopped

networks:
  default:
    name: alpha-fx-trader-network
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## Production Deployment

### 1. Using Gunicorn (Recommended)

#### Install Gunicorn
```bash
pip install gunicorn eventlet
```

#### Run with Gunicorn
```bash
gunicorn --worker-class eventlet \
  --workers 1 \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  backend.app:app
```

### 2. Using systemd (Linux)

#### Create Service File
`/etc/systemd/system/alpha-fx-trader.service`:
```ini
[Unit]
Description=AlphaFX Trader Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/alpha-fx-trader
Environment=PATH=/opt/alpha-fx-trader/venv/bin
ExecStart=/opt/alpha-fx-trader/venv/bin/python3 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable alpha-fx-trader
sudo systemctl start alpha-fx-trader
```

### 3. Nginx Reverse Proxy

#### Install Nginx
```bash
sudo apt install nginx
```

#### Configure Nginx
`/etc/nginx/sites-available/alpha-fx-trader`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000/socket.io/;
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

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/alpha-fx-trader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Database Management

### Backup Database
```bash
# Create backup
sqlite3 data/trades.db ".backup data/trades_backup_$(date +%Y%m%d).db"

# Or copy file
cp data/trades.db data/trades_backup_$(date +%Y%m%d).db
```

### Restore Database
```bash
# Restore from backup
cp data/trades_backup_YYYYMMDD.db data/trades.db
```

### Database Maintenance
```bash
# Optimize database
sqlite3 data/trades.db "VACUUM;"

# Analyze database statistics
sqlite3 data/trades.db "ANALYZE;"
```

## Monitoring and Logging

### Application Logs
```bash
# View logs (if using systemd)
sudo journalctl -u alpha-fx-trader -f

# View logs (if running directly)
tail -f /var/log/alpha-fx-trader.log
```

### Health Monitoring
```bash
# Check application status
curl http://localhost:5000/api/trading/status

# Monitor WebSocket connections
netstat -an | grep 5000
```

### Performance Monitoring
```bash
# Monitor system resources
htop

# Monitor database file size
ls -lh data/trades.db

# Check disk space
df -h
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 PID
```

#### 2. Database Permission Issues
```bash
# Fix database permissions
chmod 664 data/trades.db
chown www-data:www-data data/trades.db
```

#### 3. Module Import Errors
```bash
# Verify Python path
export PYTHONPATH=/path/to/alpha-fx-trader:$PYTHONPATH

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### 4. WebSocket Connection Issues
- Check firewall settings
- Verify proxy configuration for WebSocket support
- Ensure eventlet is installed for WebSocket support

### Debug Mode
Enable debug logging:
```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
python3 run.py
```

## Security Considerations

### Production Security
- Change default SECRET_KEY
- Use HTTPS with SSL certificates
- Implement authentication for production use
- Configure firewall rules
- Regular security updates

### Data Protection
- Regular database backups
- Secure file permissions
- Monitor access logs
- Implement rate limiting

## Scaling and Performance

### Performance Optimization
- Use connection pooling for database
- Implement caching for frequently accessed data
- Optimize database queries
- Monitor memory usage

### Horizontal Scaling
- Load balance multiple instances
- Use Redis for session storage
- Implement message queue for high-frequency trading
- Database replication for read scaling

## Maintenance

### Regular Tasks
- Database backups (daily)
- Log rotation (weekly)
- Security updates (monthly)
- Performance monitoring (continuous)

### Upgrade Process
1. Backup database and configuration
2. Stop application
3. Update code
4. Install new dependencies
5. Run database migrations (if any)
6. Restart application
7. Verify functionality