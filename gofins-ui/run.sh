#!/bin/bash

# GoFins UI Development Server
# Runs the React development server on port 3000

echo "Starting GoFins UI development server..."
echo "Server will be available at: http://localhost:3000"
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
npm run dev
