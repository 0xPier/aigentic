#!/bin/bash

# Stop any running containers and clean up
echo "Cleaning up existing containers..."
docker stop agentic-db agentic-backend 2>/dev/null
docker rm agentic-db agentic-backend 2>/dev/null

# Start PostgreSQL container
echo "Starting PostgreSQL container..."
docker run --name agentic-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=agentic_framework -p 5433:5432 -d postgres:13-alpine

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until docker exec agentic-db pg_isready -U postgres; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Build the backend image
echo "Building backend image..."
docker build -t agentic-backend -f Dockerfile.backend .

# Run the backend container
echo "Starting backend container..."
docker run -d --name agentic-backend --network host -v $(pwd)/src:/usr/src/app/src -v $(pwd)/logs:/usr/src/app/logs -v $(pwd)/uploads:/usr/src/app/uploads -e DATABASE_URL=postgresql://postgres:postgres@localhost:5433/agentic_framework agentic-backend

# Wait for the backend to start
echo "Waiting for backend to start..."
sleep 5

# Test the API
echo "Testing API endpoints..."

# Test root endpoint
echo -e "\nTesting root endpoint:"
curl -s http://localhost:8000/ | jq .

# Test health check endpoint
echo -e "\nTesting health check:"
curl -s http://localhost:8000/health | jq .

echo -e "\nSetup and testing complete!"
echo "Backend is running at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/docs"
