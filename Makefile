.PHONY: help up down build logs shell-backend shell-db migrate makemigrations test lint clean

help:
	@echo "RentTrack — common commands"
	@echo ""
	@echo "  make up              Start all services (Docker)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild containers"
	@echo "  make logs            Tail logs"
	@echo "  make shell-backend   Open Django shell"
	@echo "  make shell-db        Open psql shell"
	@echo "  make migrate         Run DB migrations"
	@echo "  make makemigrations  Create new migrations"
	@echo "  make test            Run backend tests"
	@echo "  make lint            Run ruff"
	@echo "  make clean           Remove volumes and containers"

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

shell-backend:
	docker-compose exec backend python manage.py shell

shell-db:
	docker-compose exec db psql -U renttrack -d renttrack

migrate:
	docker-compose exec backend python manage.py migrate

makemigrations:
	docker-compose exec backend python manage.py makemigrations

createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

test:
	docker-compose exec backend pytest

lint:
	docker-compose exec backend ruff check .
	cd frontend && npm run lint

clean:
	docker-compose down -v
	docker system prune -f
