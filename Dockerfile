FROM python:3.13-slim

WORKDIR /

COPY pyproject.toml uv.lock ./

RUN pip install uv

RUN uv sync --frozen

CMD ["uv", "run", "python", "main.py"]
