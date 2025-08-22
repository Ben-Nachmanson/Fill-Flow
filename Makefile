# Makefile for local dev
.PHONY: up down build run test lint demo migrate cluster-up cluster-down

up:
	docker-compose up -d --build

down:
	docker-compose down -v

build:
	docker build -t trade-svc:local .

run:
	uvicorn internal.api.app:app --reload --host 0.0.0.0 --port 8000

demo: up
	@echo "Service should be available at http://localhost:8000"

test:
	pytest -q

lint:
	flake8

migrate:
	alembic upgrade head

cluster-up:
	k3d cluster create fillflow --api-server-port 6443 -p 30080:80@loadbalancer
	kubectl create namespace trading || true

cluster-down:
	k3d cluster delete fillflow || true
