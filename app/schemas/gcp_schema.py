from typing import List, Optional
from pydantic import BaseModel

class StorageBase(BaseModel):
    user_id: int
    username: str

class StorageCreate(StorageBase):
    filename: str

class StorageResponse(BaseModel):
    user_id: int
    message: str
    response: str

class VectorStore(BaseModel):
    id: int
    name: str
    email: str
    vectorstore: bool