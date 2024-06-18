from sqlalchemy.orm import Session
import app.models.query as query
from app.schemas import query_schema
from fastapi import HTTPException, status
from app.core.model import final_result



def create_query(db: Session, chat: query_schema.QueryCreate):
    
    response = final_result(chat.message, chat.history)

    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found. Try again later.")

    new_query = query.Query(
        user_id=chat.user_id,
        message=chat.message,
        response=response,
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    return new_query

def get_history(db: Session, user_id: int, limit: int):
    history = db.query(query.Query).filter(query.Query.user_id == user_id).limit(limit).all()
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"History for user with id {user_id} not found")
    return history