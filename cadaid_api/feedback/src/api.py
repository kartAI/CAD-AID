from fastapi import FastAPI, HTTPException, Form, Depends, status, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
import os
import shutil
from typing import Optional
import json
import datetime
import httpx
from fastapi.responses import JSONResponse
from shared.utils.logger import cadaid_logger
from shared.utils.storage_handler import StorageHandler
from shared.auth import get_api_key


# Set up logger
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Feedback API")
    await asyncio.sleep(5)
    logger.info("Feedback API ready")
    yield
    # Shutdown
    logger.info("Shutting down Feedback API")

# Set up FastAPI app
app = FastAPI(root_path="/feedback",
              root_path_in_servers=True,
              title="Feedback API",
              description="API for feedback submission using CADAID system",
              version="1.0.0",
              docs_url="/docs",
              open_api_url="/openapi.json",
              openapi_tags=[{
                "name": "Feedback",
                "description": "API for feedback submission to further improve the CADAID system"
              }], 
              swagger_ui_init_oauth={
                  "apiKeyName": "X-API-Key"
              }
        )

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Make sure these directories exist and have proper permissions
UPLOAD_DIRECTORY = "/app/upload_files"
FEEDBACK_DIRECTORY = "/app/metadata_files_store"
DETECTION_RESULTS_PATH = "/app/metadata_files_store/detection_results.json"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(FEEDBACK_DIRECTORY, exist_ok=True)

class FeedbackModel(BaseModel):
    filename: str = Form(...)
    user_response: bool = Form(...)




async def fetch_detection_results(filename: str):
    """
    Get metadata from detection endpoint.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Set URL for production or local testing
            url = "http://cadaid-api.westeurope.azurecontainer.io/detect/detection-results"  # Production
            # url = "http://localhost/detect/detection-results"  # Uncomment for local testing

            logger.debug(f"Fetching detection results from URL: {url}")

            # Make the GET request
            response = await client.get(url)
            logger.debug(f"HTTP response status: {response.status_code}")

            # Raise HTTP error if the request failed
            response.raise_for_status()

            # Parse JSON response
            try:
                data = response.json()
                logger.debug(f"Response JSON data: {data}")
            except ValueError as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                raise HTTPException(status_code=500, detail="Invalid JSON response from detection endpoint")

            # Validate presence of 'metadata' key
            if not data or 'metadata' not in data:
                logger.error("No metadata found in detection results")
                raise HTTPException(status_code=404, detail="No metadata found in detection results")

            # Check if the filename is present in metadata
            if filename not in data['metadata']:
                logger.error(f"No results found for file: {filename}")
                raise HTTPException(status_code=404, detail=f"No results found for file: {filename}")

            logger.info(f"Metadata found for file: {filename}")
            return data['metadata'][filename]

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while fetching detection results: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail="Error fetching detection results")
    except httpx.RequestError as e:
        logger.error(f"Request error while fetching detection results: {str(e)}")
        raise HTTPException(status_code=500, detail="Request error fetching detection results")
    except Exception as e:
        logger.error(f"Unexpected error in fetch_detection_results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize storage handler
storage = StorageHandler(use_azure=os.getenv("USE_AZURE_STORAGE", "false").lower() == "true")

@app.post("/")
async def feedback(
    filename: str = Form(...),
    user_response: bool = Form(...),
    api_key: APIKeyHeader = Depends(get_api_key)
):
    try:
        # Fetch metadata
        detection_results = storage.get_metadata(filename)
        logger.debug(f"Detection results for {filename}: {detection_results}")

        if detection_results is None:
            logger.error(f"Metadata not found for file: {filename}")
            raise HTTPException(status_code=404, detail="Metadata not found")

        # Prepare feedback data
        feedback_data = {
            'user_response': user_response,
            'metadata': detection_results,
            'timestamp': datetime.datetime.now().isoformat()
        }
        logger.info(f"Prepared feedback data: {feedback_data}")

        # Save feedback metadata using StorageHandler
        feedback_path = f"feedback_{filename}"
        storage.save_metadata(feedback_data, feedback_path)
        logger.info(f"Feedback metadata saved at path: {feedback_path} for file: {filename}")

        # Handle local file copy if not using Azure
        if not storage.use_azure:
            upload_file_path = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(upload_file_path):
                # Ensure feedback folder exists
                feedback_folder = os.path.join(FEEDBACK_DIRECTORY, filename)
                os.makedirs(feedback_folder, exist_ok=True)

                # Copy the file to the feedback folder
                saved_image_path = os.path.join(feedback_folder, os.path.basename(upload_file_path))
                shutil.copy(upload_file_path, saved_image_path)
                logger.info(f"Copied file to feedback directory: {saved_image_path}")

        # Clean up file if Azure is enabled
        if storage.use_azure:
            storage.delete_file(filename)

        logger.info(f"Feedback saved for {filename}")
        return {"message": "Feedback submitted successfully", "feedback": feedback_data}

    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to check log file
@app.get("/logs/")
async def get_logs():
    try:
        with open('/app/logs/app.log', 'r') as log_file:
            logs = log_file.read()
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error fetchcing logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch logs")
    
@app.get("/health")
async def health_check():
    try:
        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.datetime.now().isoformat(),
                "service": "detect"
            },
            headers={
                "Content-Type": "application/json",
                #"Content-Length": "100"  # Add explicit content length
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))