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
from .gcp_utils import download_from_gcp, upload_to_gcp, create_folder_in_gcp
import tempfile
import pickle
import shutil

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

DATA_FOLDER = "data"
VECTOR_STORE_FOLDER = "vectorStore"

def load_vector_db(session_id):
    cached_db = redis_client.get(session_id)
    if cached_db:
        vectorstore = pickle.loads(cached_db)
        return vectorstore
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            download_folder_from_gcs(BUCKET_NAME, VECTOR_STORE_FOLDER, temp_dir)
            db_path = os.path.join(temp_dir, 'db_faiss')
            vectorstore = FAISS.load_local(db_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)
            redis_client.setex(session_id, 3600, pickle.dumps(vectorstore))  # Cache with TTL of 1 hour
            return vectorstore


def create_vector_db(data_path, db_faiss_path):
    # Load the data
    loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    # Split the data
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = splitter.split_documents(documents)
    # Load the embeddings
    embeddings = OpenAIEmbeddings()
    # Create the vector store
    vectorstore = FAISS.from_documents(texts, embeddings)
    # Ingest the data
    vectorstore.save_local(db_faiss_path)


def process_user_data(user_email):
    user_folder = f"{DATA_FOLDER}/{user_email}"
    resources_folder = f"{user_folder}/resources"
    user_vector_store_folder = f"{user_folder}/{VECTOR_STORE_FOLDER}"

    with tempfile.TemporaryDirectory() as temp_dir:
        # download the data from the GCS bucket
        download_from_gcp(BUCKET_NAME, resources_folder, temp_dir)

        # create a local vector database
        db_faiss_path = Path(temp_dir, VECTOR_STORE_FOLDER)
        create_vector_db(temp_dir, db_faiss_path)

        # upload the vector database to the GCS bucket
        upload_to_gcp(BUCKET_NAME, db_faiss_path, user_vector_store_folder)
