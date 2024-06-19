import os
from google.cloud import storage
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import shutil
from logging_config import logger

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

DATA_FOLDER = "data"
RESOURCE_FOLDER = "resources"
VECTOR_STORE_FOLDER = "vectorStore"


def download_from_gcp(bucket_name, source_folder_path, local_dest_path):
    """
    Download files from a Google Cloud Storage bucket to a local directory.

    :param bucket_name: The name of the GCS bucket.
    :param source_folder_path: The path to the folder in the bucket to download files from.
    :param local_dest_path: The local directory to download files to.
    """
    client = storage.Client()

    try:
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=source_folder_path)

        if not blobs:
            logger.warning(f"No blobs found in {bucket_name}/{source_folder_path}")
            return

        for blob in blobs:
            if blob.name.endswith("/"):
                continue  # Skip "folders"
            dest_file_path = os.path.join(
                local_dest_path, os.path.relpath(blob.name, source_folder_path)
            )
            os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
            blob.download_to_filename(dest_file_path)
            logger.info(f"Downloaded {blob.name} to {dest_file_path}")
    except GoogleCloudError as e:
        logger.error(
            f"Failed to download files from {bucket_name}/{source_folder_path}: {e}"
        )
        raise RuntimeError(
            f"Failed to download files from {bucket_name}/{source_folder_path}"
        ) from e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def upload_to_gcp(bucket_name, source_folder_path, destination_folder_path):
    """
    Uploads all files from a local folder to a specified folder in the Google Cloud Storage bucket.

    :param bucket_name: The name of the GCS bucket.
    :param source_folder_path: The path to the local folder containing files and subfolders.
    :param destination_folder_path: The destination folder path in the bucket.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    try:
        for root, dirs, files in os.walk(source_folder_path):
            for filename in files:
                source_file_path = os.path.join(root, filename)
                # Construct the destination blob name relative to the source folder
                relative_path = os.path.relpath(source_file_path, source_folder_path)
                destination_blob_name = os.path.join(
                    destination_folder_path, relative_path
                ).replace("\\", "/")
                blob = bucket.blob(destination_blob_name)
                blob.upload_from_filename(source_file_path)
                logger.info(
                    f"Uploaded {source_file_path} to {bucket_name}/{destination_blob_name}"
                )
    except GoogleCloudError as e:
        logger.error(
            f"Failed to upload files to {bucket_name}/{destination_folder_path}: {e}"
        )
        raise RuntimeError(
            f"Failed to upload files to {bucket_name}/{destination_folder_path}"
        ) from e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def create_folder_in_gcp(user_email: str):
    """
    Create a "folder" in the Google Cloud Storage bucket by creating an empty object with a trailing slash.

    :param user_email: The email of the user, used to construct the folder path.
    """
    bucket_name = BUCKET_NAME
    folder_path = f"data/{user_email}/"  # Ensure the path has a trailing slash it creates a "folder"

    client = storage.Client()

    try:
        bucket = client.bucket(bucket_name)

        # Check if the folder already exists
        blobs = list(bucket.list_blobs(prefix=folder_path, delimiter="/"))
        if blobs:
            logger.info(f"Folder {folder_path} already exists in bucket {bucket_name}")
            return

        # Create the folder if it does not exist
        blob1 = bucket.blob(folder_path)
        blob1.upload_from_string("")  # Create an empty object to simulate a folder
        logger.info(f"Created folder {folder_path} in bucket {bucket_name}")

        blob2 = bucket.blob(folder_path + RESOURCE_FOLDER + "/")
        blob2.upload_from_string("")  # Create an empty object to simulate a subfolder
        logger.info(
            f"Created folder {folder_path+RESOURCE_FOLDER} in bucket {bucket_name}"
        )

        blob3 = bucket.blob(folder_path + VECTOR_STORE_FOLDER + "/")
        blob3.upload_from_string("")  # Create an empty object to simulate a subfolder
        logger.info(
            f"Created folder {folder_path+VECTOR_STORE_FOLDER} in bucket {bucket_name}"
        )

    except GoogleCloudError as e:
        logger.error(
            f"Failed to create folder {folder_path} in bucket {bucket_name}: {e}"
        )
        raise RuntimeError(
            f"Failed to create folder {folder_path} in bucket {bucket_name}"
        ) from e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise


def delete_pdf_from_gcp(bucket_name, file_path):
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
