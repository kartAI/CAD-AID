from fastapi import FastAPI, File, UploadFile, HTTPException
from utils.detection_handler import DetectionHandler
from dotenv import load_dotenv
import os
import shutil

# Load environment variables
load_dotenv(".env.dev")

app = FastAPI()

# Initialize the detection handler
detection_handler = DetectionHandler()

@app.post("/detect/")
async def detect(file: UploadFile = File(...)):
    # Save uploaded file to disk
    file_location = f"temp_files/{file.filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update the prediction image path in the environment variable
    os.environ["PREDICTION_IMAGE_PATH"] = file_location
    
    # Run detection
    try:
        detection_handler.check_and_execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Return results
    return {"filename": file.filename, "detection": "Detection completed successfully."}

@app.post("/segment/")
async def segment(file: UploadFile = File(...)):
    # Save uploaded file to disk
    file_location = f"temp_files/{file.filename}"
    os.makedirs(os.path.dirname(file_location), exist_ok=True)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update the prediction image path in the environment variable
    os.environ["PREDICTION_IMAGE_PATH"] = file_location
    
    # Initialize the segmentation handler
    segmentation_handler = detection_handler.segmentation_handler
    
    # Run segmentation
    try:
        room_text_infos = segmentation_handler.find_text_segments([])
        true_count, false_count = segmentation_handler.count_rooms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Return segmentation results
    return {"filename": file.filename, "segmentation": "Segmentation completed successfully.", "rooms_with_labels": true_count, "rooms_without_labels": false_count}
        