from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from utils.detection_handler import DetectionHandler, SegmentationHandler
from utils.models_manager import ObjectDetection, Segmentation
from utils.text_manager import TextDetection
from utils.regex_patterns import room_pattern
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from utils.logger import cadaid_logger
from typing import List
from concurrent.futures import ThreadPoolExecutor
import yaml
import asyncio

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

    
# Define dependency injection for handlers
def get_detection_handler():
    return DetectionHandler()

def get_segmentation_handler():
    return SegmentationHandler()

# Health check endpoint - can be improved
@app.get("/health/")
async def health_check():
    return {"status": "ok"}

async def process_file(file: UploadFile, is_detection: bool, visualize: bool, handler):
    try:
        logger.info(f"Processing file: {file.filename}")
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.info(f"Uploaded file saved to {file_location}")

        if is_detection:
            handler.set_prediction_image(file_location)
            handler.check_and_execute()
            
            # Get the classes from data.yaml
            with open("models_to_register/detection_model/data.yaml", "r") as f:
                data = yaml.safe_load(f)
                valid_classes = set(data["names"])

            detected_classes = set(handler.detection.drawing_type)
            matched_classes = detected_classes.intersection(valid_classes)
            unmatched_classes = detected_classes - valid_classes

            result = {
                "filename": file.filename,
                "drawing_types": [{"type": t, "confidence": c} for t, c in zip(handler.detection.drawing_type, handler.detection.confidences)],
                "matched_classes": list(matched_classes),
                "unmatched_classes": list(unmatched_classes),
                "cardinal_direction": handler.detection.cardinal_direction,
                "scale": handler.detection.scale,
                "room_names": handler.detection.room_names
            }
            if visualize:
                result["visualization"] = handler.visualize_detection(file_location)
        else:
            handler.set_prediction_image(file_location)
            handler.run_segmentation(file_location)
            text_detector = TextDetection()
            text_detector.image_path = file_location
            room_text_infos = text_detector.get_target_text([room_pattern])
            handler.find_text_segments(room_text_infos)
            true_count, false_count = handler.count_rooms()
            result = {
                "filename": file.filename,
                "segmentation": "Segmentation completed successfully.",
                "rooms_with_labels": true_count,
                "rooms_without_labels": false_count,
            }
            if visualize:
                result["visualization"] = handler.visualize_segmentation(file_location)

        os.remove(file_location)
        logger.info(f"Temporary file {file_location} removed")
        return result
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise

# Detect endpoint for handling object detection
@app.post("/detect/")
async def detect(files: List[UploadFile] = File(...), visualize: bool = False, detection_handler: DetectionHandler = Depends(get_detection_handler)):
    try:
        tasks = [process_file(file, True, visualize, detection_handler) for file in files]
        results = await asyncio.gather(*tasks)
        return results
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, IOError):
            raise HTTPException(status_code=500, detail="File processing error")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

# Segment endpoint for handling segmentation
@app.post("/segment/")
async def segment(files: List[UploadFile] = File(...), visualize: bool = False, segmentation_handler: SegmentationHandler = Depends(get_segmentation_handler)):
    try:
        tasks = [process_file(file, False, visualize, segmentation_handler) for file in files]
        results = await asyncio.gather(*tasks)
        return results
    except Exception as e:
        logger.error(f"Error during segmentation: {str(e)}")
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        elif isinstance(e, IOError):
            raise HTTPException(status_code=500, detail="File processing error")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

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