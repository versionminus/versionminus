FROM milvusdb/milvus:v2.4.9

# Build args (deployment metadata)
ARG DEPLOYMENT_ENV=local
ENV DEPLOYMENT_ENV=$DEPLOYMENT_ENV

RUN echo "[INFO] Building versionminus Milvus image for '$DEPLOYMENT_ENV' environment"

USER root
# Use Python 3.11 to support PEP 585 annotations like list[str]
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3.11 python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && python3 --version

# Copy Milvus helper scripts and requirements
COPY src/versionminus/milvus/bin/init.py /init.py
COPY src/versionminus/milvus/python-requirements.txt /python-requirements.txt

# Copy project code (only what we need for settings + milvus helpers)
COPY src/versionminus /opt/versionminus
ENV PYTHONPATH=/opt:$PYTHONPATH

RUN pip3 install --no-cache-dir -r /python-requirements.txt

EXPOSE 19530 9091

# Start Milvus then run initialization (notes collection only)
CMD milvus run standalone & \
    sleep 15 && \
    python3 /init.py && \
    wait
