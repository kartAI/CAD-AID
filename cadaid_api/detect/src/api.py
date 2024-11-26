from fastapi import FastAPI, UploadFile, HTTPException, Depends, status, Security
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_403_FORBIDDEN
from pathlib import Path
from pdf2image import convert_from_path
import cv2
from concurrent.futures import ThreadPoolExecutor
from typing import List
import datetime
import os
import time
import hashlib
import json
import re
from contextlib import asynccontextmanager
import asyncio
from io import BytesIO
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from shared.utils.storage_handler import StorageHandler
from shared.utils.logger import cadaid_logger
from shared.utils.object_detection import ObjectDetectionHandler
from shared.utils.segmentation_handler import SegmentationHandler
from shared.utils.text_detection import TextDetection, TextProximityFilter
from shared.utils.data_structures import Metadata, DrawingType, DrawingInstance, TextInfo
from shared.utils.regex_patterns import (
    scale_pattern,
    cardinal_direction_pattern,
    room_pattern,
    gnr_bnr_pattern,
    areal_pattern
)

from shared.utils.json_response_converter import json_response_converter
from shared.auth import get_api_key



# Set up logging
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

@asynccontextmanager
async def lifespan(_: FastAPI): 
    try:
        logger.info("Starting up Detect API")
        # Initialization checks
        await asyncio.sleep(10)
        logger.info("Detect API ready")
        yield
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        logger.info("Shutting down Detect API")
    

app = FastAPI(lifespan=lifespan,
              root_path="/detect",
              root_path_in_servers=True,
              title="Detect API",
              description="API for object detection and text extraction using CADAID system",
              version="1.0.0",
              docs_url="/docs",
              open_api_url="/openapi.json",
              openapi_tags=[{
                "name": "Detection",
                "description": "API for object detection and text extraction using CADAID system"
              }],
              swagger_ui_init_oauth={
                  "apiKeyName": "X-API-KEY"
              }
            )


# Add middleware to handle keepalive connections
@app.middleware("http")
async def add_keepalive_header(request, call_next):
    response = await call_next(request)
    response.headers["Connection"] = "keep-alive"
    response.headers["Keep-Alive"] = "timeout=300"
    return response

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip middleware to compress responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

#UPLOAD_DIRECTORY = Path("/app/static/uploads")
#UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

UPLOAD_DIRECTORY = "/app/upload_files"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

METADATA_STORE = "/app/metadata_files_store"
os.makedirs(METADATA_STORE, exist_ok=True)



def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

class DetectionError(Exception):
    """Custom exception for detection errors"""
    pass

