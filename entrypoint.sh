#!/bin/sh

# Start Redis server
redis-server --port 6379 --bind 0.0.0.0 &

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
