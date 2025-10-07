FROM milvusdb/milvus:v2.3.9

# Build args (deployment metadata)
ARG DEPLOYMENT_ENV=local
ENV DEPLOYMENT_ENV=$DEPLOYMENT_ENV

RUN echo "[INFO] Building licodex Milvus image for '$DEPLOYMENT_ENV' environment"

USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Copy Milvus helper scripts and requirements
COPY src/licodex/milvus/bin/init.py /init.py
COPY src/licodex/milvus/python-requirements.txt /python-requirements.txt

# Copy project code (only what we need for settings + milvus helpers)
COPY src/licodex /opt/licodex
ENV PYTHONPATH=/opt:$PYTHONPATH

RUN pip3 install --no-cache-dir -r /python-requirements.txt

EXPOSE 19530 9091

# Start Milvus then run initialization (notes collection only)
CMD milvus run standalone & \
    sleep 15 && \
    python3 /init.py && \
    wait