FROM nvidia/cuda:12.6.1-cudnn-runtime-ubuntu22.04

# Set environment variables to prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    poppler-utils \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    gnupg \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs /app/temp_files /app/static/uploads

# Install Python dependencies
COPY ../shared/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Copy only the necessary application files
COPY ../shared/ /app/shared
COPY . /app/detect

# Expose port for the API
EXPOSE 80

# Command to run the application with uvicorn
CMD ["python", "-m", "uvicorn", "detect.main:app", "--host", "0.0.0.0", "--port", "80", "--log-level", "debug", "--reload"]