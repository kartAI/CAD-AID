FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install gcc python3-dev libglib2.0-0 libgl1-mesa-glx jq -y && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY detection/detection_model/ ./detection_model/
    
   
EXPOSE 80

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "80"]