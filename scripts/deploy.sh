#!/bin/bash

# AI Consultancy Platform Deployment Script
# This script handles the complete deployment of the platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Check environment file
check_environment() {
    print_status "Checking environment configuration..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.template .env
        print_warning "Please edit .env file with your actual configuration values before proceeding."
        print_warning "Required: OPENAI_API_KEY, SECRET_KEY, and database passwords"
        read -p "Press Enter after updating .env file..."
    fi
    
    # Check for critical environment variables
    source .env
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
        print_error "OPENAI_API_KEY is not set in .env file"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your_super_secret_jwt_key_change_this_in_production_minimum_32_characters" ]; then
        print_error "SECRET_KEY is not set in .env file"
        exit 1
    fi
    
    print_success "Environment configuration check passed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads
    mkdir -p logs
    mkdir -p nginx/ssl
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    print_success "Directories created"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    print_status "Building services sequentially to avoid Docker daemon issues..."
    docker-compose build --no-cache backend
    docker-compose build --no-cache celery_worker
    docker-compose build --no-cache celery_beat
    docker-compose build --no-cache frontend

    print_status "Starting all services from pre-built images..."
    docker-compose up -d --no-build --remove-orphans
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    if docker-compose ps | grep -q "unhealthy\|Exit"; then
        print_error "Some services are not healthy. Check logs:"
        docker-compose logs --tail=50
        exit 1
    fi
    
    print_success "Core services deployed successfully"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for database to be ready
    docker-compose exec backend python -c "
import time
import psycopg2
from src.core.config import settings

for i in range(30):
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.close()
        print('Database is ready')
        break
    except:
        print(f'Waiting for database... ({i+1}/30)')
        time.sleep(2)
else:
    raise Exception('Database not ready after 60 seconds')
"
    
    # Run Alembic migrations
    docker-compose exec backend alembic upgrade head
    
    print_success "Database migrations completed"
}

# Start monitoring (optional)
start_monitoring() {
    if [ "$1" = "--with-monitoring" ]; then
        print_status "Starting monitoring services..."
        docker-compose --profile monitoring up -d prometheus grafana
        print_success "Monitoring services started"
        print_status "Grafana available at: http://localhost:3001"
        print_status "Prometheus available at: http://localhost:9090"
    fi
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check backend health
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend is healthy"
    else
        print_error "Backend health check failed"
        exit 1
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend health check failed"
        exit 1
    fi
    
    print_success "All health checks passed"
}

# Show deployment info
show_deployment_info() {
    print_success "🎉 Deployment completed successfully!"
    echo
    print_status "Service URLs:"
    echo "  Frontend:    http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs:    http://localhost:8000/docs"
    echo
    print_status "Useful commands:"
    echo "  View logs:           docker-compose logs -f"
    echo "  Stop services:       docker-compose down"
    echo "  Restart services:    docker-compose restart"
    echo "  Update services:     ./scripts/deploy.sh"
    echo
    if [ "$1" = "--with-monitoring" ]; then
        echo "  Monitoring:"
        echo "    Grafana:         http://localhost:3001"
        echo "    Prometheus:      http://localhost:9090"
        echo
    fi
}

# Main deployment function
main() {
    print_status "🚀 Starting AI Consultancy Platform deployment..."
    echo
    
    check_prerequisites
    check_environment
    create_directories
    deploy_services
    run_migrations
    start_monitoring "$1"
    health_check
    show_deployment_info "$1"
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "AI Consultancy Platform Deployment Script"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --with-monitoring    Deploy with Prometheus and Grafana monitoring"
        echo "  --help, -h          Show this help message"
        echo
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac
