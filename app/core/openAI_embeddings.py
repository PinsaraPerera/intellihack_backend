import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from google.cloud import storage
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from .config import redis_client
from pathlib import Path
from dotenv import load_dotenv
from .gcp_utils import download_from_gcp, upload_to_gcp, download_file_from_gcp
from logging_config import logger
from google.cloud.exceptions import GoogleCloudError
from .config import BUCKET_NAME, DATA_FOLDER, VECTOR_STORE_FOLDER, RESOURCE_FOLDER
import tempfile
import pickle
import shutil
import faiss
import asyncio
import numpy as np

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


async def load_vector_db(session_id, user_email):
    """
    Load the vector database from Redis cache or Google Cloud Storage if not cached.

    :param session_id: The session ID used as the key for caching.
    :param user_email: The user email to locate the vectorstore in GCS.
    :return: The loaded vector store.
    :raises RuntimeError: If loading the vector store fails.
    """

    cached_index = await redis_client.get(f"{session_id}_index")
    cached_metadata = await redis_client.get(f"{session_id}_metadata")
    if cached_index and cached_metadata:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Deserialize index and metadata
                index_data = np.frombuffer(cached_index, dtype=np.uint8)
                index = faiss.deserialize_index(index_data)
                metadata = pickle.loads(cached_metadata)

                # Write the deserialized index and metadata to temporary files
                index_path = os.path.join(temp_dir, "index.faiss")
                metadata_path = os.path.join(temp_dir, "index.pkl")

                with open(index_path, "wb") as f:
                    f.write(index_data)

                with open(metadata_path, "wb") as f:
                    f.write(cached_metadata)

                # Load the vector store from the files
                vectorstore = FAISS.load_local(
                    temp_dir, OpenAIEmbeddings(), allow_dangerous_deserialization=True
                )
                logger.info(
                    f"Loaded vectorstore from cache for session_id: {session_id}"
                )
                return vectorstore

        except Exception as e:
            logger.error(
                f"Failed to load vectorstore from cache for session_id: {session_id}: {e}"
            )
            raise RuntimeError("Failed to load vectorstore from cache") from e
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                source_file_path = f"{DATA_FOLDER}/{user_email}/{VECTOR_STORE_FOLDER}"
                download_from_gcp(BUCKET_NAME, source_file_path, temp_dir)

                db_path = temp_dir
                if not (
                    os.path.exists(os.path.join(db_path, "index.faiss"))
                    and os.path.exists(os.path.join(db_path, "index.pkl"))
                ):
                    raise FileNotFoundError(f"Required files not found in {db_path}")

                vectorstore = FAISS.load_local(
                    db_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True
                )

                # Serialize the index and metadata to byte strings
                index = vectorstore.index
                index_data = faiss.serialize_index(index).tobytes()

                with open(os.path.join(db_path, "index.pkl"), "rb") as f:
                    metadata = pickle.load(f)
                metadata_data = pickle.dumps(metadata)

                # metadata_data = pickle.dumps(metadata)

                await redis_client.setex(
                    f"{session_id}_metadata", 3600, metadata_data
                )  # Cache with TTL of 1 hour

                await redis_client.setex(
                    f"{session_id}_index", 3600, index_data
                )  # Cache with TTL of 1 hour

                logger.info(
                    f"Loaded vectorstore from GCS and cached for session_id: {session_id}"
                )
                return vectorstore
            except GoogleCloudError as e:
                logger.error(
                    f"Failed to download vectorstore from GCS for session_id: {session_id}: {e}"
                )
                raise RuntimeError("Failed to download vectorstore from GCS") from e
            except Exception as e:
                logger.error(
                    f"Failed to load vectorstore for session_id: {session_id}: {e}"
                )
                raise RuntimeError("Failed to load vectorstore") from e


def create_vector_db_locally(data_path, db_faiss_path):
    """
    Create a vector database from documents in the specified data path and save it locally.

    :param data_path: The path to the data folder containing documents.
    :param db_faiss_path: The path where the vector database will be saved.
    :raises RuntimeError: If creating the vector database fails.
    """
    try:
        loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)
        vectorstore.save_local(db_faiss_path)
        logger.info(f"Created vector database and saved at {db_faiss_path}")
    except Exception as e:
        logger.error(f"Failed to create vector database: {e}")
        raise RuntimeError("Failed to create vector database") from e


