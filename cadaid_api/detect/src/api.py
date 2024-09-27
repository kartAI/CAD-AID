from fastapi import FastAPI, UploadFile, HTTPException
from pathlib import Path
from pdf2image import convert_from_path
import cv2
from concurrent.futures import ThreadPoolExecutor
from typing import List
import os
from dotenv import load_dotenv

from shared.utils.logger import cadaid_logger
from shared.utils.object_detection import ObjectDetectionHandler
from shared.utils.segmentation_handler import SegmentationHandler
from shared.utils.data_structures import Metadata, DrawingType
from shared.utils.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
from shared.utils.text_detection import TextDetection
from shared.utils.json_response_converter import json_response_converter

# Set up logging
logger = cadaid_logger(__name__)

# Load environment variables
logger.info("Loading environment variables")
load_dotenv("/app/shared/.env.dev")

app = FastAPI()

UPLOAD_DIRECTORY = Path("/app/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

class DetectionService:
    def __init__(self):
        self.metadata.store = {}
        
    def detect_and_validate(self, image, uploaded_file):
        obj_det = ObjectDetectionHandler()
        
        # Return lists of tensors
        drawing_types, bbox, confidence = obj_det.run_detection(image)
        
        # Map class indices to labels using DrawingType enum
        drawing_types = [DrawingType(int(drawing_type)).name.lower() for drawing_type in drawing_types]
        bbox = [bbox_tensor.tolist() for bbox_tensor in bbox]
        confidence = [conf.item() for conf in confidence]
        
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
        detection_response = []
        
        file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"
        
        with open(file_path, "wb") as file_object:
            file_object.write(uploaded_file.file.read())
            
        if uploaded_file.filename.endswith(".pdf"):
            input_images = convert_from_path(file_path)
            for image in input_images:
                detection_response.append(self.detect_and_validate(image, uploaded_file))
                
        elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(file_path)
            detection = self.detect_and_validate(image, uploaded_file)
            detection_response.append(detection)
            
        os.remove(file_path)
        
        if len(detection_response) > 0:
            return detection_response[0]
        return Metadata()
    
detection_service = DetectionService()

@app.post("/detect")
async def detect_objects(uploaded_files: List[UploadFile]):
    with ThreadPoolExecutor() as executor:
        metadata_results = list(executor.map(detection_service.process_file, uploaded_files))
        for metadata in metadata_results:
            detection_service.metadata.store[metadata.filename] = metadata
            
        return json_response_converter(metadata_results)
    