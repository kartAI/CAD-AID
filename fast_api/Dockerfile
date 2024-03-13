FROM python:3.12

RUN pip install --upgrade pip


WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./src /code/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]

# FROM ubuntu:20.04
# RUN apt-get update && apt-get install -y python3.12

# COPY requirements.txt .
# RUN --mount=type=cache,mode=0755,target=/root/.cache pip install -r requirements.txt
# COPY . .
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]