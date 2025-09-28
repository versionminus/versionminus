FROM postgres:15-alpine

ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB
ENV POSTGRES_USER=${POSTGRES_USER:-licodex}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-licodexpwd}
ENV POSTGRES_DB=${POSTGRES_DB:-licodex}

## Install build deps and Python + Alembic dependencies
RUN apk add --no-cache python3 py3-pip build-base postgresql-dev

WORKDIR /app

# Copy dependency list first for better layer caching
COPY src/licodex/db/python-requirements.txt ./licodex/db/python-requirements.txt

# Install Python dependencies system-wide (using --break-system-packages due to PEP 668 on Alpine)
RUN python3 -m pip install --upgrade pip --break-system-packages \
 && pip install --no-cache-dir --break-system-packages -r ./licodex/db/python-requirements.txt \
 && rm -rf /root/.cache/pip

# Copy application modules needed for migrations
COPY src/licodex/alembic.ini ./alembic.ini
COPY src/licodex/alembic ./licodex/alembic
COPY src/licodex/core ./licodex/core
COPY src/licodex/db ./licodex/db
COPY src/licodex/models ./licodex/models
COPY src/licodex/schemas ./licodex/schemas
COPY src/licodex/repositories ./licodex/repositories
COPY src/licodex/services ./licodex/services
COPY src/licodex/__init__.py ./licodex/__init__.py

# Set PYTHONPATH so alembic env imports work
ENV PYTHONPATH=/app
RUN mkdir -p /docker-entrypoint-initdb.d /app/bin

# Script 00 - derive Postgres env vars from config (exec on first init only)
COPY src/licodex/db/bin/00_config_export.sh /docker-entrypoint-initdb.d/00_config_export.sh
RUN chmod +x /docker-entrypoint-initdb.d/00_config_export.sh

COPY src/licodex/db/bin/run_with_migrations.sh /app/bin/run_with_migrations.sh
RUN chmod +x /app/bin/run_with_migrations.sh

# Expose the standard Postgres port
EXPOSE 5432

# Use wrapper that invokes original entrypoint then migrations (idempotent)
ENTRYPOINT ["/app/bin/run_with_migrations.sh"]
