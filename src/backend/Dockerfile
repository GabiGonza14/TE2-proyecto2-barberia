FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src/backend ./src/backend
COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[test]"

EXPOSE 8000

# Aplica las migraciones pendientes (idempotente) antes de arrancar la API.
CMD ["sh", "-c", "cd src/backend && alembic upgrade head && cd /app && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
