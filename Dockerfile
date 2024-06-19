# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    redis-server

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files to the working directory
COPY . .

# Expose the port for FastAPI
EXPOSE 8000

# Copy the entrypoint script
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Command to run the entrypoint script
ENTRYPOINT ["entrypoint.sh"]
