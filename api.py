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

# Segment endpoint for handling segmentation
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

        # Perform segmentation
        logger.info("Performing segmentation...")
        text_detector = TextDetection()
        room_text_infos = text_detector.get_target_text([room_pattern])
        
        # Find text segments in the detected rooms
        segmentation_handler.find_text_segments(room_text_infos)
        true_count, false_count = segmentation_handler.count_rooms()

        logger.info(f"Number of rooms with room label: {true_count}")
        logger.info(f"Number of rooms without room label: {false_count}")

        # Return segmentation results
        return {
            "filename": file.filename,
            "segmentation": "Segmentation completed successfully.",
            "rooms_with_labels": true_count,
            "rooms_without_labels": false_count,
        }

    except Exception as e:
        logger.error(f"Error during segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))