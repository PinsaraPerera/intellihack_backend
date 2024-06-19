# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the Google application credentials environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/keys/service_account.json

# Create and set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    redis-server

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files to the working directory
COPY . .

# Copy the service account key into the container
COPY gcloud-service-key.json /app/keys/service_account.json

# Expose the port that the app runs on
EXPOSE 8000

# Copy the entrypoint script
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Command to run the entrypoint script
ENTRYPOINT ["entrypoint.sh"]
