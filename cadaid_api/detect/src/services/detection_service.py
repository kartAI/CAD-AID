import time
from pdf2image import convert_from_path
import cv2
import hashlib
import os

from shared.utils.logger import cadaid_logger
#from shared.utils.object_detection import ObjectDetectionHandler
#from shared.utils.segmentation_handler import SegmentationHandler
from shared.utils.data_structures import DrawingType
from shared.utils.metadata import Metadata
from shared.utils.storage_mechanisms import MetadataStorage

from services.object_detection import ObjectDetectionHandler
from services.segmentation_handler import SegmentationHandler
from services.text_detection import TextDetection
from services.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
#from shared.utils.regex_patterns import cardinal_direction_pattern, room_pattern, scale_pattern
#from shared.utils.text_detection import TextDetection
#from shared.utils.storage_mechanisms import MetadataStorage
from pathlib import Path


UPLOAD_DIRECTORY = Path("/app/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

class DetectionService:
    def __init__(
            self, 
            obj_det_handler: ObjectDetectionHandler, 
            text_handler: TextDetection, 
            segmentation_handler: SegmentationHandler, 
            storage: MetadataStorage,
            logger):
        
        #self.metadata = {}
    
        self.cache = {}
        self.storage = storage
        self.obj_det_handler = obj_det_handler
        self.text_handler = text_handler
        self.segmentation_handler = segmentation_handler
        self.logger = logger
        
    def detect_and_validate(self, image, uploaded_file):
        start_time = time.time()
       
        # Run Object detection
        drawing_types, bbox, confidence, inference_time = self.run_object_detection(image)
        # Run text detection and/or segmentation
        detection, postprocess_time = self.postprocess_results(drawing_types, bbox, confidence, uploaded_file, image)
        
        total_time = time.time() - start_time
        
        # Log metrics to a file
        self.log_metrics(uploaded_file, image.size, total_time, inference_time, postprocess_time)
                    
        return detection
   
    def run_object_detection(self,image):
        inference_time_start = time.time()
        drawing_types, bbox, confidence = self.obj_det_handler.run_detection(image)
        inference_time_end = time.time()

        return drawing_types,bbox,confidence,inference_time_end-inference_time_start
    
    def postprocess_results(self, drawing_types, bbox, confidence, uploaded_file, image):
        postprocess_start = time.time()

        # Map class indicies to labels
        drawing_types = self.map_class_labels(drawing_types)
        # Convert YOLO bbox tensors to list
        bbox = [bbox_tensor.tolist() for bbox_tensor in bbox]
        confidence = [conf.item() for conf in confidence]

        # Store metadata results 
        detection = Metadata(
            filename=uploaded_file.filename,
            drawing_types=drawing_types,
            bbox=bbox,
            confidence=confidence,
            cardinal_direction=None,
            scale=None,
            room_names=None
        )

        # Perform text detection and/or segmentation
        self.extract_additional_info(drawing_types, image, detection)
        postprocess_end = time.time()
        return detection, postprocess_end - postprocess_start
    
    def extract_additional_info(self, drawing_types, image, detection: Metadata):
        for dtype in drawing_types:
            if dtype == DrawingType.FASADE.name.lower():
                # Find cardinal direction
                detection.cardinal_direction = self.text_handler.get_cardinal_direction([cardinal_direction_pattern])  

            elif dtype == DrawingType.SITUASJONSKART.name.lower():
                # Find scale
                detection.scale = self.text_handler.get_scale([scale_pattern])

            elif dtype == DrawingType.PLANTEGNING.name.lower():
                try:
                    # Extract all room names found in drawing
                    room_text_infos = self.text_handler.get_room_names([room_pattern])
                    detection.room_names = [text.text for text in room_text_infos]
                    # Perform segmentation
                    results = self.segmentation_handler.run_segmentation(image)
                    self.segmentation_handler.find_text_segments(room_text_infos)
              
                except Exception as e:
                    self.logger.error(f"Error processing plantegning: {str(e)}")

    
    def map_class_labels(self, drawing_types):
        drawing_type_map = {
            0: DrawingType.FASADE,
            1: DrawingType.PLANTEGNING,
            2: DrawingType.SITUASJONSKART,
            3: DrawingType.SNITT
        }

        return [drawing_type_map.get(int(drawing_type), "unknown").name.lower() for drawing_type in drawing_types]
    
    def log_metrics(self, uploaded_file, image_size, total_time, inference_time, postprocess_time):
        with open("file_processing_metrics.txt", "a") as f:
            f.write(f"File: {uploaded_file.filename}, Image Size: {image_size}, "
                    #f"Total Time: {total_time} s, Preprocessing: {preprocess_time} s, "
                    f"Inference: {inference_time} s, Postprocessing: {postprocess_time} s\n")
        
        self.logger.info(f"Processed {uploaded_file.filename} in {total_time} seconds")

    def process_file(self, uploaded_file):
        detection_response = []
        
        file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"
        
        with open(file_path, "wb") as file_object:
            file_object.write(uploaded_file.file.read())

        # Compute the file hash to check if the file has been processed before
        file_hash = compute_file_hash(file_path)
        if file_hash in self.cache:
            self.logger.info(f"File '{uploaded_file.filename}' found in cache. Skipping processing.")
            return self.cache[file_hash]
        
        # Process the file if not found in cache    
        if uploaded_file.filename.endswith(".pdf"):
            input_images = convert_from_path(file_path)
            for image in input_images:
                detection = self.detect_and_validate(image, uploaded_file)
                #detection_response.append(self.detect_and_validate(image, uploaded_file))
                
        elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(file_path)
            detection = self.detect_and_validate(image, uploaded_file)
            #detection_response.append(detection)

        # Store the detection results in cache
        self.cache[file_hash] = detection_response
        os.remove(file_path)
        
        #self.storage.save(detection)

        #if len(detection_response) > 0:
        #    return detection_response[0]
        return detection