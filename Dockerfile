FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (cache layer)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy source
COPY src/ src/
COPY alembic.ini ./
COPY alembic/ alembic/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "mahmoney.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
