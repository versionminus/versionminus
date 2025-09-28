FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement aggregators first for caching
COPY src/licodex/api/python-requirements.txt ./src/licodex/api/python-requirements.txt

RUN pip install --upgrade pip \
    && pip install -r ./src/licodex/api/python-requirements.txt

# Copy project source & packaging metadata
COPY src ./src
COPY setup.py README.md ./

RUN pip install -e .

EXPOSE 8000

ENV LOG_LEVEL=INFO \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Entrypoint uses config module (env vars override defaults) to launch uvicorn
CMD ["python", "-m", "licodex.api.run"]
