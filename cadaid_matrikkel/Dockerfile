
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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

RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-nor \
    libtesseract-dev 


COPY . /app/

RUN mkdir -p /app/upload_files /app/

EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]