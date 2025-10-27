FROM postgres:15-alpine

ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB
ENV POSTGRES_USER=${POSTGRES_USER:-versionminus}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-versionminuspwd}
ENV POSTGRES_DB=${POSTGRES_DB:-versionminus}

## Install build deps and Python + Alembic dependencies
RUN apk add --no-cache python3 py3-pip build-base postgresql-dev

WORKDIR /app

# Copy dependency list first for better layer caching
COPY src/versionminus/db/python-requirements.txt ./versionminus/db/python-requirements.txt

# Install Python dependencies system-wide (using --break-system-packages due to PEP 668 on Alpine)
RUN python3 -m pip install --upgrade pip --break-system-packages \
 && pip install --no-cache-dir --break-system-packages -r ./versionminus/db/python-requirements.txt \
 && rm -rf /root/.cache/pip

# Copy application modules needed for migrations
COPY src/versionminus/alembic.ini ./alembic.ini
COPY src/versionminus/alembic ./versionminus/alembic
COPY src/versionminus/core ./versionminus/core
COPY src/versionminus/db ./versionminus/db
COPY src/versionminus/schemas ./versionminus/schemas
COPY src/versionminus/repositories ./versionminus/repositories
COPY src/versionminus/services ./versionminus/services
COPY src/versionminus/__init__.py ./versionminus/__init__.py

# Set PYTHONPATH so alembic env imports work
ENV PYTHONPATH=/app
RUN mkdir -p /docker-entrypoint-initdb.d /app/bin

COPY src/versionminus/db/bin/run_with_migrations.sh /app/bin/run_with_migrations.sh
RUN chmod +x /app/bin/run_with_migrations.sh

# Expose the standard Postgres port
EXPOSE 5432

# Use wrapper that invokes original entrypoint then migrations (idempotent)
ENTRYPOINT ["/app/bin/run_with_migrations.sh"]
