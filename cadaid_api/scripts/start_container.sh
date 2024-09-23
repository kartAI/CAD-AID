#! /bin/bash

# Run ./start_container.sh in git bash terminal

# Container name
CONTAINER_NAME="fastapi_container"

# Start and attach container to terminal
docker start -ai $CONTAINER_NAME