class DetectionService:
    def __init__(self):
        self.metadata = {}
        self.cache = {}
        self.storage = StorageHandler(use_azure=os.getenv("USE_AZURE_STORAGE", "false").lower() == "true")
    
    def process_plantegning_instance(self, image_path, detected_text: TextInfo, text_detection: TextDetection, objdet_bbox):
        """
        Perform segmentation to detect rooms and retrieve roomnames
        """
        
        logger.info("Starting plantegning instance processing")

        # First get room names
        room_names = text_detection.get_target_text(detected_text, room_pattern)
        logger.info(f"Found room names: {[room.text for room in room_names]}")

        # Now find and append areas
        room_names_with_areas = text_detection.append_areas_to_rooms(room_names, detected_text)
        logger.info(f"Found room names with areas: {[room.text for room in room_names_with_areas]}")

        segmentation = SegmentationHandler()
        results = segmentation.run_segmentation(image_path)

        # Filter room names found in segmented masks
        text_filter = TextProximityFilter()
        rooms_in_polygons = text_filter.filter_text_within_polygons(results, room_names_with_areas)

        final_room_names = text_filter.check_text_within_object(rooms_in_polygons, objdet_bbox)
        
        return final_room_names
    
    
    def create_detection_instance(self, image, drawing_type, bbox, conf) -> DrawingInstance:
        """
        Extract relevant text based on detected drawing type
        """
        instance = DrawingInstance(drawing_type=drawing_type,bbox=bbox,confidence=conf)

        text_detection = TextDetection()
        text_filter = TextProximityFilter()
       
        detected_text = text_detection.pytesseract_ocr(image)

        # Add gnr/bnr detection for all drawing types
        gnr_bnr_txt_info = text_detection.get_gnr_bnr(detected_text, gnr_bnr_pattern)
        instance.gnr_bnr = text_filter.text_proximity_to_object(gnr_bnr_txt_info, bbox)
    
        if drawing_type  == DrawingType.FASADE.name.lower():
           
            cardinal_direction_txt_info = text_detection.get_cardinal_direction(detected_text, cardinal_direction_pattern)
            instance.cardinal_direction = text_filter.text_proximity_to_object(cardinal_direction_txt_info, bbox)

            scale_txt_info = text_detection.get_scale(detected_text, scale_pattern)
            instance.scale = text_filter.text_proximity_to_object(scale_txt_info, bbox)
        
        elif drawing_type == DrawingType.SNITT.name.lower():
            scale_txt_info = text_detection.get_scale(detected_text,scale_pattern)
            instance.scale = text_filter.text_proximity_to_object(scale_txt_info, bbox)

        
        elif drawing_type == DrawingType.SITUASJONSKART.name.lower():
            scale_txt_info = text_detection.get_scale(detected_text,scale_pattern)
            instance.scale = text_filter.text_proximity_to_object(scale_txt_info, bbox)
        
        elif drawing_type == DrawingType.PLANTEGNING.name.lower():
            try:
                
                instance.room_names = self.process_plantegning_instance(image, detected_text, text_detection, bbox)
                if not instance.room_names:
                    # Try rotating image if text is vertical for OCR
                    for i in range(4):
                        img = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                        instance.room_names = self.process_plantegning_instance(img, detected_text, text_detection, bbox)

                        if instance.room_names:
                            break


            except Exception as e:
                    logger.error(f"Error processing plantegning instance: {str(e)}")
        
        return instance
    
    
    def run_detection_pipeline(self, image) -> List[DrawingInstance]:
        """
        Perform object detection, text detection and/or segmentation
        """
        start_time = time.time()
        preprocess_start = time.time()
        
        obj_det = ObjectDetectionHandler()
        preprocess_end = time.time()

        inference_start = time.time()
        logger.debug("Running object detection")
        drawing_types, bboxes, confidences = obj_det.run_detection(image)
        logger.debug(f"Object detection results: {len(drawing_types)} types, {len(bboxes)} boxes, {len(confidences)} confidences")
        inference_end = time.time()

        return [self.create_detection_instance(image, drawing_type, bbox, conf)
               for drawing_type, bbox, conf in zip(drawing_types, bboxes, confidences)]
        

    def detect_and_validate(self, image, filename) -> Metadata:
        """
        Perform detection for current file
        """
        detections = self.run_detection_pipeline(image)
        return Metadata(filename=filename, detections=detections)

    def process_file_type(self, filename: str, file_path: str) -> List[Metadata]:
        """
        Process file depending on filetype and perform detection
        
        """
        detection_response = []
        try:
            if filename.endswith("pdf"):
                logger.debug(f"Processing PDF file: {filename}")
                input_images = convert_from_path(file_path)
                for image in input_images:
                    detection = self.detect_and_validate(image, filename)
                    detection_response.append(detection)
            elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                logger.debug(f"Processing image file: {filename}")
                image = cv2.imread(file_path)
                if image is None:
                    raise DetectionError(f"Could not read image file '{filename}'")
                
                detection = self.detect_and_validate(image, filename)
                detection_response.append(detection)
            else:
                raise ValueError(f"Unsupported file format: {filename}")
        except DetectionError as de:
            logger.error(str(de))

        except Exception as e:
            logger.error(f"Error processing file '{filename}': {str(e)}")
        
        return detection_response
    
    def clean_up_temp_file(self, file_path):
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")

            except Exception as e:
                logger.error(f"Error removing file '{file_path}': {str(e)}")
    
    def save_uploaded_file(self, uploaded_file):

        file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"

        with open(file_path, "wb") as file_object:
                file_object.write(uploaded_file.file.read())

        logger.info(f"File written to: {file_path}")

        return file_path
    
    class UploadFileLike:
        def __init__(self, content, filename):
            self.content = content
            self._filename = filename

        async def read(self):
            return self.content
        
        @property
        def filename(self):
            return self._filename
            
    async def process_file(self, uploaded_file: UploadFile):
        """
        Process a single uploaded file for detection and metadata generation.
        """
        try:
            logger.info(f"Starting processing for file: {uploaded_file.filename}")

            # Read file content as bytes
            file_content = await uploaded_file.read()
            logger.debug(f"File content read, size: {len(file_content)} bytes")

            # Save the uploaded file to storage (Azure or local)
            saved_file_path = self.storage.save_file(file_content, uploaded_file.filename)
            logger.info(f"File saved to: {saved_file_path}")

            # If using Azure, create a temporary local file for processing
            if self.storage.use_azure:
                temp_dir = Path("/app/temp_files")
                temp_dir.mkdir(exist_ok=True)
                temp_path = temp_dir / uploaded_file.filename

                # Download the file from Azure Blob Storage
                downloaded_content = await self.storage.get_file(uploaded_file.filename)
                if downloaded_content:
                    with open(temp_path, "wb") as f:
                        f.write(downloaded_content)
                    saved_file_path = str(temp_path)
                    logger.info(f"Downloaded file from Azure to temp location: {saved_file_path}")
                else:
                    logger.error(f"Error downloading file from Azure: {uploaded_file.filename}")
                    raise HTTPException(status_code=500, detail="Error downloading file from Azure")

            # Process the detection pipeline using the saved file path
            detection_response = self.process_file_type(uploaded_file.filename, saved_file_path)
            logger.debug(f"Detection response received: {bool(detection_response)}")

            # Clean up temporary file if using Azure
            if self.storage.use_azure and Path(saved_file_path).exists():
                Path(saved_file_path).unlink()
                logger.info(f"Removed temporary file: {saved_file_path}")

            # Handle detection response
            if detection_response:
                # Cache the detection response for the file hash
                file_hash = hashlib.md5(file_content).hexdigest()
                self.cache[file_hash] = detection_response

                # Prepare metadata for saving
                metadata = {
                    "metadata": {
                        uploaded_file.filename: detection_response[0].convert_to_dict()
                    }
                }

                logger.debug("Saving metadata")
                try:
                    # Save metadata (Azure or local)
                    self.storage.save_metadata(metadata, uploaded_file.filename)
                    logger.info("Metadata saved successfully")
                except Exception as metadata_error:
                    logger.error(f"Metadata storage error: {str(metadata_error)}")
                    raise HTTPException(status_code=500, detail="Error saving metadata")

                # Return the first detection response
                return detection_response[0]

            # If no detection response, return an empty metadata object
            logger.warning("No detection response, returning empty metadata")
            return Metadata()

        except Exception as e:
            logger.error(f"Error in process_file: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))



    
detection_service = DetectionService()

@app.post("/")
async def detect_objects(uploaded_files: List[UploadFile], 
                         api_key: str = Depends(get_api_key)
                         ):
    start_time = time.time()
    logger.info(f"Starting detection for {len(uploaded_files)} files")
    
    try:
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Debug logging
        logger.debug(f"Received files: {[f.filename for f in uploaded_files]}")
        
        # Process each file individually
        metadata_results = []
        # Create a list of tasks to process files
        tasks = []
        for uploaded_file in uploaded_files:
            if not uploaded_file.filename:
                logger.error("File missing filename")
                continue
            
            # Create task for each file
            task = asyncio.create_task(detection_service.process_file(uploaded_file))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing file: {str(result)}")
                continue
            if result:
                if isinstance(result, Metadata):
                    metadata_results.append(result.convert_to_dict())
                    detection_service.metadata[result.filename] = result.convert_to_dict()
                elif isinstance(result, list):
                    for item in result:
                        if isinstance(item, Metadata):
                            metadata_results.append(item.convert_to_dict())
                            detection_service.metadata[item.filename] = item.convert_to_dict()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Detection completed in {elapsed_time} seconds")

        if not metadata_results:
            logger.error("No valid results found")
            raise HTTPException(status_code=400, detail="No valid results found")
        
        return metadata_results
    
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/detection-results")
async def get_all_detection_results():
    if not detection_service.metadata:
        raise HTTPException(status_code=404, detail="No metadata found")
    return {'metadata': detection_service.metadata,
                'filepath': UPLOAD_DIRECTORY}

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
                #"Content-Length": "100"  # Add explicit content length
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Endpoint to check log file
@app.get("/logs/")
async def get_logs():
    try:
        with open('/app/logs/app.log', 'r') as log_file:
            logs = log_file.read()
        return JSONResponse(
            content={"logs": logs},
            headers={
                "Content-Type": "application/json",
            }
        )
    except Exception as e:
        logger.error(f"Error fetchcing logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch logs")