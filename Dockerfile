FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN uv sync --frozen --no-dev
RUN chmod +x /app/docker-entrypoint-api.sh /app/docker-entrypoint-cli.sh

ENV PATH="/app/.venv/bin:$PATH"

CMD ["/app/docker-entrypoint-api.sh"]
