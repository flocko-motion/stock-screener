#!/bin/bash

# GoFins UI Build Script
# Builds the React app for production and outputs to bin/

echo "Building GoFins UI for production..."
echo ""

cd "$(dirname "$0")"

# Create bin directory if it doesn't exist
mkdir -p bin

# Build the project
npm run build

# Copy built files to bin directory
echo "Copying built files to bin/..."
cp -r dist/* bin/

echo ""
echo "Build complete! Files are in the bin/ directory."
echo "You can serve them with any static file server."
echo ""
echo "Example:"
echo "  cd bin && python3 -m http.server 8080"
echo "  # or"
echo "  cd bin && npx serve ."
