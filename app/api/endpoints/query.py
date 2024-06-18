from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas import query_schema, user_schema
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils import oauth2
import app.crud.query as query

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.post("/chat", response_model=query_schema.QueryBase)
def chat(chat: query_schema.QueryCreate, db: Session = Depends(get_db)):
    return query.create_query(db, chat)


@router.get(
    "/history/{user_id}/{limit}", response_model=List[query_schema.QueryResponse]
)
def get_history(
    user_id: int,
    limit: int,
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(oauth2.get_current_user),
):
    return query.get_history(db, user_id, limit)
