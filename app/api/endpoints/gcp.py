from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Request
from app.schemas import gcp_schema, user_schema
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils import oauth2
import app.crud.gcp as gcp
from app.schemas import user_schema 
from app.core.gcp_utils import create_folder_in_gcp
from app.core.config import DATA_FOLDER, RESOURCE_FOLDER, VECTOR_STORE_FOLDER

router = APIRouter(
    prefix="/storage",
    tags=["Storage"],
)

@router.post("/upload")
def upload_file(params: gcp_schema.StorageBase, request: Request):
    return gcp.upload(params, DATA_FOLDER, RESOURCE_FOLDER)

@router.post("/setupVectorStore", response_model=user_schema.User)
def setup_vector_store(params: gcp_schema.VectorStore, request: Request, db: Session = Depends(get_db)):
    return gcp.setup_vectorStore(params, DATA_FOLDER, VECTOR_STORE_FOLDER, db)

@router.post("/generateSignedUrl")
def generate_signed_url(params: gcp_schema.StorageCreate, request: Request):
    return gcp.generate_signed_url(params, DATA_FOLDER)