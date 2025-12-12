FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONOPTIMIZE=1 \
    PYTHONPATH=/app/src


RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-java-common \
    default-jre \
    fonts-liberation \
    fonts-dejavu \
    fonts-noto \
    curl \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev

COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/db \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "src.main", "--reload"]
