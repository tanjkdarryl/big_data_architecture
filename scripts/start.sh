#!/bin/bash

# Detect project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    # Script is in root directory
    PROJECT_ROOT="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../docker-compose.yml" ]; then
    # Script is in scripts/ subdirectory
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    echo "ERROR: Could not find docker-compose.yml"
    echo "Please ensure you're running this from the project directory or scripts/ subdirectory"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

echo "🚀 Starting Blockchain Data Ingestion System..."
echo "📁 Working directory: $PROJECT_ROOT"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Please review and modify if needed."
    echo ""
fi

# Start services
echo "Starting Docker containers..."
docker compose up --build -d

echo ""
echo "✓ Services starting..."
echo ""
echo "📊 Dashboard: http://localhost:3001"
echo "🔌 API: http://localhost:8000"
echo "🗄️  ClickHouse: localhost:8123"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
