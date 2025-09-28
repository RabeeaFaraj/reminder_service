#!/bin/bash

# Wekan Reminder Service Startup Script
# This script helps you get started with the reminder service

echo "🚀 Starting Wekan Reminder Service Setup"
echo "========================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy and configure the .env file with your credentials:"
    echo "   - Wekan username and password"
    echo "   - Gmail credentials (use App Password)"
    echo "   - Receiver email address"
    echo ""
    echo "Refer to README.md for detailed setup instructions."
    exit 1
fi

echo "✅ .env file found"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check Wekan
if curl -s http://localhost:80 > /dev/null; then
    echo "✅ Wekan is running at http://localhost:80"
else
    echo "⚠️  Wekan might still be starting up at http://localhost:80"
fi

# Check Reminder Service
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Reminder Service is running at http://localhost:8000"
    echo "📚 API Documentation available at http://localhost:8000/docs"
else
    echo "⚠️  Reminder Service might still be starting up at http://localhost:8000"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Open Wekan at http://localhost:80 and create an account"
echo "2. Create a board and add cards with due dates"
echo "3. Test the reminder service:"
echo "   curl -X POST http://localhost:8000/test/email"
echo "   curl -X POST http://localhost:8000/test/wekan"
echo "   curl -X POST http://localhost:8000/reminders/run"
echo ""
echo "📋 View logs with: docker-compose logs -f reminder-service"
echo "🛑 Stop services with: docker-compose down"