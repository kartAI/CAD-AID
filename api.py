from fastapi import FastAPI, File, UploadFile, HTTPException
from contextlib import asynccontextmanager
from utils.detection_handler import DetectionHandler, SegmentationHandler
from utils.models_manager import Segmentation
from utils.text_manager import TextDetection  # Correctly import from text_manager
from utils.regex_patterns import room_pattern
from dotenv import load_dotenv
import os
import shutil
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

# Define the lifespan function
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        global detection_handler
        logger.info("Initializing detection handler")
        detection_handler = DetectionHandler()

        global segmentation_handler
        logger.info("Initializing segmentation handler")
        segmentation_model = Segmentation()
        segmentation_handler = SegmentationHandler(segmentation_model)

        yield

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during startup: {str(e)}")
    
    finally:
        logger.info("Shutting down detection handler")
        pass

# Re-instantiate the FastAPI app with the lifespan function
app = FastAPI(lifespan=lifespan)

# Health check endpoint
@app.get("/health/")
async def health_check():
    return {"status": "ok"}

# Detect endpoint for handling object detection
@app.post("/detect/")
async def detect(file: UploadFile = File(...)):
    try:
        logger.info(f"Received request for detection: {file.filename}")
        # Save uploaded file to a temporary location
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")
        
        # Update the prediction image path for detection handler
        detection_handler.set_prediction_image(file_location)
        
        # Run detection
        logger.info("Running detection")
        detection_handler.check_and_execute()
        
        # Return results
        logger.info(f"Detection completed for file: {file.filename}")
        return {"filename": file.filename, "detection": "Detection completed successfully."}
    except Exception as e:
        logger.error(f"Error during detection for file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Segment endpoint for handling segmentation
@app.post("/segment/")
async def segment(file: UploadFile = File(...)):
    try:
        logger.info(f"Received request for segmentation: {file.filename}")
        # Save uploaded file to a temporary location
        file_location = f"temp_files/{file.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Uploaded file saved to {file_location}")

        # Perform segmentation
        logger.info("Performing segmentation...")
        segmentation_handler.run_segmentation(file_location)
        
        text_detector = TextDetection()
        text_detector.image_path = file_location  # Use the uploaded file
        room_text_infos = text_detector.get_target_text([room_pattern])
        logger.info(f"Text detection completed. Found {len(room_text_infos)} potential room texts.")
        
        # Find text segments in the detected rooms
        segmentation_handler.find_text_segments(room_text_infos)
        true_count, false_count = segmentation_handler.count_rooms()

        logger.info(f"Number of rooms with room label: {true_count}")
        logger.info(f"Number of rooms without room label: {false_count}")

        # Add logging before returning results
        logger.info(f"Segmentation completed for file: {file.filename}")
        if true_count == 0 and false_count == 0:
            logger.warning(f"No rooms were detected in file: {file.filename}")
            return {
                "filename": file.filename,
                "segmentation": "Segmentation completed, but no rooms were detected.",
                "rooms_with_labels": 0,
                "rooms_without_labels": 0,
            }
        else:
            logger.info(f"Segmentation successful. Rooms with labels: {true_count}, Rooms without labels: {false_count}")
            return {
                "filename": file.filename,
                "segmentation": "Segmentation completed successfully.",
                "rooms_with_labels": true_count,
                "rooms_without_labels": false_count,
            }

    except Exception as e:
        logger.error(f"Error during segmentation for file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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