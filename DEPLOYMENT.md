# AI Consultancy Platform - Docker Deployment Guide

This guide provides comprehensive instructions for deploying the AI Consultancy SaaS platform using Docker containers.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- At least 8GB RAM and 20GB disk space
- Git
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
# Deploy the platform
docker-compose up -d --build
```

### 4. Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

### Services Overview

| Service | Purpose | Port | Health Check |
|---|---|---|---|
| `postgres` | PostgreSQL database | 5432 | `pg_isready` |
| `redis` | Celery broker/cache | 6379 | `redis-cli ping` |
| `backend` | FastAPI application | 8000 | `/health` endpoint |
| `celery_worker` | Background task processor | - | Process monitoring |
| `celery_beat` | Task scheduler | - | Process monitoring |
| `frontend` | React application | 3000 | HTTP response |
| `nginx` | Reverse proxy | 80/443 | HTTP response |
| `prometheus` | Metrics collection | 9090 | `monitoring` profile |
| `grafana` | Metrics visualization | 3001 | `monitoring` profile |


## 🔧 Management Commands

### Service Management

```bash
# Start services in production mode
docker-compose up -d

# Start services in development mode
docker-compose -f docker-compose.dev.yml up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart [service-name]

# View service status
docker-compose ps
```

### Development Tools

```bash
# View logs
docker-compose logs -f [service-name]

# Open shell in container
docker-compose exec backend /bin/bash

# Run tests
docker-compose exec backend pytest
```

### Database Management

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Reset database (WARNING: destroys data)
docker-compose down -v --rmi all
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

1.  **Obtain SSL certificates:** Use Let's Encrypt or another provider.
2.  **Configure SSL in nginx:** Update `nginx/nginx.conf` with your certificate paths.
3.  **Update environment:** Set `SSL_CERT_PATH` and `SSL_KEY_PATH` in your `.env` file.


## 📊 Monitoring and Observability

The platform exposes metrics for Prometheus and includes pre-configured Grafana dashboards. To enable monitoring:

```bash
docker-compose --profile monitoring up -d
```

- **Grafana**: `http://localhost:3001` (admin/admin)
- **Prometheus**: `http://localhost:9090`


## 🔄 Backup and Recovery

### Manual Backup

```bash
# Create backup
docker-compose exec -T postgres pg_dump -U postgres agentic_platform > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Recovery

```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres agentic_platform < backup_file.sql
```

## 🚀 Production Deployment Checklist

- [ ] Configure SSL certificates
- [ ] Set secure environment variables
- [ ] Configure firewall rules
- [ ] Setup automated backups
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedures
- [ ] Setup log rotation
- [ ] Configure rate limiting

## 🐛 Troubleshooting

### Common Issues

-   **Services won't start:** Check `docker-compose logs` for errors.
-   **Database connection errors:** Verify `DATABASE_URL` and that the `postgres` container is healthy.
-   **API key errors:** Ensure API keys in `.env` are correct and the `backend` service was restarted after changes.

---

**🎉 Your AI Consultancy Platform is now ready for production!**
