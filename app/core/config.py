import os
from redis import Redis

# Redis client setup
redis_client = Redis(host='localhost', port=6379, db=0)