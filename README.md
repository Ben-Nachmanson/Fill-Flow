# fillflow — Mock trading service

A minimal, deployable example of a mock trading service built with FastAPI, asyncpg, Redis Streams and background workers. Intended as a demo for observability, CI/CD and k8s deployments.

Status: early prototype — API, DB layer, queue, worker, Dockerfile, docker-compose, Alembic migrations, Helm stubs and basic CI are included.

Features
- POST /orders -> enqueue -> worker simulates fill -> persists fills and updates positions
- GET /orders/:id, GET /orders, GET /positions, GET /healthz, /metrics (Prometheus)
- Redis Streams for internal eventing
- Postgres for durable state
- Prometheus instrumentation (basic counters)

Repository layout (important)
- internal/     — api, domain, storage, queue, pricing, metrics
- alembic/      — migrations
- deploy/helm/  — helm chart stubs for trade-svc
- dashboards/   — grafana panel JSON
- .github/workflows — CI
- Dockerfile, docker-compose.yml, Makefile, README.md

Quickstart (local)
Prerequisites: Docker, docker-compose, make

1. Copy example env and customize (do NOT commit secrets):
   cp .env.example .env

2. Start the stack:
   make up

3. Confirm service is healthy:
   curl http://localhost:8000/healthz

4. Create an order:
   curl -X POST http://localhost:8000/orders \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","side":"BUY","qty":1,"price":150}'

5. Check order and positions:
   curl http://localhost:8000/orders/1
   curl http://localhost:8000/positions

Run locally without Docker
1. Create a virtualenv and install deps:
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
2. Start the API:
   make run
3. Start the worker in a separate terminal:
   python -m internal.queue.worker

Database migrations
- Alembic migrations are in `alembic/versions`. Run:
  make migrate

Running tests
- Unit/integration tests with pytest:
  make test

Observability
- Metrics are exposed at /metrics. Dashboards are in `dashboards/grafana.json`.

CI/CD
- GitHub Actions workflows live under `.github/workflows`. CI runs lint and tests; a basic integration job is included.

Development notes / recommendations
- Use Alembic as the canonical schema. Disable schema-on-start in production.
- Do not commit `.env` or secrets. Use GitHub Secrets / SOPS / Vault in CI and k8s.
- Improve CI by running integration tests against docker-compose or Testcontainers and enforce coverage thresholds.

Contributing
- Fork, create a feature branch, add tests, open a PR.

License
- MIT
