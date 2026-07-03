FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

RUN chmod +x /app/backend/docker/entrypoint.sh

ENTRYPOINT ["/app/backend/docker/entrypoint.sh"]
