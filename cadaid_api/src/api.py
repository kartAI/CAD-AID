from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from pathlib import Path
from pdf2image import convert_from_path
import cv2
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
from concurrent.futures import ThreadPoolExecutor
import yaml
import asyncio

from fastapi import APIRouter, Body
from pydantic import BaseModel
import json

from .utils.logger import cadaid_logger
from .utils.object_detection import ObjectDetectionHandler
from .utils.segmentation_handler import SegmentationHandler
from .utils.data_structures import Metadata, DrawingType
from .utils.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
from .utils.text_detection import TextDetection
from .utils.json_response_converter import json_response_converter
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
FEEDBACK_DIRECTORY = "feedback"

os.makedirs(FEEDBACK_DIRECTORY, exist_ok=True)

class_name_map = {0:'fasade', 1: 'plantegning', 2:'situasjonskart', 3:'snitt'}

class FeedbackModel(BaseModel):
    filename: str
    drawing_types: list
    is_correct: bool

def map_drawing_types(drawing_types):
    return [class_name_map[int(drawing_type)] for drawing_type in drawing_types]

def extract_metadata(image, uploaded_file):
    obj_det = ObjectDetectionHandler()
    drawing_types, bbox, confidence=obj_det.run_detection(image)

    drawing_types = map_drawing_types(drawing_types)
    bbox =  [bbox_tensor.tolist() for bbox_tensor in bbox]
    confidence = [conf.item() for conf in confidence]

    return drawing_types,bbox, confidence

def process_text_and_detection(detection, drawing_types, image):
    text = TextDetection()
    text.easy_ocr(image)

    for dtype in drawing_types:
            if dtype == DrawingType.FASADE:
                # Find cardinal direction
                cardinal_direction = text.get_cardinal_direction([cardinal_direction_pattern])

                detection.cardinal_direction = cardinal_direction
               

            elif dtype == DrawingType.SITUASJONSKART:
                # Find scale
                scale = text.get_scale([scale_pattern])
                detection.scale = scale
                

            elif dtype == DrawingType.PLANTEGNING: # TODO: does not work as intended 
                room_text_infos = text.get_room_names([room_pattern])
                room_names = [text.text for text in room_text_infos]
                detection.room_names = room_names
                segmentation = SegmentationHandler()
        
                segmentation.run_segmentation(image)
                segmentation_results = segmentation.find_text_segments(room_text_infos)
                true_count,false_count = segmentation.count_rooms()
                detection.room_count = true_count + false_count

    return detection

def detect_and_validate(image, uploaded_file):
    
    drawing_types, bbox, confidence = extract_metadata(image, uploaded_file)
    
    # Store object detection results in Metadata class. TODO: Write cleaner with fewer lines?
    detection = Metadata(
        filename=uploaded_file.filename,
        drawing_types=drawing_types,
        bbox=bbox,
        confidence=confidence

    )
    detection = process_text_and_detection(detection, drawing_types, image)
              
    return detection



# Health check endpoint - can be improved
@app.get("/health/")
async def health_check():
    return {"status": "ok"}

def process_file(uploaded_file):
    detection_response = []
    
    file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"

    with open(file_path, "wb") as file_object:
        file_object.write(uploaded_file.file.read())

    if uploaded_file.filename.lower().endswith('.pdf'):
        input_images = convert_from_path(file_path)
        for image in input_images:
            detection_response.append(detect_and_validate(image, uploaded_file))

    elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        image = cv2.imread(file_path)
        detection = (detect_and_validate(image, uploaded_file))
        detection_response.append(detection)
        

    os.remove(file_path)
    if detection_response:
        return detection_response[0]
    
    return None

metadata_store = {}
response_store = []

@app.post("/detect/")
async def detect_objects(uploaded_files: List[UploadFile]):

    with ThreadPoolExecutor() as executor:
        metadata_results = list(executor.map(process_file, uploaded_files))
        response = json_response_converter(metadata_results)
        response_store.append(response)
        
        for metadata in metadata_results:
            if metadata:
                metadata_store[metadata.filename] = metadata
        
        return response
    


@app.get("/feedbacks", response_model=list[Metadata])
async def submit_feedback():
    return response_store


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




