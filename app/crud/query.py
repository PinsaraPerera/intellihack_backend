from sqlalchemy.orm import Session
import app.models.query as query
from app.schemas import query_schema
from datetime import datetime
from fastapi import HTTPException, status, Request
from app.core.qa_model import final_result as qa_final_result
from app.core.graph_model import final_result as graph_final_result
from app.core.summarise_model import final_result as summary_final_result
from app.quizGeneratingAgent.main import main as quiz_main
import json

def create_query(db: Session, chat: query_schema.QueryCreate, request: Request):

    response = qa_final_result(
        chat.message,
        chat.history,
        request,
        chat.username,
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    new_query = query.Query(
        user_id=chat.user_id,
        message=chat.message,
        response=response,
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    return new_query


def generate_graph_notation(
    db: Session, chat: query_schema.QueryGraphGenerate, request: Request
):
    response = graph_final_result(chat.message, chat.difficulty, request)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    new_query = query.Query(
        user_id=chat.user_id,
        message=chat.message,
        response=response,
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    return new_query


def generate_summary(
    db: Session, chat: query_schema.QuerySummaryGenerate, request: Request
):
    response = summary_final_result(chat.message, chat.difficulty, request)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    new_query = query.Query(
        user_id=chat.user_id,
        message=chat.message,
        response=response,
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    return new_query

def generate_summary_and_graph(db: Session, chat: query_schema.QuerySummaryGenerate, request: Request):
    summary = summary_final_result(chat.message, chat.difficulty, request)
    graph_notation = graph_final_result(chat.message, chat.difficulty, request)

    if not summary or not graph_notation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )
    
    new_query = query.Query(
        user_id=chat.user_id,
        message=chat.message,
        response=summary + graph_notation,
    )

    db.add(new_query)
    db.commit()
    db.refresh(new_query)
    
    response = query_schema.CustomResponse(
        user_id=chat.user_id,
        message=chat.message,
        response={
            "summary": summary,
            "graph_notation": graph_notation
        },
        date_created=datetime.utcnow()
    )

    return response




def get_history(db: Session, user_id: int, limit: int):
    history = (
        db.query(query.Query).filter(query.Query.user_id == user_id).limit(limit).all()
    )
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History for user with id {user_id} not found",
        )
    return history

def create_quiz(chat: query_schema.QuizCreate, request: Request):

    response = quiz_main(no_of_questions=chat.no_of_questions, request=request, user_email=chat.username)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    if isinstance(response, str):
        response = json.loads(response)

    questions_data = response.get("questions", [])

    response_model = query_schema.Response(
        questions=questions_data
    )

    questions = query_schema.QuizBase(
        user_id=chat.user_id,
        response=response_model,
        date_created=datetime.utcnow()
    )

    return questions