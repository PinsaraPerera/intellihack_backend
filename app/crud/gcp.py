import os
import datetime
from sqlalchemy.orm import Session
from app.schemas import gcp_schema
from google.cloud import storage
from fastapi import HTTPException, status
import datetime
import app.models.user as user
from app.core.openAI_embeddings import create_vector_db_gcp, create_vector_db_for_selected_pdfs
from app.core.gcp_utils import delete_pdf_from_gcp, list_pdfs



def upload(params: gcp_schema.StorageBase, data_folder: str, resource_folder: str):
    try:
        # We create the folder in login endpoint
        # For demonstration, we just create a response
        response = {
            "usr_id": params.user_id,
            "message": "Folder created successfully",
            "response": f"{data_folder}/{params.username}/{resource_folder}",
        }
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create folder for user {params.username}: {e}",
        )


def setup_vectorStore(
    params: gcp_schema.VectorStore, data_folder: str, vector_folder: str, db: Session
):

    try:
        user_found = db.query(user.User).filter(user.User.id == params.id).first()
        if not user_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found",
            )

        create_vector_db_gcp(params.email)

        user_found.vectorstore = True

        db.add(user_found)
        db.commit()
        db.refresh(user_found)
        return user_found

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup vector store for user {params.email}: {e}",
        )


def setup_vectorStoreWithPdf(
    params: gcp_schema.VectorStoreFiles, data_folder: str, vector_folder: str, db: Session
):

    try:
        user_found = db.query(user.User).filter(user.User.id == params.id).first()
        if not user_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found",
            )

        create_vector_db_for_selected_pdfs(params.email, params.filenames)

        user_found.vectorstore = True

        db.add(user_found)
        db.commit()
        db.refresh(user_found)
        return user_found

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup vector store for user {params.email}: {e}",
        )


def generate_signed_url(params: gcp_schema.StorageCreate, data_folder: str):
    """Generates a v4 signed URL for uploading a blob using HTTP PUT."""
    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(
            status_code=500, detail="Bucket name not set in environment variables"
        )

    user_folder = f"{data_folder}/{params.username}/resources"
    blob_name = f"{user_folder}/{params.filename}"

    storage_client = storage.Client.from_service_account_json(
        "keys/service_account.json"
    )
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),  # This URL is valid for 15 minutes
        method="PUT",
        content_type="application/octet-stream",
    )

    response = {
        "user_id": params.user_id,
        "message": "URL generated successfully",
        "validation_time": 15,
        "response": url,
        "date_created": datetime.datetime.utcnow(),
    }

    return response

def delete(params: gcp_schema.DeleteFile):
    try:
        delete_pdf_from_gcp(params.username, params.filenames)
        response = gcp_schema.Response( message = "Files deleted successfully")
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete files: {e}",
        )

def list_files(params: gcp_schema.StorageBase):
    try:
        files = list_pdfs(params.username)
        files = [file.split("/")[-1] for file in files]
        response = gcp_schema.FileList(user_id = params.user_id, filenames = files)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {e}",
        )
