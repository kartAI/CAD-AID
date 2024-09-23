#! /bin/bash
CONTAINER_NAME="fastapi_container"
IMAGE_NAME="fastapi_app"

echo "Stopping and removing existing container (if running).."

docker stop $CONTAINER_NAME 2>/dev/null || true

docker rm $CONTAINER_NAME 2>/dev/null || true

echo "Building Docker image.."

docker build -t $IMAGE_NAME .

docker run -d -p 8000:80 --name $CONTAINER_NAME -v $(pwd):/app $IMAGE_NAME
