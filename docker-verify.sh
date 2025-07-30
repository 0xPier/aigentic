#!/bin/bash

# Quick Docker Configuration Verification Script

echo "🔍 Docker Configuration Verification"
echo "====================================="

# Check Docker and docker-compose
echo "📋 Checking prerequisites..."
docker --version || { echo "❌ Docker not found"; exit 1; }
docker-compose --version || { echo "❌ docker-compose not found"; exit 1; }
echo "✅ Docker and docker-compose are available"

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running"
    exit 1
fi
echo "✅ Docker daemon is running"

# Validate docker-compose.yml
echo "📋 Validating docker-compose.yml..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    docker-compose config
    exit 1
fi

# Check if required files exist
echo "📋 Checking required files..."
required_files=(
    "docker-compose.yml"
    "Dockerfile.backend" 
    "nextjs-frontend/Dockerfile"
    "requirements.txt"
    "nextjs-frontend/package.json"
    ".env"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

# Check environment variables
echo "📋 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check for critical variables
    critical_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
    for var in "${critical_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is configured"
        else
            echo "⚠️  $var is not configured"
        fi
    done
else
    echo "⚠️  .env file not found"
fi

# Check network ports availability
echo "📋 Checking port availability..."
ports=(3000 8000 8080 27017 6379)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
    else
        echo "✅ Port $port is available"
    fi
done

echo ""
echo "🎯 VERIFICATION COMPLETE"
echo "========================"
echo "✅ Your Docker configuration appears to be correct!"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Run: ./docker-test.sh"
echo "2. Or manually: docker-compose up --build"
echo ""
echo "📚 USEFUL COMMANDS:"
echo "- View logs: docker-compose logs [service]"
echo "- Stop all: docker-compose down"
echo "- Rebuild: docker-compose build --no-cache"
echo "- Shell access: docker exec -it [container] bash" 