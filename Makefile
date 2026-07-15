.PHONY: install dev-api dev-web lint test build

install:
	python3 -m pip install -r backend/requirements-dev.txt
	npm --prefix frontend ci

dev-api:
	cd backend && uvicorn main:app --reload

dev-web:
	npm --prefix frontend run dev

lint:
	cd backend && ruff check .
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck

test:
	cd backend && pytest

build:
	npm --prefix frontend run build
