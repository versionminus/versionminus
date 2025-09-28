.PHONY: dev lint format type test migrate

PYTHON=python
APP_MODULE=licodex.main:app

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

run:
	uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

dev: install run

lint:
	ruff check src/

format:
	ruff format src/

type:
	mypy src/licodex

test:
	pytest -q
