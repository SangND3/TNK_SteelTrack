.PHONY: help build up down logs shell migrate makemigrations collectstatic test lint format

# Default
help:
	@echo ""
	@echo "TNK SteelTrack — Available commands:"
	@echo ""
	@echo "  make build           Build Docker images"
	@echo "  make up              Start all services (dev)"
	@echo "  make down            Stop all services"
	@echo "  make logs            Tail logs (all services)"
	@echo "  make shell           Django shell"
	@echo "  make bash            Bash inside backend container"
	@echo "  make migrate         Run migrations"
	@echo "  make mm              Make migrations"
	@echo "  make mm app=<name>   Make migrations for specific app"
	@echo "  make createsuperuser Create Django superuser"
	@echo "  make collectstatic   Collect static files"
	@echo "  make test            Run test suite"
	@echo "  make lint            Ruff lint check"
	@echo "  make format          Ruff format + fix"
	@echo ""

build:
	docker compose build

up:
	docker compose up

upd:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec backend python manage.py shell

bash:
	docker compose exec backend bash

migrate:
	docker compose exec backend python manage.py migrate

mm:
ifdef app
	docker compose exec backend python manage.py makemigrations $(app)
else
	docker compose exec backend python manage.py makemigrations
endif

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput

test:
	docker compose exec backend pytest

test-cov:
	docker compose exec backend pytest --cov --cov-report=html

lint:
	docker compose exec backend ruff check backend/

format:
	docker compose exec backend ruff format backend/
	docker compose exec backend ruff check --fix backend/

# CSS build (Tailwind)
css-watch:
	npx tailwindcss -i ./frontend/static_src/css/main.css -o ./frontend/static_src/css/output.css --watch

css-build:
	npx tailwindcss -i ./frontend/static_src/css/main.css -o ./frontend/static_src/css/output.css --minify
