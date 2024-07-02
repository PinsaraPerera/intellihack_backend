from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class QueryBase(BaseModel):
    user_id: int
    response: str
    date_created: datetime

class QueryCreate(BaseModel):
    user_id: int
    username: str
    message: str
    history: Optional[str] = None

class QueryGraphGenerate(BaseModel):
    user_id: int
    username: str
    message: str
    difficulty: Optional[int] = None

class QuerySummaryGenerate(QueryGraphGenerate):
    pass

class QueryResponse(BaseModel):
    message: str
    response: str
    date_created: datetime

class CustomResponse(BaseModel):
    user_id: int
    response: Dict[str, Optional[str]]
    date_created: datetime = Field(default_factory=datetime.utcnow)

class QuizCreate(BaseModel):
    user_id: int
    username: str
    no_of_questions: int
    topic: Optional[str] = None

class Question(BaseModel):
    question: str
    options: List[str]
    correct: str

class Response(BaseModel):
    questions: List[Question]

class QuizBase(BaseModel):
    user_id: int
    response: Response
    date_created: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        protected_namespaces = ()
