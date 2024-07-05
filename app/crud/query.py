from sqlalchemy.orm import Session
import app.models.query as query
from app.schemas import query_schema
from datetime import datetime
from fastapi import HTTPException, status, Request
from app.core.qa_model import final_result as qa_final_result
from app.core.graph_model import final_result as graph_final_result
from app.core.summarise_model import final_result as summary_final_result
from app.quizGeneratingAgent.main import main as quiz_main
from app.core.config import AGENT_SERVICE_URL
import requests
import json

from app.quizGeneratingAgent.createVectorDB import search_vector_db


async def create_query(db: Session, chat: query_schema.QueryCreate, request: Request):

    response = await qa_final_result(
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


def generate_summary_and_graph(
    db: Session, chat: query_schema.QuerySummaryGenerate, request: Request
):
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
        response={"summary": summary, "graph_notation": graph_notation},
        date_created=datetime.utcnow(),
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


# def create_quiz(chat: query_schema.QuizCreate, request: Request):

#     response = quiz_main(
#         no_of_questions=chat.no_of_questions, request=request, user_email=chat.username
#     )

#     if not response:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Response not found. Try again later.",
#         )

#     if isinstance(response, str):
#         response = json.loads(response)

#     questions_data = response.get("questions", [])

#     response_model = query_schema.Response(questions=questions_data)

#     questions = query_schema.QuizBase(
#         user_id=chat.user_id, response=response_model, date_created=datetime.utcnow()
#     )

#     return questions


def create_quiz(chat: query_schema.QuizCreate, request: Request):

    response = requests.post(
        f"{AGENT_SERVICE_URL}/quiz/",
        json={
            "user_id": chat.user_id,
            "username": chat.username,
            "no_of_questions": chat.no_of_questions,
            "topic": chat.topic,
        },
        headers={"Content-Type": "application/json"},
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    response_data = response.json()

    return query_schema.QuizBase(
        user_id=chat.user_id,
        response=response_data.get("response", ""),
        date_created=datetime.utcnow(),
    )



def create_research(research: query_schema.ResearchCreate, request: Request):

    response = requests.post(
        f"{AGENT_SERVICE_URL}/research/",
        json={
            "user_id": research.user_id,
            "username": research.username,
            "query": research.query,
        },
        headers={"Content-Type": "application/json"},
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found. Try again later.",
        )

    response_data = response.json()

    return query_schema.ResearchResponse(response=response_data.get("response", ""))
