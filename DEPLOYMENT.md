# AlphaFX Trader Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AlphaFX Trader system in development, staging, and production environments. The system consists of a FastAPI backend, React frontend, and SQLite database (development) or PostgreSQL (production).

## Quick Start (Development)

### Prerequisites

- Python 3.8+ 
- Node.js 16+
- npm or yarn
- Git

### 1. Clone and Setup Backend

```bash
# Clone the repository
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
cd app
pip install -r requirements.txt

# Initialize database with sample data
python db_init.py --init

# Start the backend server
python main.py
```

The backend will be running at `http://localhost:8000`
API documentation available at `http://localhost:8000/docs`

### 2. Setup and Start Frontend

```bash
# Open new terminal in project root
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be running at `http://localhost:3000`

### 3. Access the Application

1. Open your browser to `http://localhost:3000`
2. The dashboard should show live FX rates and trading interface
3. API documentation: `http://localhost:8000/docs`

## Detailed Backend Setup

### Environment Configuration

Create `.env` file in the `app/` directory:

```bash
# app/.env
DATABASE_URL=sqlite:///./alphafx_trader.db
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
DATA_SOURCE=mock
API_RATE_LIMIT=1000
```

### Python Dependencies

```bash
# Core dependencies
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install sqlalchemy==2.0.23
pip install pydantic==2.5.0

# Data processing
pip install numpy==1.24.3
pip install pandas==2.0.3

# HTTP client
pip install aiohttp==3.9.0

# Database
pip install alembic==1.12.1

# Development tools
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1
```

### Database Setup

#### SQLite (Development)
```bash
cd app
python db_init.py --init
```

#### PostgreSQL (Production)
```bash
# Install PostgreSQL dependencies
pip install psycopg2-binary==2.9.7

# Update .env file
DATABASE_URL=postgresql://username:password@localhost:5432/alphafx_db

# Run migrations
python db_init.py --init
```

### Running the Backend

#### Development Mode
```bash
cd app
python main.py
```

#### Production Mode with Gunicorn
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Detailed Frontend Setup

### Node.js Dependencies

```bash
cd frontend
npm install

# Development dependencies
npm install --save-dev @types/react @types/react-dom typescript vite
npm install --save-dev @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install --save-dev eslint eslint-plugin-react

# Runtime dependencies  
npm install react react-dom react-router-dom
npm install axios recharts antd @ant-design/icons
npm install moment socket.io-client styled-components
npm install react-query lodash
```

### Frontend Configuration

Update `vite.config.ts` for different environments:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
    sourcemap: true
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV)
  }
})
```

### Environment Variables

Create `.env` files for different environments:

#### `.env.development`
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
```

#### `.env.production`
```bash
VITE_API_URL=https://api.alphafx-trader.com
VITE_WS_URL=wss://api.alphafx-trader.com
VITE_ENV=production
```

### Build for Production

```bash
cd frontend
npm run build
```

## Docker Deployment

### Backend Dockerfile

Create `app/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Initialize database
RUN python db_init.py --init

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

Create `frontend/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 80;
        server_name localhost;

        # Serve static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # Proxy API requests
        location /api/ {
            proxy_pass http://backend:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://backend:8000/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ./app
      dockerfile: Dockerfile
    container_name: alphafx-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/alphafx
      - DEBUG=false
    depends_on:
      - db
    volumes:
      - ./app:/app
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: alphafx-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: alphafx-db
    environment:
      - POSTGRES_DB=alphafx
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: alphafx-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
```

### Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

## Production Deployment

### AWS Deployment

#### Using EC2 with Docker

```bash
# 1. Launch EC2 instance (Ubuntu 20.04+)
# 2. Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# 3. Clone and deploy
git clone https://github.com/Anubothu-Aravind/alpha-fx-trader.git
cd alpha-fx-trader
docker-compose -f docker-compose.prod.yml up -d
```

#### Using ECS (Elastic Container Service)

Create `ecs-task-definition.json`:

```json
{
  "family": "alphafx-trader",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-repo/alphafx-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/alphafx"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/alphafx-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    },
    {
      "name": "frontend",
      "image": "your-repo/alphafx-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/alphafx-frontend", 
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Kubernetes Deployment

#### Backend Deployment

Create `k8s/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alphafx-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alphafx-backend
  template:
    metadata:
      labels:
        app: alphafx-backend
    spec:
      containers:
      - name: backend
        image: alphafx/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        - name: DEBUG
          value: "false"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: alphafx-backend-service
spec:
  selector:
    app: alphafx-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment

Create `k8s/frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alphafx-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: alphafx-frontend
  template:
    metadata:
      labels:
        app: alphafx-frontend
    spec:
      containers:
      - name: frontend
        image: alphafx/frontend:latest
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: alphafx-frontend-service
spec:
  selector:
    app: alphafx-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

## SSL/HTTPS Setup

### Using Let's Encrypt with Nginx

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx SSL Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        root /var/www/alphafx-trader;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring and Logging

### Application Monitoring

```python
# app/monitoring.py
import logging
import time
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    REQUEST_LATENCY.observe(process_time)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Centralized Logging

Create `docker-compose.logging.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:7.17.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

  filebeat:
    image: elastic/filebeat:7.17.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml
      - /var/lib/docker/containers:/var/lib/docker/containers:ro

volumes:
  elasticsearch_data:
```

## Testing

### Backend Testing

```bash
cd app

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest -v

# Run with coverage
pip install pytest-cov
pytest --cov=. --cov-report=html
```

### Frontend Testing

```bash
cd frontend

# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

### Load Testing

```bash
# Install artillery
npm install -g artillery

# Create load test config
cat > load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Get rates"
    requests:
      - get:
          url: "/rates"
  - name: "Execute trade"
    requests:
      - post:
          url: "/trade"
          json:
            pair: "EUR/USD"
            action: "buy"
            volume: 0.1
EOF

# Run load test
artillery run load-test.yml
```

## Security Checklist

### Backend Security
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] Rate limiting implementation
- [ ] HTTPS enforcement
- [ ] Security headers
- [ ] Environment variable protection
- [ ] Database connection encryption

### Frontend Security
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Content Security Policy
- [ ] Secure cookie settings
- [ ] Input sanitization
- [ ] Authentication token handling

### Infrastructure Security
- [ ] Firewall configuration
- [ ] VPC/Network security
- [ ] Database access controls
- [ ] SSL certificate management
- [ ] Backup encryption
- [ ] Access logging

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -h localhost -U postgres alphafx > backup_$(date +%Y%m%d).sql

# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres alphafx | gzip > /backups/alphafx_$DATE.sql.gz
find /backups -name "alphafx_*.sql.gz" -mtime +7 -delete
EOF

# Schedule backup
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

### Recovery Procedure

```bash
# Restore from backup
gunzip -c /backups/alphafx_20240115.sql.gz | psql -h localhost -U postgres alphafx

# Application recovery
docker-compose down
docker-compose up -d db
# Wait for database
sleep 30
docker-compose up -d
```

This deployment guide provides a comprehensive foundation for deploying AlphaFX Trader in various environments, from local development to production-ready infrastructure.