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
from dotenv import load_dotenv
import time
import hashlib
import json
from contextlib import asynccontextmanager
import asyncio
from shared.utils.logger import cadaid_logger
from shared.utils.object_detection import ObjectDetectionHandler
from shared.utils.segmentation_handler import SegmentationHandler
from shared.utils.data_structures import Metadata, DrawingType
from shared.utils.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
from shared.utils.text_detection import TextDetection
from shared.utils.json_response_converter import json_response_converter
from shared.auth import get_api_key
from fastapi.responses import JSONResponse

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

UPLOAD_DIRECTORY = Path("/app/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

class DetectionService:
    def __init__(self):
        self.metadata = {}
        self.cache = {}
        
    def detect_and_validate(self, image, uploaded_file):
        start_time = time.time()
        preprocess_start = time.time()
        
        obj_det = ObjectDetectionHandler()
        preprocess_end = time.time()
        
        # Return lists of tensors
        inference_start = time.time()
        drawing_types, bbox, confidence = obj_det.run_detection(image)
        inference_end = time.time()

        # Mapping class indices to labels using DrawingType enum
        drawing_type_map = {
            0: DrawingType.FASADE,
            1: DrawingType.PLANTEGNING,
            2: DrawingType.SITUASJONSKART,
            3: DrawingType.SNITT
        }
        
        # Map class indices to labels using DrawingType enum
        postprocess_start = time.time()
        drawing_types = [drawing_type_map.get(int(drawing_type), "unknown").name.lower() for drawing_type in drawing_types]
        bbox = [bbox_tensor.tolist() for bbox_tensor in bbox]
        confidence = [conf.item() for conf in confidence]
        postprocess_end = time.time()
        
        total_time = time.time() - start_time
        
        # Log metrics to a file
        with open("file_processing_metrics.txt", "a") as f:
            f.write(f"File: {uploaded_file.filename}, Image Size: {image.size}, "
                    f"Total Time: {total_time} s, Preprocessing: {preprocess_end - preprocess_start} s, "
                    f"Inference: {inference_end - inference_start} s, Postprocessing: {postprocess_end - postprocess_start} s\n")
        
        logger.info(f"Detected results for {uploaded_file.filename}: {drawing_types}, {bbox}, {confidence}")
        
        # Store object detection results in Metadata class
        detection = Metadata(
            filename=uploaded_file.filename,
            drawing_types=drawing_types,
            bbox=bbox,
            confidence=confidence,
            cardinal_direction=None,
            scale=None,
            room_names=None
        )
        
        text = TextDetection()
        text.easy_ocr(image)
        
        for dtype in drawing_types:
            if dtype == DrawingType.FASADE.name.lower():
                # Find cardinal direction
                cardinal_direction = text.get_cardinal_direction([cardinal_direction_pattern])
                detection.cardinal_direction = cardinal_direction
                
            elif dtype == DrawingType.SITUASJONSKART.name.lower():
                # Find scale
                scale = text.get_scale([scale_pattern])
                detection.scale = scale
                
            elif dtype == DrawingType.PLANTEGNING.name.lower():
                try:
                    room_text_infos = text.get_room_names([room_pattern])
                    room_names = [text.text for text in room_text_infos]
                    detection.room_names = room_names
                    
                    segmentation = SegmentationHandler()
                    segmentation.run_segmentation(image)
                    segmentation_results = segmentation.find_text_segments(room_text_infos)
                    
                    segmentation_data = segmentation_results
                    
                except Exception as e:
                    logger.error(f"Error processing plantegning: {str(e)}")
                    
        return detection
    
    def process_file(self, uploaded_file):
        if not uploaded_file or not uploaded_file.filename:
            logger.error("File missing filename")
            return None
        
        detection_response = []
        file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"


        try:
            with open(file_path, "wb") as file_object:
                file_object.write(uploaded_file.file.read())
            logger.debug(f"File written to: {file_path}")

            # Compute the file hash to check if the file has been processed before
            file_hash = compute_file_hash(file_path)
            if file_hash in self.cache:
                logger.info(f"File '{uploaded_file.filename}' found in cache. Skipping processing.")
                return self.cache[file_hash]
            
            # Process the file if not found in cache    
            if uploaded_file.filename.endswith(".pdf"):
                logger.debug(f"Processing PDF file '{uploaded_file.filename}'")
                input_images = convert_from_path(file_path)
                for image in input_images:
                    detection_response.append(self.detect_and_validate(image, uploaded_file))
                    
            elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                logger.debug(f"Processing image file '{uploaded_file.filename}'")
                image = cv2.imread(file_path)
                if image is None:
                    raise ValueError(f"Could not read image file '{uploaded_file.filename}'")
                detection = self.detect_and_validate(image, uploaded_file)
                detection_response.append(detection)
            else:
                raise ValueError(f"Unsupported file format: {uploaded_file.filename}")

            # Store the detection results in cache
            if detection_response:
                self.cache[file_hash] = detection_response
                logger.debug(f"Cached results for file '{uploaded_file.filename}'")

        except Exception as e:
            logger.error(f"Error processing file '{uploaded_file.filename}': {str(e)}")
            return None
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing file '{file_path}': {str(e)}")

        
        if len(detection_response) > 0:
            return detection_response[0]
        return Metadata()
    
detection_service = DetectionService()

max_workers = 6

@app.post("/")
async def detect_objects(uploaded_files: List[UploadFile], api_key: str = Depends(get_api_key)):
    start_time = time.time()
    logger.info(f"Starting detection for {len(uploaded_files)} files")
    
    try:
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Debug logging
        logger.debug(f"Received files: {[f.filename for f in uploaded_files]}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Process each file individually
            metadata_results = []
            for uploaded_file in uploaded_files:
                if not uploaded_file.filename:
                    logger.error("File missing filename")
                    continue
                result = detection_service.process_file(uploaded_file)
                if result:
                    metadata_results.append(result)
                    detection_service.metadata[result.filename] = result

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Detection completed in {elapsed_time} seconds")

        if not metadata_results:
            raise HTTPException(status_code=400, detail="No valid results found")
        
        return json_response_converter(metadata_results)
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
                "Content-Length": "100"  # Add explicit content length
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