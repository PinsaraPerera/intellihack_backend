from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.db.base import Base
from app.db.session import engine
from app.api.endpoints import authentication, users, query, train, gcp
from app.core.config import redis_client

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="!secret")

Base.metadata.create_all(bind=engine)

app.include_router(authentication.router)
app.include_router(users.router)
app.include_router(query.router)
# app.include_router(train.router)
app.include_router(gcp.router)
