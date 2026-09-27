.PHONY: install web api worker test schemas
install:
	uv sync --project backend --extra dev --frozen
	cd frontend && npm ci --ignore-scripts
web:
	cd frontend && npm run build
api:
	cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
worker:
	cd backend && python -m app.worker
test: web
	cd backend && python -m pytest --cov=app --cov-report=term-missing
	cd frontend && npm run typecheck
schemas:
	python scripts/export_contracts.py
