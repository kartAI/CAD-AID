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
#from shared.auth import get_api_key


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
              #swagger_ui_init_oauth={
                #  "apiKeyName": "X-API-Key"
              #}
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
    filename: str
    user_response: bool


async def fetch_detection_results(filename: str):
    """
    Get metadata from detection endpoint
    """
    try:
        async with httpx.AsyncClient() as client:
            url = "http://detect:8000/detection-results"
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'metadata' not in data:
                logger.error("No metadata found in detection results")
                raise HTTPException(status_code=404, detail="No metadata found")
                
            if filename not in data['metadata']:
                logger.error(f"No results found for file: {filename}")
                raise HTTPException(status_code=404, detail=f"No results found for file: {filename}")
                
            return data['metadata'][filename]
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while fetching detection results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching detection results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/")
async def feedback(
    filename: str = Form(...),
    user_response: bool = Form(...),
    #api_key: APIKeyHeader = Depends(get_api_key)
):
    try:
        detection_results = await fetch_detection_results(filename)
        logger.info(f"Fetched detection response {detection_results}")
        if not detection_results:
            raise HTTPException(status_code=404, detail="Metadata not found")
        
        # Use .get() with default values to handle missing keys
        metadata = detection_results.get('filename', {})
        upload_path = detection_results.get('filepath', '/app/upload_files')  # Default path if not found

        upload_file_path = f"{upload_path}/{filename}"
       
        feedback_folder = os.path.join(FEEDBACK_DIRECTORY, filename)
        os.makedirs(feedback_folder, exist_ok=True)

        feedback_data = {
            'user_response': user_response,
            'metadata': metadata,
            'timestamp': datetime.datetime.now().isoformat()
        }

        feedback_file_path = os.path.join(feedback_folder, f"{filename}_feedback_metadata.json")

        with open(feedback_file_path, 'w') as f:
            json.dump(feedback_data, f, indent=4)
        
        # Only try to copy and remove if the file exists
        if os.path.exists(upload_file_path):
            saved_image_path = os.path.join(feedback_folder, os.path.basename(upload_file_path))
            shutil.copy(upload_file_path, saved_image_path)

            # Clean up
            try:
                os.remove(upload_file_path)
                logger.info(f"Removed temporary file: {upload_file_path}")
            except Exception as e:
                logger.error(f"Error removing file '{upload_file_path}': {str(e)}")
            
        return {'message': 'Feedback admitted', 'feedback': feedback_data}

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
                "Content-Length": "100"  # Add explicit content length
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))