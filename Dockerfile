FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE="copy"

COPY ./pyproject.toml ./uv.lock ./
RUN ["uv", "sync", "--frozen", "--no-install-project", "--no-cache", "--no-dev"]

COPY ./ ./

CMD ["uv", "run", "main.py"]
