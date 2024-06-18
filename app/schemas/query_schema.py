from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class QueryBase(BaseModel):
    user_id: int
    message: str
    response: str
    date_created: datetime

class QueryCreate(BaseModel):
    user_id: int
    message: str
    history: Optional[str] = None

class QueryResponse(BaseModel):
    message: str
    response: str
    date_created: datetime