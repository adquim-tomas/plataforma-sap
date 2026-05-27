FROM python:3.14-slim

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencias primero (caching de Docker)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Código
COPY . .

# Correr como usuario sin privilegios (no root)
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]