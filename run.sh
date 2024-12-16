#!/bin/bash

# Define variables
IMAGE="ghcr.io/flocko-motion/stock-screener:latest"

HTML_DIR="/var/www/html/your/output/directory"
API_KEYS_DIR="$HOME/your/path/to/the/api-keys/directory"

# Pull the latest version of the Docker image
echo "Pulling the latest Docker image..."
docker pull $IMAGE

# Run the Docker container
echo "Running the Docker container..."
docker run --rm \
  -v "$HTML_DIR:/app/html" \
  -v "$API_KEYS_DIR:/app/api-keys" \
  $IMAGE

echo "Docker container has finished running."
