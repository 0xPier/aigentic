#!/bin/bash

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.template .env
    echo "Please edit the .env file with your actual configuration"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
export $(grep -v '^#' .env | xargs)

echo "Environment setup complete!"
