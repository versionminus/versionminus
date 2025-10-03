.PHONY: help dev lint format type test migrate install run pr smoke smoke-populate

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


#  make smoke-populate clean_before=1 clean_after=1 threads=2 messages=3
#  Purpose: run the standalone smoke population script (devtools/bin/smoke.sh)
#           which ensures users/threads/messages exist (optionally cleans).
#  Variables (all optional):
#    clean_before=1        -> pass --clean-before (delete existing smoke data first)
#    clean_after=1         -> pass --clean-after  (cleanup after successful run)
#    threads=<N>           -> export THREADS_PER_USER
#    messages=<N>          -> export MESSAGES_PER_THREAD
smoke-populate:
	@flags=""; \
	[ "$(clean_before)" = "1" ] && flags="$$flags --clean-before"; \
	[ "$(clean_after)" = "1" ] && flags="$$flags --clean-after"; \
	env_vars=""; \
	[ -n "$(threads)" ] && env_vars="$$env_vars THREADS_PER_USER=$(threads)"; \
	[ -n "$(messages)" ] && env_vars="$$env_vars MESSAGES_PER_THREAD=$(messages)"; \
	echo "Running smoke.sh with flags: '$$flags' and env: '$$env_vars'"; \
	eval "$$env_vars devtools/bin/smoke.sh $$flags"

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
