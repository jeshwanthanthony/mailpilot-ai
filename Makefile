.PHONY: install dev-api dev-web dev-intelligence lint test test-backend test-java build

install:
	python3 -m venv backend/venv
	backend/venv/bin/pip install -r backend/requirements-dev.txt
	npm --prefix frontend ci
	mvn -B -q -f intelligence-service/pom.xml dependency:go-offline

dev-api:
	cd backend && venv/bin/uvicorn main:app --reload

dev-web:
	npm --prefix frontend run dev

dev-intelligence:
	mvn -f intelligence-service/pom.xml spring-boot:run

lint:
	cd backend && venv/bin/ruff check .
	cd backend && venv/bin/ruff format --check .
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck

test:
	$(MAKE) test-backend
	$(MAKE) test-java

test-backend:
	cd backend && venv/bin/pytest

test-java:
	mvn -B --no-transfer-progress -f intelligence-service/pom.xml verify

build:
	npm --prefix frontend run build
	mvn -B -q -f intelligence-service/pom.xml -DskipTests package
