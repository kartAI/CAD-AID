from fastapi import FastAPI, UploadFile, HTTPException, Depends, status, Security, File
from fastapi.middleware.gzip import GZipMiddleware
from starlette.status import HTTP_403_FORBIDDEN
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor
from typing import List, Annotated
import os
from dotenv import load_dotenv
import time
import hashlib
import json
from sqlalchemy.orm import Session
from shared.utils.logger import cadaid_logger
#from services.detection_service import DetectionService
#from shared.utils.object_detection import ObjectDetectionHandler
#from shared.utils.segmentation_handler import SegmentationHandler
#from shared.utils.text_detection import TextDetection
from .services.object_detection import ObjectDetectionHandler
from .services.segmentation_handler import SegmentationHandler
from .services.text_detection import TextDetection
from .services.detection_service import DetectionService

from shared.auth import get_api_key

from shared.utils.storage_mechanisms import MetadataStorage, InMemoryMetadataStorage, DatabaseMetadataStorage
from shared.db.db import get_session

# Set up logging
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

app = FastAPI(root_path="/detect",
              title="Detect API",
              description="API for object detection and text extraction using CADAID system",
              version="1.0.0",
              docs_url="/docs",
              open_api_url="/openapi.json",
              openapi_tags=[{
                "name": "Detection",
                "description": "API for object detection and text extraction using CADAID system"
              }],
              #swagger_ui_init_oauth={
                  #"apiKeyName": "X-API-KEY"
              #}
            
            )


app.add_middleware(GZipMiddleware, minimum_size=1000)

UPLOAD_DIRECTORY = Path("/app/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)



"""def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()"""

def get_in_memory_storage():
    return InMemoryMetadataStorage()

def get_database_storage(session: Session = Depends(get_session)):
    return DatabaseMetadataStorage(session)


def get_detection_service(
        obj_det_handler: ObjectDetectionHandler = Depends(),
        text_handler: TextDetection = Depends(),
        segmentation_handler: SegmentationHandler = Depends(),
        storage: MetadataStorage = Depends(get_in_memory_storage),
        logger = Depends(cadaid_logger)
        ):
    return DetectionService(obj_det_handler, text_handler, segmentation_handler, storage, logger)

#detection_service = DetectionService()

max_workers = 6

@app.post("/")
async def detect_objects(
    uploaded_files: List[UploadFile] = File(...), 
    service: DetectionService = Depends(get_database_storage)
    ):#api_key: str = Depends(get_api_key)):
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(service.process_file, uploaded_files))
        
            
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Time taken for detection: {elapsed_time} seconds")
            
    return results
