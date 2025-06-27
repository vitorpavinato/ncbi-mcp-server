#!/bin/bash

# NCBI MCP Server Deployment Script
# Usage: ./deploy.sh [local|docker|production]

set -e

DEPLOYMENT_TYPE=${1:-local}

echo "🚀 Deploying NCBI MCP Server ($DEPLOYMENT_TYPE mode)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

case $DEPLOYMENT_TYPE in
    "local")
        echo "📦 Installing dependencies..."
        poetry install
        
        echo "🧪 Running tests..."
        poetry run python -c "
import asyncio
from src.ncbi_mcp_server.server import cache_stats, search_pubmed

async def test():
    await search_pubmed('test query', max_results=1)
    stats = await cache_stats()
    print(f'✅ Server ready! Cache: {stats}')

asyncio.run(test())
"
        
        echo "✅ Local deployment complete!"
        echo "Run: poetry run python -m src.ncbi_mcp_server.server"
        ;;
        
    "docker")
        echo "🐳 Building Docker image..."
        docker build -t ncbi-mcp-server .
        
        echo "🚀 Starting services with Docker Compose..."
        docker-compose up -d
        
        echo "⏳ Waiting for services to be ready..."
        sleep 10
        
        echo "🧪 Testing container..."
        docker-compose exec ncbi-mcp-server python -c "
import asyncio
from src.ncbi_mcp_server.server import cache_stats

async def test():
    stats = await cache_stats()
    print(f'✅ Container ready! Cache: {stats}')

asyncio.run(test())
"
        
        echo "✅ Docker deployment complete!"
        echo "Server: docker-compose logs -f ncbi-mcp-server"
        echo "Redis UI: http://localhost:8081"
        ;;
        
    "production")
        echo "🏭 Production deployment..."
        
        # Check for production requirements
        if [ ! -f .env.production ]; then
            echo "❌ .env.production file not found!"
            exit 1
        fi
        
        # Copy production config
        cp .env.production .env
        
        # Build optimized image
        docker build -t ncbi-mcp-server:production .
        
        # Deploy with production compose
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        
        echo "✅ Production deployment complete!"
        echo "Monitor: docker-compose logs -f"
        ;;
        
    *)
        echo "❌ Unknown deployment type: $DEPLOYMENT_TYPE"
        echo "Usage: $0 [local|docker|production]"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment successful!"
echo "📖 Check README.md for usage instructions"
