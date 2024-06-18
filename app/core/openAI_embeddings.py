import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from google.cloud import storage
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import shutil

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

DATA_FOLDER = "users"
VECTOR_STORE_FOLDER = "vector_store"

def download_from_gcs(bucket_name, user_folder, local_dir):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=user_folder)
    for blob in blobs:
        if blob.name.endswith('.pdf'):
            local_path = os.path.join(local_dir, os.path.basename(blob.name))
            blob.download_to_filename(local_path)
            print(f"Downloaded {blob.name} to {local_path}")

def upload_to_gcs(bucket_name, source_folder, destination_folder):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for root, _, files in os.walk(source_folder):
        for file in files:
            file_path = os.path.join(root, file)
            blob_name = os.path.join(destination_folder, os.path.relpath(file_path, source_folder))
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            print(f"Uploaded {file_path} to {bucket_name}/{blob_name}")

def create_vector_db(data_path, db_faiss_path):
    # Load the data
    loader = DirectoryLoader(data_path, glob='*.pdf', loader_cls=PyPDFLoader)
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
    user_vector_store_folder = f"{user_folder}/{VECTOR_STORE_FOLDER}"

    with tempfile.TemporaryDirectory() as temp_dir:
        # download the data from the GCS bucket
        download_from_gcs(BUCKET_NAME, user_folder, temp_dir)

        # create a local vector database
        db_faiss_path = Path(temp_dir, VECTOR_STORE_FOLDER)
        create_vector_db(temp_dir, db_faiss_path)

        # upload the vector database to the GCS bucket
        upload_to_gcs(BUCKET_NAME, db_faiss_path, user_vector_store_folder)

def delete_pdf_from_gcs(bucket_name, file_path):
    """
    Delete a specific PDF from the Google Cloud Storage bucket.

    FILE_PATH = 'users/user@example.com/sample.pdf'

    :param bucket_name: The name of the GCS bucket.
    :param file_path: The path to the PDF file in the bucket.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if blob.exists():
        blob.delete()
        print(f"Deleted {file_path} from {bucket_name}")
    else:
        print(f"The file {file_path} does not exist in {bucket_name}")
