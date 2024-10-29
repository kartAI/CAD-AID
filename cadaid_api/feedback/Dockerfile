FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc file
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/shared

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the shared directory before the volume is mounted
COPY shared/ /app/shared

# Create logs directory
RUN mkdir -p /app/logs /app/temp_files /app/static/uploads

# Install Python dependencies
COPY shared/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy only the necessary application files
COPY feedback/src /app/src

# Expose port for the API
EXPOSE 8001

# Command to run the application with uvicorn
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "debug"]
