#!/bin/bash

echo "Starting FINS.."
cd "$(dirname "$(readlink -f "$0")")" || exit 1


poetry run ipython -i terminal.py
