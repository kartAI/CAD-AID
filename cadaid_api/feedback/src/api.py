from fastapi import FastAPI, HTTPException, Form, Depends, status, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import json

from shared.utils.logger import cadaid_logger
from shared.utils.data_structures import Metadata
from shared.auth import get_api_key

# Set up logger
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")


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
)

FEEDBACK_DIRECTORY = "feedback"
os.makedirs(FEEDBACK_DIRECTORY, exist_ok=True)

class FeedbackModel(BaseModel):
    filename: str
    user_response: str
    drawing_type: List[str]
    bbox: List[List[float]]
    confidence: List[float]
    cardinal_direction: str
    scale: str
    room_names: List[str]

metadata_store = {}

@app.post("/")
async def feedback(
    filename: str = Form(...),
    user_response: str = Form(...),
    api_key: APIKeyHeader = Depends(get_api_key)
):
    # Use the authentication function to validate the API key
    if filename not in metadata_store:
        raise HTTPException(status_code=404, detail="Metadata not found")
    
    metadata = metadata_store[filename]
    
    if user_response not in ['ja', 'nei']:
        raise HTTPException(status_code=400, detail="Invalid user response")
    
    feedback_data = {
        'filename': metadata.filename,
        'user_response': user_response,
        'drawing_type': metadata.drawing_types,
        'bbox': metadata.bbox,
        'confidence': metadata.confidence,
    }
    
    feedback_file = os.path.join(FEEDBACK_DIRECTORY, f"{filename}_feedback.json")
    with open(feedback_file, 'w') as f:
        json.dump(feedback_data, f, indent=4)
        
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