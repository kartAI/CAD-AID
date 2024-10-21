from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Query
from pathlib import Path
from pdf2image import convert_from_path
import cv2
from dotenv import load_dotenv
from pydantic import field_validator
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
from concurrent.futures import ThreadPoolExecutor
import yaml
import asyncio
from typing import Optional, Dict

from fastapi import APIRouter, Body
from pydantic import BaseModel
import json
from uuid import uuid4

from .utils.logger import cadaid_logger
from .utils.object_detection import ObjectDetectionHandler
from .utils.segmentation_handler import SegmentationHandler
from .utils.data_structures import Metadata, DrawingType
from .utils.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
from .utils.text_detection import TextDetection
from .utils.json_response_converter import json_response_converter
from utils.messages import MESSAGES

# Set up logging
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables from .env.dev")
load_dotenv(".env.dev")

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIRECTORY = Path("static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

FEEDBACK_DIRECTORY = Path("static/feedback")

FEEDBACK_DIRECTORY.mkdir(parents=True, exist_ok=True)





class Feedback(BaseModel):
    detection_id: str
    is_correct: bool



def get_text_detection(detection: Metadata, drawing_types, image):
    text = TextDetection()
    text.easy_ocr(image)

    if DrawingType.FASADE in drawing_types:
        cardinal_direction = text.get_cardinal_direction([cardinal_direction_pattern])
        detection.cardinal_direction = cardinal_direction

        if not cardinal_direction:
            detection.detection_message= MESSAGES["NO_CARDINAL_DIRECTION"]

    elif DrawingType.SITUASJONSKART in drawing_types:
                # Find scale
                scale = text.get_scale([scale_pattern])
                detection.scale = scale

                if not scale:
                    detection.detection_message = MESSAGES["NO_SCALE"]
    
    elif DrawingType.PLANTEGNING in drawing_types:
        room_text_infos = text.get_room_names([room_pattern])
        # Extract room names from the list of all detectec text
        all_room_labels = [text.text for text in room_text_infos]
        # Segment all rooms
        segmentation = SegmentationHandler()

        segmentation.run_segmentation(image)
        labels_in_room_counter, total_rooms_detected, labels_in_room = segmentation.find_text_segments(room_text_infos)
        print(f"Num of rooms contains room name: {labels_in_room_counter}, total rooms:{total_rooms_detected}")
        print(f"Room names is inside a room {labels_in_room}")
        
        # Add to metadata
        detection.room_names = all_room_labels           # all room names detected in drawinf
        detection.room_count = total_rooms_detected # total rooms detected from segmentation
        detection.rooms_with_label = labels_in_room # room names that is inside a room


        if labels_in_room_counter == 0:
            detection.detection_message = MESSAGES["NO_ROOM_NAMES"]
                    
    return detection

def detect_and_validate(image, uploaded_file):
    detection_id = str(uuid4())
    obj_det = ObjectDetectionHandler()
    drawing_types, bbox, confidence = obj_det.run_detection(image)

    
    # Store object detection results in Metadata class. TODO: Write cleaner with fewer lines?
    detection = Metadata(
        detection_id=detection_id,
        filename=uploaded_file.filename,
        drawing_types=drawing_types,
        bbox=bbox,
        confidence=confidence

    )
    if set(drawing_types) & {DrawingType.FASADE, DrawingType.PLANTEGNING, DrawingType.SNITT, DrawingType.SITUASJONSKART}:
        detection = get_text_detection(detection, drawing_types, image)
        

    #detection = process_text_and_detection(detection, drawing_types, image)
              
    return detection



# Health check endpoint - can be improved
@app.get("/health/")
async def health_check():
    return {"status": "ok"}

def process_file(uploaded_file: UploadFile) -> Optional[Metadata]:
    #detection_response = []
    
    file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"

    with open(file_path, "wb") as file_object:
        file_object.write(uploaded_file.file.read())

    if uploaded_file.filename.lower().endswith('.pdf'):
        input_images = convert_from_path(file_path)
        for image in input_images:
            metadata = detect_and_validate(image, uploaded_file)

    elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        image = cv2.imread(file_path)
        metadata = detect_and_validate(image, uploaded_file)
        #detection_response.append(detection)
    else:
        metadata = None
        

    os.remove(file_path)
    
    #if detection_response:
    #    return detection_response[0]

    return metadata



feedback_store = {}

@app.post("/detect/")
async def detect_objects(uploaded_files: List[UploadFile]):

    with ThreadPoolExecutor() as executor:
        metadata_results = list(executor.map(process_file, uploaded_files))
        for metadata in metadata_results:
            feedback_store[metadata.detection_id] = metadata.model_dump()
            print(feedback_store[metadata.detection_id])
        
        return metadata_results
        
    

def save_feedback_data(feedback_data: dict, filename):
    if not FEEDBACK_DIRECTORY.exists():
        FEEDBACK_DIRECTORY.mkdir(parents=True, exist_ok=True)

    #file_path = f"{FEEDBACK_DIRECTORY}/{filename}.json"
    file_path = FEEDBACK_DIRECTORY / f"{filename}.json"
    with open(file_path, "w") as json_file:
        json.dump(feedback_data, json_file, indent=4)
    
    print(f"Feedback saved to {file_path}")

@app.post("/feedback")
async def submit_feedback(detection_id: str = Query(...), is_detection_correct: bool = Form(...)):
    # detection id as a query parameter
    
    metadata = feedback_store[detection_id]
    print(metadata)
    filename = metadata["filename"]

    feedback_data = {
        "metadata":metadata,
        "is_detection_correct": is_detection_correct
    }


    save_feedback_data(feedback_data, filename)


    return {"message": "Feedback recieved", "filename": filename, "Detection correct": is_detection_correct, "Feedback metadata": feedback_store}


# Add a new endpoint to check the log file
@app.get("/logs/")
async def get_logs():
    try:
        with open('/app/logs/app.log', 'r') as log_file:
            logs = log_file.read()
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error fetching logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch logs")


#app.include_router(feedback_router)




