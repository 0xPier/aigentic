# AI Consultancy Platform - Docker Deployment Guide

This guide provides comprehensive instructions for deploying the AI Consultancy SaaS platform using Docker containers.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- At least 4GB RAM and 10GB disk space
- OpenAI API key (required)
- Optional: Twitter/X, Telegram, Stability AI API keys

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agentic-framework
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your API keys and configuration
nano .env
```

**Required Configuration:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT secret (minimum 32 characters)
- `POSTGRES_PASSWORD`: Secure database password

### 3. Deploy

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy the platform
./scripts/deploy.sh
```

### 4. Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Deployment Options

### Production Deployment

```bash
# Full production deployment with monitoring
./scripts/deploy.sh --with-monitoring

# Access monitoring
# Grafana: http://localhost:3001 (admin/admin)
# Prometheus: http://localhost:9090
```

### Development Deployment

```bash
# Start development environment with hot reload
./scripts/manage.sh start dev

# Run tests
./scripts/manage.sh test

# View logs
./scripts/manage.sh logs backend
```

## 🏗️ Architecture

### Services Overview

| Service | Purpose | Port | Health Check |
|---------|---------|------|--------------|
| `postgres` | PostgreSQL database | 5432 | `pg_isready` |
| `redis` | Celery broker/cache | 6379 | `redis-cli ping` |
| `backend` | FastAPI application | 8000 | `/health` endpoint |
| `celery_worker` | Background task processor | - | Process monitoring |
| `celery_beat` | Task scheduler | - | Process monitoring |
| `frontend` | React application | 3000 | HTTP response |
| `nginx` | Reverse proxy | 80/443 | HTTP response |

### Optional Services

| Service | Purpose | Port | Profile |
|---------|---------|------|---------|
| `prometheus` | Metrics collection | 9090 | `monitoring` |
| `grafana` | Metrics visualization | 3001 | `monitoring` |

## 🔧 Management Commands

### Service Management

```bash
# Start services
./scripts/manage.sh start [dev|prod]

# Stop services
./scripts/manage.sh stop

# Restart services
./scripts/manage.sh restart [service-name]

# View service status
./scripts/manage.sh status

# Check service health
./scripts/manage.sh health
```

### Development Tools

```bash
# View logs
./scripts/manage.sh logs [service-name]

# Open shell in container
./scripts/manage.sh shell backend

# Run tests
./scripts/manage.sh test

# Build images
./scripts/manage.sh build
```

### Database Management

```bash
# Run migrations
./scripts/manage.sh db-migrate

# Reset database (WARNING: destroys data)
./scripts/manage.sh db-reset

# Backup database
./scripts/manage.sh backup

# Restore database
./scripts/manage.sh restore backup_file.sql
```

### Maintenance

```bash
# Clean up containers and images
./scripts/manage.sh clean

# View help
./scripts/manage.sh help
```

## 🔐 Security Configuration

### Environment Variables

**Critical Security Settings:**
```env
# JWT Configuration
SECRET_KEY=your_super_secret_jwt_key_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Security
POSTGRES_PASSWORD=your_secure_postgres_password
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/agentic_platform

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,app.yourdomain.com
```

### SSL/HTTPS Setup

1. **Obtain SSL certificates:**
```bash
# Using Let's Encrypt (recommended)
certbot certonly --standalone -d yourdomain.com
```

2. **Configure SSL in nginx:**
```bash
# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Update nginx configuration
# Uncomment HTTPS server block in nginx/nginx.conf
```

3. **Update environment:**
```env
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

## 📊 Monitoring and Observability

### Prometheus Metrics

The platform exposes metrics for:
- API request rates and latencies
- Database connection pools
- Celery task execution
- Agent performance metrics
- Memory usage and learning analytics

### Grafana Dashboards

Pre-configured dashboards for:
- Application performance monitoring
- Infrastructure metrics
- Business metrics (task completion rates, user engagement)
- Agent performance and learning trends

### Log Management

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Log files location
./logs/
├── backend.log
├── celery.log
└── nginx/
    ├── access.log
    └── error.log
```

## 🔄 Backup and Recovery

### Automated Backups

```bash
# Setup automated daily backups
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * cd /path/to/agentic-framework && ./scripts/manage.sh backup
```

### Manual Backup

```bash
# Create backup
./scripts/manage.sh backup

# Backup with custom name
docker-compose exec -T postgres pg_dump -U postgres agentic_platform > custom_backup.sql
```

### Recovery

```bash
# Restore from backup
./scripts/manage.sh restore backup_20240121_020000.sql

# Full disaster recovery
./scripts/deploy.sh
./scripts/manage.sh restore latest_backup.sql
```

## 🚀 Production Deployment

### Server Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB SSD storage
- Ubuntu 20.04+ or similar

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ SSD storage
- Load balancer for high availability

### Production Checklist

- [ ] Configure SSL certificates
- [ ] Set secure environment variables
- [ ] Configure firewall rules
- [ ] Setup automated backups
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedures
- [ ] Setup log rotation
- [ ] Configure rate limiting
- [ ] Setup health checks
- [ ] Configure auto-scaling (if using cloud)

### Cloud Deployment

#### AWS ECS/Fargate
```bash
# Build and push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t agentic-backend -f Dockerfile.backend .
docker tag agentic-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/agentic-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/agentic-backend:latest
```

#### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy agentic-backend --image gcr.io/project-id/agentic-backend --platform managed
```

#### Azure Container Instances
```bash
# Deploy to Azure
az container create --resource-group myResourceGroup --name agentic-platform --image myregistry.azurecr.io/agentic-backend
```

## 🐛 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Rebuild images
./scripts/manage.sh build
```

**Database connection errors:**
```bash
# Check database health
./scripts/manage.sh health

# Reset database
./scripts/manage.sh db-reset
```

**API key errors:**
```bash
# Verify environment variables
docker-compose exec backend env | grep API_KEY

# Update .env file and restart
./scripts/manage.sh restart backend
```

### Performance Issues

**High memory usage:**
```bash
# Check resource usage
docker stats

# Reduce Celery workers
# Edit docker-compose.yml: --concurrency=2
```

**Slow API responses:**
```bash
# Check backend logs
./scripts/manage.sh logs backend

# Monitor metrics
# Access Grafana at http://localhost:3001
```

### Log Analysis

```bash
# Search for errors
./scripts/manage.sh logs backend | grep ERROR

# Monitor real-time logs
./scripts/manage.sh logs -f

# Check specific timeframe
docker-compose logs --since="2024-01-21T10:00:00" backend
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review service logs: `./scripts/manage.sh logs`
3. Verify environment configuration
4. Check system requirements

## 🔄 Updates and Maintenance

### Updating the Platform

```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
./scripts/deploy.sh

# Run any new migrations
./scripts/manage.sh db-migrate
```

### Regular Maintenance

- **Weekly**: Review logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate API keys and secrets
- **Annually**: Update SSL certificates

---

**🎉 Your AI Consultancy Platform is now ready for production!**

Access your platform at the configured URLs and start leveraging the power of AI-driven consultancy automation.
