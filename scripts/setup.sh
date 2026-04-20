#!/usr/bin/env bash
# One-command setup for fresh checkout
set -e

echo "🏗️  RentTrack — first-time setup"
echo ""

if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ Created .env from .env.example"
else
  echo "✓ .env already exists"
fi

echo ""
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for database..."
sleep 5

echo ""
echo "🔧 Running migrations..."
docker-compose exec backend python manage.py migrate

echo ""
echo "👤 Create a superuser:"
docker-compose exec backend python manage.py createsuperuser

echo ""
echo "✨ All set!"
echo ""
echo "Services running:"
echo "  Backend API  → http://localhost:8000"
echo "  API docs     → http://localhost:8000/api/docs/"
echo "  Django admin → http://localhost:8000/admin/"
echo "  Frontend     → http://localhost:5173"
echo "  Mailhog UI   → http://localhost:8025"
echo ""
echo "Tail logs:    make logs"
echo "Stop all:     make down"
