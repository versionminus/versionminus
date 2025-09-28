# Development environment
FROM ghcr.io/diogobaltazar/licodex-devcontainer-tools:1.0.0

LABEL version="1.0.0"

# Define build-time arguments
ARG USRID
ARG USRNAME
ARG WORKSPACE=/workspace

# Set environment variables
ENV USRID=${USRID}
ENV USRNAME=${USRNAME}
ENV PATH="/home/$USRNAME/.local/bin:$PATH"

## ------------------------------------------------------------------
## System user (done early so later layers can cache if deps unchanged)
## ------------------------------------------------------------------
RUN useradd --uid $USRID --create-home -s /bin/bash $USRNAME \
    && usermod -aG sudo,docker $USRNAME \
    && echo "$USRNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

## ------------------------------------------------------------------
## Python runtime & build tooling
## Keep this separate from requirements so it rarely rebuilds.
## ------------------------------------------------------------------
RUN apt update \
    && apt install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-dev \
    build-essential git \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off

## ------------------------------------------------------------------
## Python dependencies (layer invalidates only when requirements change)
## We copy ONLY requirement files to maximize cache hits.
## ------------------------------------------------------------------
COPY src/licodex/core/python-requirements.txt /tmp/requirements/core.txt
COPY src/licodex/api/python-requirements.txt /tmp/requirements/api.txt
COPY src/licodex/db/python-requirements.txt /tmp/requirements/pg.txt
COPY src/licodex/models/python-requirements.txt /tmp/requirements/model.txt
COPY src/licodex/alembic/python-requirements.txt /tmp/requirements/alembic.txt
COPY src/licodex/repositories/python-requirements.txt /tmp/requirements/repositories.txt
COPY src/licodex/schemas/python-requirements.txt /tmp/requirements/schemas.txt
COPY src/licodex/services/python-requirements.txt /tmp/requirements/services.txt
COPY tests/python-requirements.txt /tmp/requirements/tests.txt

RUN set -eux; \
    for f in /tmp/requirements/*.txt; do \
    echo "Installing $f"; \
    pip3 install --no-cache-dir -r "$f"; \
    done; \
    rm -rf /root/.cache/pip

## ------------------------------------------------------------------
## Workspace directory (mounted at runtime by devcontainer)
## ------------------------------------------------------------------
RUN mkdir -p ${WORKSPACE} \
    && chown ${USRNAME}:${USRNAME} ${WORKSPACE}

WORKDIR ${WORKSPACE}

USER $USRNAME
