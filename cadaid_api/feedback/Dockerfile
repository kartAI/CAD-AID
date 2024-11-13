FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/shared

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/metadata_files_store \
    /app/upload_files

WORKDIR /app

# Copy requirements and install dependencies
COPY shared/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY feedback/src /app/src
COPY shared/ /app/shared

EXPOSE 8001

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
