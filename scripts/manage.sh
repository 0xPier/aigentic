#!/bin/bash

# AI Consultancy Platform Management Script
# Utility script for common development and production tasks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Show help
show_help() {
    echo "AI Consultancy Platform Management Script"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start [dev|prod]     Start services (default: dev)"
    echo "  stop                 Stop all services"
    echo "  restart [service]    Restart all services or specific service"
    echo "  logs [service]       Show logs for all services or specific service"
    echo "  shell <service>      Open shell in service container"
    echo "  db-migrate          Run database migrations"
    echo "  db-reset            Reset database (WARNING: destroys data)"
    echo "  test                Run test suite"
    echo "  build               Build all images"
    echo "  clean               Clean up containers and images"
    echo "  backup              Backup database"
    echo "  restore <file>      Restore database from backup"
    echo "  status              Show service status"
    echo "  health              Check service health"
    echo
    echo "Examples:"
    echo "  $0 start dev        Start development environment"
    echo "  $0 logs backend     Show backend logs"
    echo "  $0 shell backend    Open shell in backend container"
    echo "  $0 test             Run all tests"
}

# Start services
start_services() {
    local env=${1:-dev}
    
    if [ "$env" = "dev" ]; then
        print_status "Starting development environment..."
        docker-compose -f docker-compose.dev.yml up -d
    else
        print_status "Starting production environment..."
        docker-compose up -d
    fi
    
    print_success "Services started"
}

# Stop services
stop_services() {
    print_status "Stopping services..."
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    print_success "Services stopped"
}

# Restart services
restart_services() {
    local service=$1
    
    if [ -n "$service" ]; then
        print_status "Restarting $service..."
        docker-compose restart "$service"
    else
        print_status "Restarting all services..."
        docker-compose restart
    fi
    
    print_success "Services restarted"
}

# Show logs
show_logs() {
    local service=$1
    
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# Open shell
open_shell() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_error "Service name required"
        exit 1
    fi
    
    print_status "Opening shell in $service..."
    docker-compose exec "$service" /bin/bash
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec backend alembic upgrade head
    print_success "Migrations completed"
}

# Reset database
reset_database() {
    print_warning "This will destroy all data in the database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Resetting database..."
        docker-compose exec backend alembic downgrade base
        docker-compose exec backend alembic upgrade head
        print_success "Database reset completed"
    else
        print_status "Database reset cancelled"
    fi
}

# Run tests
run_tests() {
    print_status "Running test suite..."
    docker-compose exec backend python -m pytest tests/ -v --cov=src --cov-report=term-missing
    print_success "Tests completed"
}

# Build images
build_images() {
    print_status "Building all images..."
    docker-compose build --no-cache
    print_success "Images built"
}

# Clean up
cleanup() {
    print_status "Cleaning up containers and images..."
    
    # Stop and remove containers
    docker-compose down --remove-orphans
    docker-compose -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    read -p "Remove unused volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    print_success "Cleanup completed"
}

# Backup database
backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    print_status "Creating database backup: $backup_file"
    docker-compose exec -T postgres pg_dump -U postgres agentic_platform > "$backup_file"
    print_success "Backup created: $backup_file"
}

# Restore database
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Backup file required"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This will overwrite the current database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Restoring database from: $backup_file"
        docker-compose exec -T postgres psql -U postgres -d agentic_platform < "$backup_file"
        print_success "Database restored"
    else
        print_status "Database restore cancelled"
    fi
}

# Show service status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Health check
health_check() {
    print_status "Checking service health..."
    
    # Check backend
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend: Healthy"
    else
        print_error "Backend: Unhealthy"
    fi
    
    # Check frontend (if running)
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend: Healthy"
    else
        print_warning "Frontend: Not accessible (may not be running)"
    fi
    
    # Check database
    if docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_success "Database: Healthy"
    else
        print_error "Database: Unhealthy"
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis: Healthy"
    else
        print_error "Redis: Unhealthy"
    fi
}

# Main command handler
case "$1" in
    start)
        start_services "$2"
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services "$2"
        ;;
    logs)
        show_logs "$2"
        ;;
    shell)
        open_shell "$2"
        ;;
    db-migrate)
        run_migrations
        ;;
    db-reset)
        reset_database
        ;;
    test)
        run_tests
        ;;
    build)
        build_images
        ;;
    clean)
        cleanup
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    status)
        show_status
        ;;
    health)
        health_check
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
