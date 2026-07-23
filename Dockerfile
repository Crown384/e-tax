# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder
WORKDIR /app
ENV POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"
COPY pyproject.toml ./
RUN poetry install --only main --no-root

FROM python:3.13-slim AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    ETAX_STORAGE_DIR=/app/data/generated
COPY --from=builder /app/.venv /app/.venv
COPY app ./app
COPY schemas ./schemas
COPY main.py ./main.py
RUN mkdir -p /app/data/generated
EXPOSE 8000
CMD ["python", "main.py"]
