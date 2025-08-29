# Deployment Guide

This guide covers deployment options for JKB Finance Insights, from development to production environments.

## 🏃‍♂️ Quick Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment support

### Local Development
```bash
# 1. Clone and setup
git clone <repository-url>
cd jkbFinanceInsights

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp env.example .env
# Edit .env with your settings

# 5. Run application
python main.py
```

Access at: http://localhost:8000

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/debug-status || exit 1

# Run application
CMD ["python", "main.py"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
      - DATABASE_URL=/app/data/finance_insights.db
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/debug-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add Redis for future RQ migration
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Build and Run
```bash
# Build image
docker build -t jkb-finance-insights .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Option 1: AWS ECS with Fargate
```bash
# 1. Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker build -t jkb-finance-insights .
docker tag jkb-finance-insights:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/jkb-finance-insights:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/jkb-finance-insights:latest

# 2. Create ECS task definition
# 3. Create ECS service
# 4. Configure load balancer
```

#### Option 2: AWS Lambda (Serverless)
```python
# lambda_handler.py
from mangum import Mangum
from app import app

handler = Mangum(app)
```

### Google Cloud Platform

#### Cloud Run Deployment
```bash
# 1. Build and deploy
gcloud run deploy jkb-finance-insights \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10
```

### Digital Ocean App Platform
```yaml
# .do/app.yaml
name: jkb-finance-insights
services:
  - name: web
    source_dir: /
    github:
      repo: your-username/jkb-finance-insights
      branch: main
    run_command: python main.py
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8000
    envs:
      - key: SERVER_HOST
        value: "0.0.0.0"
      - key: SERVER_PORT
        value: "8000"
```

## 🖥️ Traditional Server Deployment

### Ubuntu/Debian Server

#### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx supervisor curl

# Create application user
sudo useradd -m -s /bin/bash jkbfinance
sudo usermod -aG sudo jkbfinance
```

#### 2. Application Setup
```bash
# Switch to app user
sudo su - jkbfinance

# Clone and setup application
git clone <repository-url> /home/jkbfinance/app
cd /home/jkbfinance/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cp env.example .env
# Edit .env with production settings
```

#### 3. Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
keepalive = 2
timeout = 30
user = "jkbfinance"
group = "jkbfinance"
tmp_upload_dir = None
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}
```

#### 4. Supervisor Configuration
```ini
# /etc/supervisor/conf.d/jkbfinance.conf
[program:jkbfinance]
command=/home/jkbfinance/app/venv/bin/gunicorn -c gunicorn.conf.py app:app
directory=/home/jkbfinance/app
user=jkbfinance
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/jkbfinance.log
environment=PATH="/home/jkbfinance/app/venv/bin"
```

#### 5. Nginx Configuration
```nginx
# /etc/nginx/sites-available/jkbfinance
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/jkbfinance/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 6. SSL with Let's Encrypt
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (crontab)
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 7. Start Services
```bash
# Enable and start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start jkbfinance

sudo systemctl enable nginx
sudo systemctl start nginx

# Check status
sudo supervisorctl status jkbfinance
sudo systemctl status nginx
```

## 🔧 Production Configuration

### Environment Variables
```bash
# Production .env
DEBUG_MODE=false
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Database
DATABASE_URL=/app/data/finance_insights.db

# Security
CORS_ENABLED=true
CORS_ALLOWED_ORIGINS=https://your-domain.com
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Performance
TASK_WORKER_COUNT=4
FRONTEND_TABLE_REFRESH_INTERVAL=30000

# External Services
OPENAI_API_KEY=your_production_api_key
```

### Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/jkbfinance/backups"
DB_PATH="/home/jkbfinance/app/finance_insights.db"

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup $BACKUP_DIR/finance_insights_$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

# Add to crontab: 0 2 * * * /home/jkbfinance/backup.sh
```

### Log Rotation
```bash
# /etc/logrotate.d/jkbfinance
/var/log/supervisor/jkbfinance.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 jkbfinance jkbfinance
    postrotate
        supervisorctl restart jkbfinance
    endscript
}
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint
```python
# Already available at /api/debug-status
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": APP_VERSION
    }
```

### Monitoring Script
```bash
#!/bin/bash
# monitor.sh
URL="http://localhost:8000/api/debug-status"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): Service is healthy"
else
    echo "$(date): Service is down (HTTP $RESPONSE)"
    # Restart service
    sudo supervisorctl restart jkbfinance
fi
```

### Performance Monitoring
```python
# Add to app.py for production monitoring
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🔄 Deployment Automation

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /home/jkbfinance/app
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo supervisorctl restart jkbfinance
```

### Deployment Checklist
- [ ] Update environment variables
- [ ] Run database migrations (if any)
- [ ] Update dependencies
- [ ] Restart application services
- [ ] Verify health checks
- [ ] Check application logs
- [ ] Test critical functionality
- [ ] Monitor performance metrics

## 🚨 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo supervisorctl tail -f jkbfinance

# Check Python path
which python
source venv/bin/activate && which python

# Check dependencies
pip list | grep fastapi
```

#### Database Issues
```bash
# Check database file permissions
ls -la finance_insights.db

# Test database connection
sqlite3 finance_insights.db ".tables"
```

#### High Memory Usage
```bash
# Monitor memory usage
htop
ps aux | grep gunicorn

# Reduce worker count in gunicorn.conf.py
workers = 2  # Reduce from 4
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run
```

### Log Locations
- Application logs: `/var/log/supervisor/jkbfinance.log`
- Nginx logs: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- System logs: `/var/log/syslog`

This deployment guide provides comprehensive coverage for getting JKB Finance Insights running in various environments, from development to production.
