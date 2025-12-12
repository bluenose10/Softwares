# Media Toolkit - Production Dockerfile with FFmpeg

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY static ./static
COPY templates ./templates

# Create directories for uploads and outputs
RUN mkdir -p uploads outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0

# Expose port (Render will set PORT dynamically)
EXPOSE 10000

# Health check (using dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; import requests; port = os.getenv('PORT', '8000'); requests.get(f'http://localhost:{port}/health')" || exit 1

# Run the application (use PORT from environment, default to 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
