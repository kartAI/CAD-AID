from fastapi import FastAPI, File, UploadFile, HTTPException
from utils.detection_handler import DetectionHandler, SegmentationHandler
from utils.models_manager import Segmentation
from dotenv import load_dotenv
import os
import shutil
import uuid
import logging
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='/app/logs/app.log', filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Initialize the detection handler
logger.info("Initializing detection handler")
detection_handler = DetectionHandler()

def download_models():
    try:
        # Example logic for downloading models without Azure authentication
        # Assume models are stored in a public location or an accessible path within the container
        logger.info(f"Downloading detection and segmentation models")

        detection_model_path = "models/detection_model"
        segmentation_model_path = "models/segmentation_model"

        # Implement logic to download or copy models from a public or accessible location
        # Example: Use wget, curl, or copy from a mounted volume

        logger.info(f"Models downloaded to: {detection_model_path}, {segmentation_model_path}")
        return detection_model_path, segmentation_model_path

    except Exception as e:
        logger.error(f"Error downloading models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download models.")

@app.on_event("startup")
def startup_event():
    try:
        # Download both models at startup
        logger.info("Downloading models at startup")
        detection_model_path, segmentation_model_path = download_models()

        # Initialize the detection handler
        global detection_handler
        logger.info("Initializing detection handler")
        detection_handler = DetectionHandler()

        # Initialize the segmentation handler
        global segmentation_handler
        logger.info("Initializing segmentation handler")
        segmentation_model = Segmentation()
        segmentation_handler = SegmentationHandler(model=segmentation_model)
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during startup: {str(e)}")

@app.post("/detect/")
async def detect(file: UploadFile = File(...)):
    try:
        # Save uploaded file to disk
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")
            
        # Update the prediction image path in the environment variable
        os.environ["PREDICTION_IMAGE_PATH"] = file_location
        
        # Run detection
        logger.info("Running detection")
        detection_handler.check_and_execute()
        
        # Return results
        return {"filename": file.filename, "detection": "Detection completed successfully."}
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment/")
async def segment(file: UploadFile = File(...)):
    try:
        # Save uploaded file to disk
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")
            
        # Update the prediction image path in the environment variable
        os.environ["PREDICTION_IMAGE_PATH"] = file_location
        
        # Initialize the segmentation handler
        logger.info("Initializing segmentation handler")
        segmentation_handler = detection_handler.segmentation_handler
        
        room_text_infos = segmentation_handler.find_text_segments([])
        true_count, false_count = segmentation_handler.count_rooms()
        
        # Return segmentation results
        return {"filename": file.filename, "segmentation": "Segmentation completed successfully.", "rooms_with_labels": true_count, "rooms_without_labels": false_count}
    
    except Exception as e:
        logger.error(f"Error during segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))