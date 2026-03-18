# Use a slim Python image for the build stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app/src

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project files
COPY pyproject.toml uv.lock ./
COPY tbank_converter/ ./tbank_converter/
COPY tg_bot/ ./tg_bot/
COPY configs/ ./configs/

# Install dependencies using uv
RUN uv sync --frozen --no-dev --no-install-project

# Final stage
FROM python:3.11-slim-bookworm

WORKDIR /app/src

# Copy the virtualenv and code from builder
COPY --from=builder /app/src /app/src

# Set environment variables
ENV PATH="/app/src/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Command to run the bot
CMD ["python", "tg_bot/main.py"]
