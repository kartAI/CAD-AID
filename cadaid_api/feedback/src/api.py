from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json

from shared.utils.logger import cadaid_logger
from shared.utils.data_structures import Metadata

# Set up logger
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

# Set up FastAPI app
app = FastAPI()

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

@app.post("/feedback")
async def feedback(filename: str = Form(...),
                   user_response: str = Form(...)):
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