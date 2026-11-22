FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY policies ./policies
COPY dashboard/dist ./dashboard/dist
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

EXPOSE 8000

CMD ["./start.sh"]
