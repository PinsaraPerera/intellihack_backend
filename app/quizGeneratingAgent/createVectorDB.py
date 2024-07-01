from fastapi import Request
from app.core.openAI_embeddings import load_vector_db
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path
import uuid


def search_vector_db(query: str, request: Request, user_email: str):
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = request.session["session_id"] = str(uuid.uuid4())
    db = load_vector_db(session_id, user_email)

    results = db.search(query=query, search_type="similarity", k=5)

    if results:
        return results[0].page_content
    return ""


