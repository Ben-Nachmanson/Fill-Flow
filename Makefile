PY?=python3
PIP?=pip3
APP_MODULE=internal.api.app:app

.PHONY: install run-api run-worker fmt lint test compose down

install:
	$(PIP) install -r requirements.txt

run-api:
	uvicorn $(APP_MODULE) --reload --port $${SERVICE_PORT:-8000}

run-worker:
	$(PY) -m internal.queue.worker

fmt:
	$(PY) -m black . || true

lint:
	$(PY) -m flake8 || true

compose:
	docker compose up -d

down:
	docker compose down -v
