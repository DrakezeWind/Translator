FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev

ENV ENV=production
EXPOSE 8080

CMD ["uv", "run", "main.py"]
