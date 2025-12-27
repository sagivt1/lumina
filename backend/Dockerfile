FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# Install dependencies first
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy app code
COPY . .

# Run the app
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]