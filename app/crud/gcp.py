import os
import datetime
from sqlalchemy.orm import Session
from app.schemas import gcp_schema
from google.cloud import storage
import datetime
from app.core.openAI_embeddings import create_vector_db_gcp


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


def setup_vector_store(
    params: gcp_schema.StorageBase, data_folder: str, vector_folder: str
):

    try:
        create_vector_db_gcp(params.username)

        response = {
            "usr_id": params.user_id,
            "message": "Vector store setup successfully",
            "response": f"{data_folder}/{params.username}/{vector_folder}",
        }
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup vector store for user {params.username}: {e}",
        )


def generate_signed_url(params: gcp_schema.StorageCreate, data_folder: str):
    """Generates a v4 signed URL for uploading a blob using HTTP PUT."""
    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="Bucket name not set in environment variables")

    user_folder = f"{data_folder}/{params.username}/resources"
    blob_name = f"{user_folder}/{params.filename}"

    storage_client = storage.Client.from_service_account_json('keys/service_account.json')
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
        "date_created": datetime.datetime.utcnow()
    }

    return response