FROM python:3.13-slim-bookworm AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv

RUN uv sync --frozen

COPY . . 

FROM base AS runtime

CMD ["uv", "run", "python", "main.py"]

FROM runtime AS bot

# Only the bot posts to Dzen. API and migrations do not need a browser.
RUN uv run playwright install --with-deps chromium
