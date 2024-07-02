from fastapi import FastAPI, Request, Response
import uuid
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.base import Base
from app.db.session import engine
from app.api.endpoints import authentication, users, query, train, gcp
import aioredis
from app.core.config import redis_client
from logging_config import logger

# class RedisSessionMiddleware(SessionMiddleware):
#     def __init__(self, app, secret_key: str, redis_client):
#         super().__init__(app, secret_key=secret_key)
#         self.redis_client = redis_client

#     async def dispatch(self, request: Request, call_next):
#         session_id = request.cookies.get("session_id")
#         if not session_id:
#             session_id = str(uuid.uuid4())
#             request.state.session_id = session_id
#             response = await call_next(request)
#             response.set_cookie(key="session_id", value=session_id, httponly=True)
#             await self.redis_client.setex(
#                 session_id, 3600, ""
#             )  # Set session with TTL of 1 hour
#             return response
#         else:
#             request.state.session_id = session_id
#             response = await call_next(request)
#             return response

class RedisSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str, redis_client):
        super().__init__(app)
        self.secret_key = secret_key
        self.redis_client = redis_client

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        print(request.cookies)
        if session_id:
            request.state.session_id = session_id
            logger.info(f"Existing session_id: {session_id}")
        else:
            session_id = str(uuid.uuid4())
            request.state.session_id = session_id
            logger.info(f"New session_id created: {session_id}")
            await self.redis_client.setex(session_id, 3600, "")  # Set session with TTL of 1 hour

        response = await call_next(request)
        if not request.cookies.get("session_id"):
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                samesite="None",  
                secure=True  # Secure only if using HTTPS
            )
            logger.info(f"Set-Cookie header added with session_id: {session_id}")

        return response

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "https://intellihack-web-cloud-run-rcbmvyttca-uc.a.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(
    RedisSessionMiddleware, secret_key="!secret", redis_client=redis_client
)

Base.metadata.create_all(bind=engine)

app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(query.router)
app.include_router(gcp.router)

@app.get("/")
async def read_root(request: Request):
    session_id = getattr(request.state, "session_id", None)
    return {"message": f"Hello, your session ID is {session_id}"}