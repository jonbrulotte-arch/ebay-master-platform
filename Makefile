.PHONY: up down build migrate test lint seed test-unit test-cov health

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec backend pytest -v

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend ruff format --check app/

seed:
	docker compose exec backend python -m scripts.seed_fee_schedules
	docker compose exec backend python -m scripts.seed_categories

shell:
	docker compose exec backend python -c "from app.database import *; import asyncio"

backend-shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

test-unit:
	docker compose exec backend pytest tests/test_services/ -v --tb=short

test-cov:
	docker compose exec backend pytest --cov=app --cov-report=term-missing -v

health:
	curl -s http://localhost:8000/health | python3 -m json.tool

flower:
	@echo "Celery Flower UI: http://localhost:5555"
	@open http://localhost:5555 2>/dev/null || xdg-open http://localhost:5555 2>/dev/null || true
