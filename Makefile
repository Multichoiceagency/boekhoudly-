.PHONY: dev-up dev-down dev-logs dev-build frontend-dev backend-dev db-migrate db-reset

dev-up:
	docker compose up -d

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f

dev-build:
	docker compose build

frontend-dev:
	cd frontend && pnpm dev

backend-dev:
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

db-migrate:
	docker compose exec backend alembic upgrade head

db-reset:
	docker compose down -v && docker compose up -d db
