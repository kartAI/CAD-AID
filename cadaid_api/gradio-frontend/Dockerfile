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
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/upload_files

WORKDIR /app

# Copy requirements and install dependencies
COPY shared/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gradio-frontend/src /app/src
COPY shared/ /app/shared

RUN pip install --no-cache-dir gradio

EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]
