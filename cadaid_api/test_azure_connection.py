from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
import os
import json

def test_azure_connection():
    try:
        # Get connection details
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.getenv('AZURE_STORAGE_CONTAINER')
        
        print(f"\n1. Testing connection details:")
        print(f"Container name: {container_name}")
        print(f"Connection string exists: {'Yes' if connection_string else 'No'}")
        
        # Create clients
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service.get_container_client(container_name)
        
        print("\n2. Testing container access:")
        container_exists = container_client.exists()
        print(f"Container exists: {container_exists}")
        
        # List blobs in each directory
        print("\n3. Listing blobs in uploads/:")
        upload_blobs = list(container_client.list_blobs(name_starts_with="uploads/"))
        print(f"Found {len(upload_blobs)} files in uploads/")
        for blob in upload_blobs[:5]:  # Show first 5
            print(f"- {blob.name}")
            
        print("\n4. Listing blobs in metadata/:")
        metadata_blobs = list(container_client.list_blobs(name_starts_with="metadata/"))
        print(f"Found {len(metadata_blobs)} files in metadata/")
        for blob in metadata_blobs[:5]:  # Show first 5
            print(f"- {blob.name}")
            
        # Test downloading a specific file (if any exist)
        if metadata_blobs:
            print("\n5. Testing metadata file download:")
            test_blob = metadata_blobs[0]
            print(f"Attempting to download: {test_blob.name}")
            
            blob_client = container_client.get_blob_client(test_blob.name)
            content = blob_client.download_blob().readall()
            metadata = json.loads(content)
            print("Successfully downloaded and parsed metadata file")
            
        return True

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Azure Storage Connection Test")
    print("=====================================")
    
    success = test_azure_connection()
    
    print("\n=====================================")
    print(f"Test {'PASSED' if success else 'FAILED'}")