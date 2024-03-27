FROM python:3.12

RUN pip install --upgrade pip

WORKDIR /code
# COPY ./requirements.txt /code/requirements.txt
# RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install fastapi
RUN pip install "uvicorn[standard]"
RUN pip install opencv-python
RUN pip install ultralytics
RUN pip install easyocr
RUN pip install pdf2image
RUN pip install pathlib
RUN pip install regex
RUN pip install python-multipart
COPY . .

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]