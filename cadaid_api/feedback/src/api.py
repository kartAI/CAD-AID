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
)

FEEDBACK_DIRECTORY = "/app/metadata_files_store"
os.makedirs(FEEDBACK_DIRECTORY, exist_ok=True)

class FeedbackModel(BaseModel):
    filename: str
    user_response: bool


async def fetch_detection_results(filename:str):
    """
    Get metadata from detection endpoint
    """
    async with httpx.AsyncClient() as client:
        url = "http://detect:8000/detect/detection-results"
        response = await client.get(url)
        response.raise_for_status()

        detection_results = response.json()
      
        if isinstance(detection_results, dict):
            detection_filepath = detection_results['filepath']
            detection_results = detection_results['metadata'][filename]
        for item in detection_results:
            if detection_results[item] == filename:
                return {'filename': detection_results, 'filepath': detection_filepath}
        
    return None



@app.post("/")
async def feedback(#feedback: FeedbackModel
    filename: str = Form(...),
    user_response: bool = Form(...),
    #api_key: APIKeyHeader = Depends(get_api_key)
):
    
    detection_results = await fetch_detection_results(filename)
    logger.info(f"Fetched detection response {detection_results}")
    if not detection_results:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    metadata = detection_results['filename']
    upload_path = detection_results['filepath']

    upload_file_path = f"{upload_path}/{filename}"
   
    feedback_folder =os.path.join(FEEDBACK_DIRECTORY, filename)
    os.makedirs(feedback_folder, exist_ok=True)

    feedback_data = {
        'user_response': user_response,
        'metadata': metadata
    }

    feedback_file_path = os.path.join(feedback_folder, f"{filename}_feedback_metadata.json")

    with open(feedback_file_path, 'w') as f:
        json.dump(feedback_data, f, indent=4)
    
    saved_image_path = os.path.join(feedback_folder, os.path.basename(upload_file_path))
    shutil.copy(upload_file_path, saved_image_path)

    #clean up
    if os.path.exists(upload_file_path):
        try:
            os.remove(upload_file_path)
            logger.info(f"Removed temporary file: {upload_file_path}")

        except Exception as e:
            logger.error(f"Error removing file '{upload_file_path}': {str(e)}")

        
    return {'message': 'Feedback admitted', 'feedback': feedback_data}

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