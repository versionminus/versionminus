FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt update && apt install -y build-essential
COPY src/versionminus/python-requirements.txt /app/requirements.txt
COPY src/versionminus/mcp/python-requirements.txt /app/mcp-requirements.txt

RUN pip install --no-cache-dir -r /app/mcp-requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "versionminus.mcp.main"]