def create_vector_db_gcp(user_email):
    """
    Process user data by downloading resources from GCP, creating a vector database, and uploading it back to GCP.

    :param user_email: The email of the user.
    :raises RuntimeError: If any step in processing user data fails.
    """
    user_folder = f"{DATA_FOLDER}/{user_email}"
    resources_folder = f"{user_folder}/{RESOURCE_FOLDER}"
    user_vector_store_folder = f"{user_folder}/{VECTOR_STORE_FOLDER}"

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download the data from the GCS bucket
            download_from_gcp(BUCKET_NAME, resources_folder, temp_dir)
            logger.info(f"Downloaded user data for {user_email} to {temp_dir}")

            # Create a local vector database
            db_faiss_path = Path(temp_dir, VECTOR_STORE_FOLDER)
            create_vector_db_locally(temp_dir, db_faiss_path)

            # Upload the vector database to the GCS bucket
            upload_to_gcp(BUCKET_NAME, db_faiss_path, user_vector_store_folder)
            logger.info(
                f"Uploaded vector database for {user_email} to {BUCKET_NAME}/{user_vector_store_folder}"
            )
        except RuntimeError as e:
            logger.error(f"Failed to process data for user {user_email}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing data for user {user_email}: {e}"
            )
            raise RuntimeError("Failed to process user data") from e


def create_vector_db_for_selected_pdfs(user_email, pdf_list):
    """
    Process user data by downloading resources from GCP, creating a vector database, and uploading it back to GCP.

    :param user_email: The email of the user.
    :raises RuntimeError: If any step in processing user data fails.
    """
    user_folder = f"{DATA_FOLDER}/{user_email}"
    resources_folder = f"{user_folder}/{RESOURCE_FOLDER}"
    user_vector_store_folder = f"{user_folder}/{VECTOR_STORE_FOLDER}"

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download the data from the GCS bucket
            for pdf in pdf_list:
                download_file_from_gcp(
                    BUCKET_NAME, f"{resources_folder}/{pdf}", temp_dir
                )
                logger.info(f"Downloaded file {pdf} for {user_email}")

            logger.info(f"Downloaded user data for {user_email} to {temp_dir}")

            # Create a local vector database
            db_faiss_path = Path(temp_dir, VECTOR_STORE_FOLDER)
            create_vector_db_locally(temp_dir, db_faiss_path)

            # Upload the vector database to the GCS bucket
            upload_to_gcp(BUCKET_NAME, db_faiss_path, user_vector_store_folder)
            logger.info(
                f"Uploaded vector database for {user_email} to {BUCKET_NAME}/{user_vector_store_folder}"
            )
        except RuntimeError as e:
            logger.error(f"Failed to process data for user {user_email}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing data for user {user_email}: {e}"
            )
            raise RuntimeError("Failed to process user data") from e


def download_vector_db(session_id, user_email):
    """
    Load the vector database from Redis cache or Google Cloud Storage if not cached.

    :param session_id: The session ID used as the key for caching.
    :param user_email: The user email to locate the vectorstore in GCS.
    :return: The loaded vector store.
    :raises RuntimeError: If loading the vector store fails.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            source_file_path = f"{DATA_FOLDER}/{user_email}/{VECTOR_STORE_FOLDER}"
            download_from_gcp(BUCKET_NAME, source_file_path, temp_dir)

            db_path = temp_dir
            if not (
                os.path.exists(os.path.join(db_path, "index.faiss"))
                and os.path.exists(os.path.join(db_path, "index.pkl"))
            ):
                raise FileNotFoundError(f"Required files not found in {db_path}")

            vectorstore = FAISS.load_local(
                db_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True
            )

            return vectorstore

        except GoogleCloudError as e:
            logger.error(
                f"Failed to download vectorstore from GCS for session_id: {session_id}: {e}"
            )
            raise RuntimeError("Failed to download vectorstore from GCS") from e
        except Exception as e:
            logger.error(
                f"Failed to load vectorstore for session_id: {session_id}: {e}"
            )
            raise RuntimeError("Failed to load vectorstore") from e

