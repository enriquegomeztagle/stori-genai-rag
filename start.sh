#!/bin/bash

echo "🚀 Starting Stori GenAI RAG Challenge..."

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your AWS credentials before continuing"
    echo "   Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    read -p "Press Enter after updating .env file..."
fi

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it and try again."
    exit 1
fi

echo "🔧 Building and starting services..."
docker compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking service health..."

if curl -f http://localhost:8000/api/v1/health/health > /dev/null 2>&1; then
    echo "✅ Backend API is running at http://localhost:8000"
    echo "📚 API Documentation: http://localhost:8000/docs"
else
    echo "❌ Backend API is not responding"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "❌ Frontend is not responding"
fi

if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding"
fi

echo ""
echo "🎉 Stori GenAI RAG Challenge is ready!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:3000/health"
echo ""
echo "💡 To stop the services, run: docker compose down"
echo "💡 To view logs, run: docker compose logs -f" 
