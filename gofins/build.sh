#!/bin/bash

set -e

# Create bin directory if it doesn't exist
mkdir -p bin

BIN_PATH="bin/gofins"

# Build the binary
echo "Building gofins..."
go build -o $BIN_PATH .

echo "✓ Build complete: $BIN_PATH"

