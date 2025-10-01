.PHONY: help dev lint format type test migrate install run pr smoke

PYTHON ?= python
APP_MODULE ?= licodex.api.main:app

help:
	@echo "Available targets:"
	@grep -E '^# {2,}make ' Makefile | sed -E 's/^# +//'

run:
	uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

build:
	docker compose build --no-cache

build-api:
	docker compose build --no-cache api

build-db:
	docker compose build --no-cache db

up:
	docker compose up -d

down:
	docker compose down -v

lint:
	ruff check src/licodex

format:
	ruff format src/licodex

type:
	mypy src/licodex

ut:
	pytest -m unit -q

it:
	pytest -m integration -q

smoke:
	pytest -m smoke -q || true
	@echo "Or run devtools/bin/smoke.sh against a running server"

#  make pr title="refactor: api.endpoints, feat: delete, edit user"
#  make pr title="fix: something"  # Provide your PR title via title variable
title ?=
pr:
	@if [ -z "$(title)" ]; then \
		echo "Error: title variable is required"; \
		echo "Usage: make pr title=\"your pr title\""; \
		exit 1; \
	fi; \
	devtools/bin/pr.sh "$(title)"
