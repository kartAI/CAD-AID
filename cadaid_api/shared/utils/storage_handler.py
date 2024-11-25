from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import os
import json
from typing import Optional, BinaryIO
from pathlib import Path
from .logger import cadaid_logger

logger = cadaid_logger(__name__)

class StorageHandler:
    def __init__(self, use_azure: bool = False):
        self.use_azure = use_azure
        logger.debug(f"Using Azure Blob Storage: {self.use_azure}")
        if self.use_azure:
            try:
                # Get connection details from environment variables
                self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                self.container_name = os.getenv('AZURE_STORAGE_CONTAINER')

                if not self.connection_string or not self.container_name:
                    raise ValueError("Azure Blob Storage connection details not found in environment variables.")
                
                # Create the blob service client
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

                # Get container client and verify its existence
                self.container_client = self.blob_service_client.get_container_client(self.container_name)
                if not self.container_client.exists():
                    raise ValueError(f"Azure Blob Storage container '{self.container_name}' not found.")
                
                # Verify that we can list blobs in the container
                next(self.container_client.list_blobs(), None)

                logger.info(f"Connected to Azure Blob Storage container: {self.container_name}")
            except Exception as e:
                logger.error(f"Error connecting to Azure Blob Storage: {str(e)}")
                raise
        else:
            self.upload_dir = Path("/app/upload_files")
            self.metadata_dir = Path("/app/metadata_files_store")
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return its path"""
        try:
            if self.use_azure:
                blob_path = f"uploads/{filename}"
                blob_client = self.container_client.get_blob_client(blob_path)
                blob_client.upload_blob(file_content, overwrite=True)
                return blob_path
            else:
                file_path = self.upload_dir / filename
                with open(file_path, "wb") as f:
                    f.write(file_content)
                return str(file_path)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise

        
    def save_metadata(self, metadata: dict, filename: str) -> str:
        """Save metadata and return its path"""
        try:
            if self.use_azure:
                blob_path = f"metadata/{filename}_metadata.json"
                logger.debug(f"Saving metadata to Azure Blob: {blob_path}")
                blob_client = self.container_client.get_blob_client(blob_path)
                blob_client.upload_blob(json.dumps(metadata), overwrite=True)  # Asynchronous
                return blob_path
            else:
                file_path = self.metadata_dir / f"{filename}_metadata.json"
                logger.debug(f"Saving metadata locally at path: {file_path}")
                with open(file_path, "w") as f:
                    json.dump(metadata, f)  # Synchronous
                return str(file_path)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise

        
    async def get_file(self, filename: str) -> Optional[bytes]:
        """Retrieve file content."""
        try:
            if self.use_azure:
                # Azure operations are async
                blob_path = f"uploads/{filename}"
                blob_client = self.container_client.get_blob_client(blob_path)
                download_stream = blob_client.download_blob()
                file_content = download_stream.readall()  # Synchronous call
                return file_content
            else:
                # Local operations are sync
                file_path = self.upload_dir / filename
                if file_path.exists():
                    return file_path.read_bytes()
                return None
        except Exception as e:
            logger.error(f"Error retrieving file: {str(e)}")
            raise

        
    def get_metadata(self, filename: str) -> Optional[dict]:
        """Retrieve metadata content"""
        try:
            if self.use_azure:
                blob_path = f"metadata/{filename}_metadata.json"
                logger.debug(f"Trying to fetch metadata blob at path: {blob_path}")
                blob_client = self.container_client.get_blob_client(blob_path)
                if not blob_client.exists():
                    logger.warning(f"Metadata blob at {blob_path} not found.")
                    return None
                
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                logger.debug(f"Successfully downlaoded metadata for {filename}")
                return json.loads(content)
            else:
                file_path = self.metadata_dir / f"{filename}_metadata.json"
                logger.debug(f"Trying to fetch metadata file at path: {file_path}")
                if file_path.exists():
                    with open(file_path, "r") as f:
                        return json.load(f)
                    logger.error(f"Metadata file not found: {file_path}")
                return None
        except ResourceNotFoundError:
            logger.warning(f"Metadata not found for file: {filename}")
            return None
        except AzureError as e:
            logger.error(f"Azure storage error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving metadata: {str(e)}")
            raise
        
    def delete_file(self, filename: str):
        """Delete file from Azure Blob Storage or local storage."""
        try:
            if self.use_azure:
                blob_path = f"uploads/{filename}"
                blob_client = self.container_client.get_blob_client(blob_path)
                try:
                    blob_client.delete_blob()  # Synchronous call
                    logger.info(f"Blob {blob_path} deleted successfully.")
                except ResourceNotFoundError:
                    logger.warning(f"Blob {blob_path} not found or already deleted.")
            else:
                file_path = self.upload_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Local file {file_path} deleted successfully.")
                else:
                    logger.warning(f"Local file {file_path} not found or already deleted.")
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {str(e)}")
            raise

