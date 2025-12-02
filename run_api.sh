#!/bin/bash

# NHL Shots Betting API Startup Script

echo "Starting NHL Shots Betting API..."
echo ""
echo "API will be available at:"
echo "  - Main endpoint: http://localhost:8000"
echo "  - API docs: http://localhost:8000/docs"
echo "  - Health check: http://localhost:8000/health"
echo ""
echo "Default API key: dev-key-123"
echo ""

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the API with hot reload for development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000