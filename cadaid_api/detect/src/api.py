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
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from shared.utils.logger import cadaid_logger
from shared.utils.object_detection import ObjectDetectionHandler
from shared.utils.segmentation_handler import SegmentationHandler
from shared.utils.data_structures import Metadata, DrawingType, DrawingInstance, TextInfo
from shared.utils.regex_patterns import (
    scale_pattern,
    cardinal_direction_pattern,
    room_pattern,
    gnr_bnr_pattern,
    areal_pattern
)
from shared.utils.text_detection import TextDetection
from shared.utils.json_response_converter import json_response_converter
#from shared.auth import get_api_key



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
             # swagger_ui_init_oauth={
             #     "apiKeyName": "X-API-KEY"
            #  }
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
    
    def process_plantegning_instance(self, image_path, detected_text: TextInfo, text_detection: TextDetection):
        #scale = text.get_scale_in_region([scale_pattern], bbox)
        #gnr_bnr = text.get_gnr_bnr_in_region([gnr_bnr_pattern], bbox)
        
        def extract_areal(detected_areal_string):
            number_pattern = r"\d+([.,]+d+)?"
            areal_as_float = []
            for areal in detected_areal_string:
                match = re.search(number_pattern, areal)
                if match:
                    areal_float = float(match.group().replace(',', '.'))
                    areal_as_float.append(areal_float)
            return areal_as_float

        # filter all detected text by roomnames
        textfilter_by_roomlabels = text_detection.get_target_text(detected_text,room_pattern)
        segmentation = SegmentationHandler()
        results = segmentation.run_segmentation(image_path)

        # Filter room names found in segmented masks
        filtered_rooms_by_polygons = segmentation.filter_text_within_polygons(results, textfilter_by_roomlabels)

        room_names = []
        for text_info in filtered_rooms_by_polygons:
            room = text_info.text
            room_names.append(room)
        # Filter text by areal
        textfiltered_by_areal = text_detection.get_rom_areal(detected_text, areal_pattern)
        # Filter room areal found in segmented masks
        filtered_areal_by_polygons = segmentation.filter_text_within_polygons(results, textfiltered_by_areal)
        areal_text = []
        for text_info in filtered_areal_by_polygons:
            prob = text_info.probability
            areal_text_raw = text_info.text
            if prob > 0.80:
                areal_text.append(areal_text_raw)
        areal = extract_areal(areal_text)
        total_areal = sum(areal)
    
        return room_names, total_areal
    
    
    def create_detection_instance(self, image, drawing_type, bbox, conf, drawing_type_map) -> DrawingInstance:
        dtype = drawing_type_map.get(int(drawing_type), "unknown").name.lower()
        instance = DrawingInstance(drawing_type=dtype,bbox=bbox.tolist(),confidence=conf.item())

        text_detection = TextDetection()
        detected_text = text_detection.pytesseract_ocr(image)

        if dtype in [DrawingType.FASADE.name.lower(), DrawingType.SITUASJONSKART.name.lower()]:
            instance.cardinal_direction = text_detection.get_cardinal_direction_in_region(detected_text,[cardinal_direction_pattern], bbox)
            #instance.cardinal_direction = text_detection.get_cardinal_direction(detected_text,cardinal_direction_pattern, bbox)
            instance.scale = text_detection.get_scale_in_region(detected_text,[scale_pattern], bbox)
            #instance.scale = text_detection.get_scale(detected_text, scale_pattern)
            #instance.gnr_bnr = text.get_gnr_bnr_in_region([gnr_bnr_pattern], bbox)
        
        elif dtype == DrawingType.SNITT.name.lower():
            instance.scale = text_detection.get_scale_in_region(detected_text,[scale_pattern], bbox)
        
        elif dtype == DrawingType.PLANTEGNING.name.lower():
            try:
                #instance.gnr_bnr = text_detection.get_gnr_bnr()
                #instance.scale, instance.gnr_bnr, instance.room_names = self.process_plantegning_instance(image_path,bbox, text)
                instance.room_names, instance.total_areal = self.process_plantegning_instance(image, detected_text, text_detection)


            except Exception as e:
                    logger.error(f"Error processing plantegning instance: {str(e)}")
        
        return instance
    
    
    def run_detection_pipeline(self, image, uploaded_file) -> List[DrawingInstance]:
        start_time = time.time()
        preprocess_start = time.time()
        
        obj_det = ObjectDetectionHandler()
        preprocess_end = time.time()

        inference_start = time.time()
        drawing_types, bboxes, confidences = obj_det.run_detection(image)
        inference_end = time.time()

        
        drawing_type_map = {
            0: DrawingType.FASADE,
            1: DrawingType.PLANTEGNING,
            2: DrawingType.SITUASJONSKART,
            3: DrawingType.SNITT
        }

        return [self.create_detection_instance(image, drawing_type, bbox, conf, drawing_type_map)
               for drawing_type, bbox, conf in zip(drawing_types, bboxes, confidences)]
        

    def detect_and_validate(self, image, uploaded_file) -> Metadata:
        detections = self.run_detection_pipeline(image, uploaded_file)
        return Metadata(filename=uploaded_file.filename, detections=detections)

    def process_file_type(self, uploaded_file, file_path) -> List[Metadata]:
        detection_response = []
        try:
            if uploaded_file.filename.endswith("pdf"):
                input_images = convert_from_path(file_path)
                for image in input_images:
                    detection = self.detect_and_validate(image, uploaded_file)
                    detection_response.append(detection)
            elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image = cv2.imread(file_path)
                if image is None:
                    raise DetectionError(f"Could not read image file '{uploaded_file.filename}'")
                
                detection = self.detect_and_validate(image, uploaded_file)
                detection_response.append(detection)
            else:
                raise ValueError(f"Unsupported file format: {uploaded_file.filename}")
        except DetectionError as de:
            logger.error(str(de))

        except Exception as e:
            logger.error(f"Error processing file '{uploaded_file.filename}': {str(e)}")
        
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
            
    def process_file(self, uploaded_file: UploadFile) -> Metadata:
        if not uploaded_file or not uploaded_file.filename:
            logger.error("File missing filename")
            return None
        
        file_path = self.save_uploaded_file(uploaded_file)
        file_hash = compute_file_hash(file_path)

        if file_hash in self.cache:
            logger.info(f"File '{uploaded_file.filename}' found in cache. Skipping processing.")
            return self.cache[file_hash]
        
        detection_response = self.process_file_type(uploaded_file, file_path)
        if detection_response:
            self.cache[file_hash] = detection_response
        
        #self.clean_up_temp_file(file_path) # TODO: Clean up after a feedback is given/not given. Currently implemented in feedback api

        if len(detection_response)>0:
            return detection_response[0]
        return Metadata()
    
detection_service = DetectionService()

max_workers = 6

@app.post("/")
async def detect_objects(uploaded_files: List[UploadFile], 
                         #api_key: str = Depends(get_api_key)
                         ):
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
                    metadata_results.append(result.convert_to_dict())
                    
                    detection_service.metadata[result.filename] = result.convert_to_dict()
                
    
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Detection completed in {elapsed_time} seconds")

        if not metadata_results:
            raise HTTPException(status_code=400, detail="No valid results found")
        
        uploaded_files = os.listdir(UPLOAD_DIRECTORY)
        logger.info(f"Uploaded files detection: {uploaded_files}")

        return metadata_results
        #return json_response_converter(metadata_results)
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