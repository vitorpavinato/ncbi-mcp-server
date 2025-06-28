# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./
COPY README.md ./

# Configure poetry: don't create virtual env, install dependencies only
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

# Copy application code
COPY src/ ./src/

# Now install the current project
RUN poetry install --only-root

# Create cache directory
RUN mkdir -p .cache

# Set default environment variables for easier usage
ENV NCBI_EMAIL="" \
    NCBI_API_KEY="" \
    LOG_LEVEL="INFO" \
    PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (though MCP typically uses stdio)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.ncbi_mcp_server.server import ncbi_client; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "src.ncbi_mcp_server.server"]
