FROM python:3.11-slim

# Set environment variables
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Create data directory for SQLite database
RUN mkdir /app/data

# Create a non-root user and set permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/data

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

# Create and activate virtual environment
RUN uv venv $VIRTUAL_ENV

# Copy the rest of the application
COPY . .

# Install dependencies using uv in the virtual environment
RUN uv sync

# Expose port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
