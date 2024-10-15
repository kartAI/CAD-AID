FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc file
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /training

# Copy requirements.txt file into the container
COPY requirements.txt /training/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the training directory into the container
COPY train_yolo.py /training/

CMD ["python", "train_yolo.py"]