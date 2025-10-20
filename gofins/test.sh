#!/bin/bash

set -e

echo "Running all tests..."
echo ""

# Run all tests with verbose output
go test -v ./...

echo ""
echo "✓ All tests passed"
