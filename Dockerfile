FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv

RUN uv sync --frozen

# Playwright's Python package does not include the browser binary or its
# system libraries. Install both into the image used by the bot.
RUN uv run playwright install --with-deps chromium

COPY . . 

CMD ["uv", "run", "python", "main.py"]
