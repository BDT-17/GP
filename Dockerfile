# ==============================================================================
# MASCOT Web Application - Dockerfile
# Multi-Agent Simulated Online Classroom for Active Tutoring
# ==============================================================================

FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install dependencies (cached if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and data assets
COPY server.py .
COPY src/ ./src/
COPY data/ ./data/
COPY static/ ./static/

# Create a non-root user for security best practices
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port (default 8000)
EXPOSE 8000

# Container healthcheck using standard Python library (no curl required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/session').read()" || exit 1

# Start FastAPI application using uvicorn (respecting $PORT if set by cloud platforms)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]

