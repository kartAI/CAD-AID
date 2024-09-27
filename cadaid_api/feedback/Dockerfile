FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc file
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs /app/temp_files /app/static/uploads

# Install Python dependencies
COPY ../shared/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application files
COPY ../shared/ /app/shared
COPY . /app/feedback

# Expose port for the API
EXPOSE 80

# Command to run the application with uvicorn
CMD ["uvicorn", "feedback.main:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "debug", "--reload"]
