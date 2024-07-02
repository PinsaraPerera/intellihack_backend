from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from app.schemas import query_schema, user_schema
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.core.config import redis_client
from app.utils import oauth2
import app.crud.query as query

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.post("/chat", response_model=query_schema.QueryBase)
async def chat(chat: query_schema.QueryCreate, request: Request,  db: Session = Depends(get_db)):
    return await query.create_query(db, chat, request)

@router.post("/quiz", response_model=query_schema.QuizBase)
def quiz(chat: query_schema.QuizCreate, request: Request,  db: Session = Depends(get_db)):
    return query.create_quiz(chat, request)

@router.post("/graphGenerate", response_model=query_schema.QueryBase)
def graphGenerate(chat: query_schema.QueryGraphGenerate, request: Request,  db: Session = Depends(get_db)):
    return query.generate_graph_notation(db, chat, request)

@router.post("/summary", response_model=query_schema.QueryBase)
def summary(chat: query_schema.QuerySummaryGenerate, request: Request,  db: Session = Depends(get_db)):
    return query.generate_summary(db, chat, request)

@router.post("/getBothGraphAndSummary", response_model=query_schema.CustomResponse)
def getBothGraphAndSummary(chat: query_schema.QuerySummaryGenerate, request: Request,  db: Session = Depends(get_db)):
    return query.generate_summary_and_graph(db, chat, request)

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

@router.get("/clear-session")
async def clear_user_session(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session ID found in request")

    try:
        # Check if the session ID exists in Redis
        session_key_index = f"{session_id}_index"
        session_key_metadata = f"{session_id}_metadata"
        if not await redis_client.exists(session_key_index) and not await redis_client.exists(session_key_metadata):
            return {"message": "Session key not found"}

        # Delete the session key
        await redis_client.delete(session_key_index)
        await redis_client.delete(session_key_metadata)
        return {"message": f"Session data cleared for session_id: {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to clear session data")
