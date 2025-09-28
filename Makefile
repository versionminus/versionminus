.PHONY: help dev lint format type test migrate install run

PYTHON ?= python
APP_MODULE ?= licodex.api.main:app

help:
	@echo "Available targets:"
	@grep -E '^# {2,}make ' Makefile | sed -E 's/^# +//'

run:
	uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

build:
	docker compose build --no-cache

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

test:
	pytest -q

pr:
	devtools/bin/pr.sh
