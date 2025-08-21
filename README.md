# trade-svc (FastAPI)

Mock trading service with REST API + background worker, Postgres for state, Redis Streams for the internal queue, and Prometheus metrics.

Quickstart (local):
- Prereqs: Python 3.11+, Docker, Docker Compose
- Copy env: cp .env.example .env
- Start dependencies: docker compose up -d
- Create venv and install deps: make install
- Run API: make run-api
- Run Worker (separate shell): make run-worker

Endpoints:
- POST /orders
- GET /orders/{id}
- GET /positions
- GET /healthz
- GET /metrics (Prometheus)

Environment:
- See .env.example for DB and Redis settings. Defaults work with docker compose.

Notes:
- On API startup, tables are created if not present.
- Orders are accepted and enqueued; the worker simulates fills and updates state.
