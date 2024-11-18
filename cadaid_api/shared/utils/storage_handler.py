from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import os
import json
from typing import Optional, BinaryIO
from pathlib import Path

class StorageHandler:
    def __init__(self):
        self.use_azure = os.getenv('USE_AZURE_STORAGE', 'false').lower() == 'true'
        if self.use_azure:
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            self.container_name = os.getenv('AZURE_STORAGE_CONTAINER')
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
        else:
            self.upload_dir = Path("/app/upload_files")
            self.metadata_dir = Path("/app/metadata_files_store")
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
    async def save_file(self, file_content: BinaryIO, filename: str) -> str:
        """Save uploaded file and return its path"""
        try:
            if self.use_azure:
                blob_path = f"uploads/{filename}"
                print(f"Saving to Azure Blob: {blob_path}")
                blob_client = self.container_client.get_blob_client(blob_path)
                # Convert file content to bytes before uploading
                print("Reading file content")
                content = await file_content.read()
                if not isinstance(content, bytes):
                    print(f"Converting content type {type(content)} to bytes")
                    content = bytes(str(content), "utf-8") if isinstance(content, (str, dict)) else bytes(content)
                print(f"Content read, size: {len(content)} bytes")
                print("Uploading to blob storage")
                blob_client.upload_blob(content, overwrite=True)
                print("Upload complete")
                return blob_path
            else:
                file_path = self.upload_dir / filename
                print(f"Saving to local path: {file_path}")
                content = await file_content.read()
                print(f"Content read, size: {len(content)} bytes")
                with open(file_path, "wb") as f:
                    f.write(content)
                print("File saved locally")
                return str(file_path)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {e.__dict__}")
            print(f"Content type: {type(content)}")
            raise


        
    def save_metadata(self, metadata: dict, filename: str) -> str:
        """Save metadata and return its path"""
        if self.use_azure:
            blob_path = f"metadata/{filename}_metadata.json"
            blob_client = self.container_client.get_blob_client(blob_path)
            blob_client.upload_blob(json.dumps(metadata), overwrite=True)  # Asynchronous
            return blob_path
        else:
            file_path = self.metadata_dir / f"{filename}_metadata.json"
            with open(file_path, "w") as f:
                json.dump(metadata, f)  # Synchronous
            return str(file_path)


        
    async def get_file(self, filename: str) -> Optional[bytes]:
        """Retrieve file content"""
        try:
            if self.use_azure:
                blob_path = f"uploads/{filename}"
                blob_client = self.container_client.get_blob_client(blob_path)
                download_stream = blob_client.download_blob()
                content = download_stream.readall()
                return content
            else:
                file_path = self.upload_dir / filename
                if file_path.exists():
                    return file_path.read_bytes()
                return None
        except Exception as e:
            print(f"Error retrieving file: {str(e)}")
            return None
        
    async def get_metadata(self, filename: str) -> Optional[dict]:
        """Retrieve metadata content"""
        try:
            if self.use_azure:
                blob_path = f"metadata/{filename}_metadata.json"
                blob_client = self.container_client.get_blob_client(blob_path)
                content = await blob_client.download_blob().readall()
                return json.loads(content)
            else:
                file_path = self.metadata_dir / f"{filename}_metadata.json"
                if file_path.exists():
                    return json.loads(file_path.read_text())
                return None
        except Exception as e:
            print(f"Error retrieving metadata: {str(e)}")
            return None
        
    async def delete_file(self, filename: str):
        """Delete file"""
        try:
            if self.use_azure:
                blob_path = f"uploads/{filename}"
                blob_client = self.container_client.get_blob_client(blob_path)
                await blob_client.delete_blob()
            else:
                file_path = self.upload_dir / filename
                if file_path.exists():
                    file_path.unlink()
        except Exception as e:
            print(f"Error deleting file: {str(e)}")