FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /frontend
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY policies ./policies
COPY --from=frontend-builder /frontend/dist ./dashboard/dist
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

EXPOSE 8000

CMD ["./start.sh"]