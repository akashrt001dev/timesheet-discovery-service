#!/bin/bash

# Discovery Service (Eureka) - Startup Script

echo "=========================================="
echo "Starting Eureka Discovery Service"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start the server with auto-reload enabled
echo ""
echo "Starting server on http://$EUREKA_INSTANCE_HOSTNAME:$SERVER_PORT"
echo "=========================================="
echo "Auto-reload is enabled - changes will be reloaded automatically"
echo "=========================================="
echo ""

uvicorn app.main:app --host $SERVER_HOST --port $SERVER_PORT --reload --reload-dirs=app

echo ""
echo "=========================================="
echo "Service stopped"
echo "=========================================="
