# Docker Deployment Guide - AI Consultancy SaaS Platform

This comprehensive guide will walk you through deploying your AI consultancy SaaS platform using Docker, from development to production.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (v20.10+)
- Docker Compose (v2.0+)
- Git
- 8GB+ RAM recommended

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd "Agentic Framework"
cp .env.template .env
```

### 2. Configure Environment
Edit `.env` file with your API keys and settings:
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
TWITTER_API_KEY=your_twitter_key_here
TWITTER_API_SECRET=your_twitter_secret_here
TELEGRAM_BOT_TOKEN=your_telegram_token_here

# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/ai_consultancy
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here

# Application Settings
ENVIRONMENT=production
DEBUG=false
```

### 3. Deploy with One Command
```bash
./scripts/deploy.sh
```

Your platform will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Detailed Deployment Options

### Development Environment
For development with hot reload and debugging:
```bash
# Start development environment
./scripts/manage.sh start dev

# View logs
./scripts/manage.sh logs backend
./scripts/manage.sh logs frontend

# Run tests
./scripts/manage.sh test

# Stop development environment
./scripts/manage.sh stop dev
```

### Production Environment
For production deployment with monitoring:
```bash
# Deploy with monitoring stack
./scripts/deploy.sh --with-monitoring

# Access monitoring
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### Manual Docker Compose Commands
```bash
# Production deployment
docker-compose up -d

# Development deployment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🏗️ Architecture Overview

### Services Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  React Frontend │    │  FastAPI Backend│
│   (Port 80/443) │    │   (Port 3000)   │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │   PostgreSQL    │    │     Redis       │    │ Celery Workers  │
         │   (Port 5432)   │    │   (Port 6379)   │    │  (Background)   │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Details

#### 1. **Backend Container** (`backend/`)
- **Base**: Python 3.11-slim
- **Framework**: FastAPI with Uvicorn
- **Features**: JWT auth, async processing, AI agents
- **Health Check**: `/health` endpoint
- **Ports**: 8000 (internal)

#### 2. **Frontend Container** (`frontend/`)
- **Base**: Node.js 18 + Nginx
- **Framework**: React with modern build tools
- **Features**: Responsive UI, API integration
- **Ports**: 3000 (internal)

#### 3. **Database Container**
- **Image**: PostgreSQL 15
- **Features**: Persistent storage, automated backups
- **Ports**: 5432 (internal)
- **Volume**: `postgres_data`

#### 4. **Cache Container**
- **Image**: Redis 7-alpine
- **Features**: Session storage, task queuing
- **Ports**: 6379 (internal)
- **Volume**: `redis_data`

#### 5. **Worker Container**
- **Base**: Same as backend
- **Purpose**: Celery background tasks
- **Features**: AI processing, memory management

#### 6. **Nginx Proxy**
- **Image**: Nginx 1.24-alpine
- **Features**: Reverse proxy, SSL termination, rate limiting
- **Ports**: 80, 443 (external)

## 🔧 Configuration Files

### Docker Compose Files

#### `docker-compose.yml` (Production)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_consultancy
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - backend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      - backend

  nginx:
    image: nginx:1.24-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

#### `docker-compose.dev.yml` (Development)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_consultancy_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - DATABASE_URL=postgresql://postgres:devpassword@postgres:5432/ai_consultancy_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    command: npm start

volumes:
  postgres_dev_data:
```

### Dockerfile Examples

#### `Dockerfile.backend`
```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Development stage
FROM base as development
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chown -R app:app /app
USER app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### `frontend/Dockerfile`
```dockerfile
# Multi-stage build for React frontend
FROM node:18-alpine as base

# Development stage
FROM base as development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# Build stage
FROM base as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.24-alpine as production
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🛠️ Management Scripts

### `scripts/deploy.sh`
```bash
#!/bin/bash
set -e

echo "🚀 Deploying AI Consultancy SaaS Platform..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed."; exit 1; }

# Check environment file
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.template to .env and configure it."
    exit 1
fi

# Validate required environment variables
source .env
required_vars=("OPENAI_API_KEY" "SECRET_KEY" "JWT_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env file."
        exit 1
    fi
done

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "unhealthy\|Exit"; then
    echo "❌ Some services are not healthy. Check logs:"
    docker-compose logs
    exit 1
fi

echo "✅ Deployment successful!"
echo ""
echo "🌐 Access your platform:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Management commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart [service]"
```

### `scripts/manage.sh`
```bash
#!/bin/bash

case "$1" in
    "start")
        if [ "$2" = "dev" ]; then
            docker-compose -f docker-compose.dev.yml up -d
        else
            docker-compose up -d
        fi
        ;;
    "stop")
        if [ "$2" = "dev" ]; then
            docker-compose -f docker-compose.dev.yml down
        else
            docker-compose down
        fi
        ;;
    "logs")
        docker-compose logs -f $2
        ;;
    "test")
        docker-compose exec backend python -m pytest
        ;;
    "backup")
        docker-compose exec postgres pg_dump -U postgres ai_consultancy > backup_$(date +%Y%m%d_%H%M%S).sql
        ;;
    "restore")
        docker-compose exec -T postgres psql -U postgres ai_consultancy < $2
        ;;
    "health")
        docker-compose ps
        ;;
    *)
        echo "Usage: $0 {start|stop|logs|test|backup|restore|health} [options]"
        ;;
