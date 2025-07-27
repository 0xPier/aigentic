#!/bin/bash

# Stop and remove all containers
echo "Stopping and removing all containers..."
docker-compose down

# Rebuild the containers
echo "Rebuilding containers..."
docker-compose build --no-cache

# Start the services
echo "Starting services..."
docker-compose up -d

echo "
Services are starting up...

Access the application at: http://localhost:8080

View logs with: docker-compose logs -f
"
