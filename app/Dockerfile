FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Install locked Python dependencies first for Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy backend, knowledge base policies, and compiled React dashboard
COPY app ./app
COPY policies ./policies
COPY dashboard/dist ./dashboard/dist

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