esac
```

## 🔒 Security Configuration

### Environment Variables (`.env`)
```bash
# CRITICAL: Never commit this file to version control
# Copy from .env.template and customize

# API Keys (Required)
OPENAI_API_KEY=sk-your-openai-key-here
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Database Configuration
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/ai_consultancy
POSTGRES_PASSWORD=secure_password_here
REDIS_URL=redis://redis:6379/0

# Security Keys (Generate strong random keys)
SECRET_KEY=your-super-secret-key-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Application Settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring (Optional)
ENABLE_MONITORING=true
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

### SSL/HTTPS Configuration
```bash
# Generate SSL certificates
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/private.key \
    -out nginx/ssl/certificate.crt
```

## 📊 Monitoring and Logging

### Prometheus Configuration (`prometheus/prometheus.yml`)
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboard
- **Application Metrics**: Request rates, response times, error rates
- **System Metrics**: CPU, memory, disk usage
- **Database Metrics**: Connection pools, query performance
- **AI Agent Metrics**: Task completion rates, processing times

## 🚨 Troubleshooting

### Common Issues

#### 1. **Port Already in Use**
```bash
# Check what's using the port
lsof -i :8000
# Kill the process
kill -9 <PID>
```

#### 2. **Database Connection Issues**
```bash
# Check database logs
docker-compose logs postgres
# Reset database
docker-compose down -v
docker-compose up -d
```

#### 3. **Memory Issues**
```bash
# Check container resource usage
docker stats
# Increase Docker memory limit in Docker Desktop settings
```

#### 4. **API Key Issues**
```bash
# Verify environment variables
docker-compose exec backend env | grep API_KEY
# Check .env file format (no spaces around =)
```

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:3000

# Check database connection
docker-compose exec postgres pg_isready -U postgres

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Log Analysis
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Search logs for errors
docker-compose logs | grep ERROR
```

## 🌐 Production Deployment

### Cloud Deployment Options

#### 1. **AWS ECS**
```bash
# Install AWS CLI and configure
aws configure

# Create ECS cluster
aws ecs create-cluster --cluster-name ai-consultancy

# Deploy using docker-compose
docker context create ecs myecscontext
docker context use myecscontext
docker compose up
```

#### 2. **Google Cloud Run**
```bash
# Build and push images
docker build -t gcr.io/PROJECT_ID/backend .
docker push gcr.io/PROJECT_ID/backend

# Deploy to Cloud Run
gcloud run deploy backend --image gcr.io/PROJECT_ID/backend
```

#### 3. **Azure Container Instances**
```bash
# Create resource group
az group create --name ai-consultancy --location eastus

# Deploy container group
az container create --resource-group ai-consultancy \
    --file docker-compose.yml
```

### Domain and SSL Setup
```bash
# Update nginx configuration for your domain
# Add SSL certificates
# Configure DNS records
# Set up automatic certificate renewal with Let's Encrypt
```

## 📈 Scaling and Performance

### Horizontal Scaling
```yaml
# Scale specific services
docker-compose up -d --scale backend=3 --scale celery=2
```

### Load Balancing
```nginx
# nginx/nginx.conf
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);
```

## 🔄 Backup and Recovery

### Automated Backups
```bash
# Daily database backup
0 2 * * * docker-compose exec postgres pg_dump -U postgres ai_consultancy > /backups/db_$(date +\%Y\%m\%d).sql

# Weekly full backup
0 3 * * 0 tar -czf /backups/full_backup_$(date +\%Y\%m\%d).tar.gz /var/lib/docker/volumes/
```

### Disaster Recovery
```bash
# Restore from backup
docker-compose down
docker volume rm agentic-framework_postgres_data
docker-compose up -d postgres
docker-compose exec -T postgres psql -U postgres ai_consultancy < backup.sql
docker-compose up -d
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [React Production Build](https://create-react-app.dev/docs/production-build/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)

---

## 🎯 Next Steps

1. **Configure your `.env` file** with actual API keys
2. **Run the deployment script**: `./scripts/deploy.sh`
3. **Access your platform** at http://localhost:3000
4. **Set up monitoring** with `--with-monitoring` flag
5. **Configure SSL** for production deployment
6. **Set up automated backups** for data protection

Your AI consultancy SaaS platform is now ready for production deployment! 🚀
