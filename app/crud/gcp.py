from sqlalchemy.orm import Session
from app.schemas import gcp_schema
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


def setup_vector_store(params: gcp_schema.StorageBase, data_folder: str, vector_folder: str):

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
