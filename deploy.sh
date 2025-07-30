#!/bin/bash

# AI Agent Platform Deployment Script
# This script helps you deploy the AI Agent Platform

set -e

echo "🚀 AI Agent Platform Deployment Script"
echo "======================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from template"
        echo "⚠️  Please edit .env file with your configuration before continuing"
        echo "   Press Enter when you're ready to continue..."
        read
    else
        echo "❌ .env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Test the application
echo "🧪 Testing the application..."
echo "Testing backend health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

echo "Testing frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

echo "Testing nginx proxy..."
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ Nginx proxy is working"
else
    echo "❌ Nginx proxy is not working"
fi

echo ""
echo "🎉 Deployment completed!"
echo "========================"
echo "Your AI Agent Platform is now running at:"
echo "  🌐 Main Application: http://localhost:8080"
echo "  🖥️  Frontend Direct: http://localhost:3000"
echo "  🔌 Backend API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  📊 View logs: docker-compose logs -f"
echo "  🛑 Stop services: docker-compose down"
echo "  🔄 Restart services: docker-compose restart"
echo "  🧹 Clean up: docker-compose down -v"
echo ""
echo "Happy coding! 🚀" 