# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for Python libraries
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libpng-dev libffi-dev build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install required Python libraries
RUN pip install --no-cache-dir pillow requests beautifulsoup4 matplotlib pandas numpy yfinance

CMD ["python", "stock-screener.py"]
