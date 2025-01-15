
import json
from fastapi import FastAPI, UploadFile, HTTPException, APIRouter
import requests
from typing import List, Optional
from pydantic import BaseModel
import os
import cv2
from contextlib import asynccontextmanager
import asyncio
from difflib import get_close_matches
import pandas as pd
import time
from difflib import SequenceMatcher
from detect.src.api import DetectionService
from shared.utils.logger import cadaid_logger
from shared.config import Config


logger = cadaid_logger(__name__)
config = Config()

# Load environment variables
logger.info("Loading environment variables")
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
              root_path="/performance",
              root_path_in_servers=True,
              title="Performance API",
              description="API for performance analysis of CADAID system",
              version="1.0.0",
              docs_url="/docs",
              open_api_url="/openapi.json",
              openapi_tags=[{
                "name": "Performance",
                "description": "API for performance analysis of CADAID system"
              }],
             

            )
class PlantegningMetrics(BaseModel):
    objdet_accuracy: float
    num_rooms_accuracy: float    # detected rooms from segmentation
    ocr_rooms_accuracy: float
  

class FasadeMetrics(BaseModel):
    objdet_accuracy: float
    scale_accuracy: float
    cardinal_direction_accuracy: float

class SnittMetrics(BaseModel):
    objdet_accuracy: float
    ocr_accuracy: float

class SituasjonskartMetrics(BaseModel):
    objdet_accuracy: float


class PerformanceMetrics(BaseModel):
    OCR_model: Optional[str] = "unknown"
    rotation_applied: Optional[bool] = False
    average_processing_time: Optional[float] = 0
    images_processed: Optional[int] = 0
    plantegning: Optional[List[PlantegningMetrics]] = []
    fasade: Optional[List[FasadeMetrics]] = []
    snitt: Optional[List[SnittMetrics]] = []
    situasjonskart: Optional[SituasjonskartMetrics] = None

def calculate_objdet_accuracy(detection, ground_truth):
    objdet_accuracy = 1.0 if detection.drawing_type == ground_truth["drawing_type"] else 0.0

    return objdet_accuracy

def get_rooms_accurscy(detection, ground_truth):
    ground_truth_rooms = ground_truth.get("num_of_rooms")
    detected_num_rooms = detection.num_of_rooms
    if ground_truth_rooms == 0:
        return 1.0 if detected_num_rooms == 0 else 0.0
    error = abs(detected_num_rooms - ground_truth_rooms)
    accuracy = 1 - (error / ground_truth_rooms )
    return accuracy

def get_room_index(room_name, valid_room_names):
    for idx, labels in valid_room_names.items():
        match = get_close_matches(room_name.lower(), labels, n=1, cutoff=0.7)
        if match:
            return idx
    return None

def room_idx_to_label(indicies, valid_room_names):
    room_names = []
    for idx in indicies:
        room_names.extend(valid_room_names[str(idx)])
    return room_names

def calculate_accuracy(ground_truth,extracted):
    matcher = SequenceMatcher(None, ground_truth, extracted)
    accuracy = matcher.ratio() 
    return accuracy

def ocr_accuracy(ground_truth, ocr_output):
    ocr_detections = [name.lower() for name in ocr_output]
   
    correct_detections = sum(1 for gt in ground_truth if any (calculate_accuracy(gt,det) >0.8 for det in ocr_detections))
    total_detections = len(ocr_detections)
    accuracy = (correct_detections) / total_detections * 100 if total_detections > 0 else 0
    return accuracy
   


def evaluate_image(detection_results,filename, ground_truth_data):
    
    for detection in detection_results:

        ground_truth = next((entry["ground_truth"] for entry in ground_truth_data if entry["filename"] == filename), None)
    
        objdet_acc = calculate_objdet_accuracy(detection, ground_truth)

        if detection.drawing_type == "plantegning":
            num_of_rooms_acc = get_rooms_accurscy(detection, ground_truth)
            ground_truth_rooms = ground_truth.get("room_names") if ground_truth else None
            detected_rooms = detection.room_names
            ocr_acc = ocr_accuracy(ground_truth_rooms, detected_rooms)
            print("Room OCR accuracy", ocr_acc)
            
            all_metrics.plantegning.append(PlantegningMetrics(
                objdet_accuracy=objdet_acc,
                num_rooms_accuracy=num_of_rooms_acc,
                ocr_rooms_accuracy=ocr_acc
  
            ))

        if detection.drawing_type == "fasade":
            
            cardinal_direction = detection.cardinal_direction
            ground_truth_directions = ground_truth.get("cardinal_direction")
            detected_scale = detection.scale
            ground_truth_scale = ground_truth.get("scale")
            ocr_cardinal_acc = ocr_accuracy(ground_truth_directions, cardinal_direction)
            ocr_scale_acc = ocr_accuracy(ground_truth_scale, detected_scale)

            all_metrics.fasade.append(FasadeMetrics(
                objdet_accuracy=objdet_acc,
                cardinal_direction_accuracy=ocr_cardinal_acc,
                scale_accuracy=ocr_scale_acc

            ))

def summarized_metrics(metrics: PerformanceMetrics, num_images,avg_processing_time):
    def average(values):
        return sum(values)/len(values) if values else 0
    avg_metrics = PerformanceMetrics()
    avg_metrics.OCR_model = config.OCR_MODEL
    avg_metrics.rotation_applied = False
    avg_metrics.average_processing_time = avg_processing_time
    avg_metrics.images_processed = num_images
    print("Metrics Summary:")
    print(f"OCR Model: {avg_metrics.OCR_model}")
    print(f"Average time pr image: {avg_metrics.average_processing_time:.2f}s")
    print(f"Image Rotation: {avg_metrics.rotation_applied}")
    print(f"Total images:{avg_metrics.images_processed}")
    
    if metrics.plantegning:
        avg_objdet = average([m.objdet_accuracy for m in metrics.plantegning])
        avg_segm = average([m.num_rooms_accuracy for m in metrics.plantegning])
        avg_ocr_acc = average([m.ocr_rooms_accuracy for m in metrics.plantegning])
        avg_metrics.plantegning.append(PlantegningMetrics(
            objdet_accuracy=avg_objdet,
            num_rooms_accuracy=avg_segm,
            ocr_rooms_accuracy=avg_ocr_acc
        
        ))
        print(f"Plantegning - ObjDet Accuracy: {avg_objdet:.2f} - Room Segm. Accuracy: {avg_segm:.2f}")
        print(f"- Room OCR Accuracy: {avg_ocr_acc:.2f}")
    if metrics.fasade:
        avg_objdet = average([m.objdet_accuracy for m in metrics.fasade])
        avg_card_acc = average([m.cardinal_direction_accuracy for m in metrics.fasade])
        avg_scale_acc = average([m.scale_accuracy for m in metrics.fasade])
        avg_metrics.fasade.append(FasadeMetrics(
            objdet_accuracy=avg_objdet,
            scale_accuracy=avg_scale_acc,
            cardinal_direction_accuracy=avg_card_acc
        ))
        print(f"Fasade - ObjDet Accuracy: {avg_objdet:.2f} - Himmelretning Accuracy: {avg_card_acc:.2f}")
        print(f"OCR Målestokk Acc: {avg_scale_acc:.2f}")
    
    return avg_metrics
    

detection_service = DetectionService()

all_metrics = PerformanceMetrics(
        #OCR_model=config.OCR_MODEL,
        #rotation_applied=False
    )

def find_images_in(directory):
    images_files = []
    for root, i, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".png")):
                images_files.append(os.path.join(root, file))
    return images_files

def find_avg_processing_time(processed_time):
    average_time = sum(processed_time)/len(processed_time) if processed_time else 0
    return average_time

with open("./performance_data/ground_truth.json", "r") as f:
    ground_truth = json.load(f)

with open("./performance_data/valid_room_names.json", "r") as f:
    valid_room_names = json.load(f)

DEFAULT_FOLDER_PATH = "./performance_data/images"


@app.get("/process-folder")
def process_folder():
    folder_path = DEFAULT_FOLDER_PATH

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Invalid folder path")
    image_files = find_images_in(DEFAULT_FOLDER_PATH)
    
    if not image_files:
        raise HTTPException(status_code=400, detail=f"No image files found")
    results = []
    processing_times = []
    num_images = 0
    for image_path in image_files:
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            filename = os.path.basename(image_path)
            logger.info(f"Processing file: {filename}")

            start_time = time.time()
            detections = detection_service.run_detection_pipeline(image)
            end_time = time.time()
            detection_time = end_time-start_time
            processing_times.append(detection_time)
            logger.info(f"Drawing type: {detections}")

            evaluate_image(detections, filename, ground_truth)
            num_images += 1
            results.append({
                "filename": os.path.relpath(image_path, DEFAULT_FOLDER_PATH),
                "detections": [detection.__dict__ for detection in detections],
            })

        except Exception as e:
            logger.error(f"Error during detection: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    avg_processing_time = find_avg_processing_time(processing_times)
    avg_metrics = summarized_metrics(all_metrics, num_images,avg_processing_time)
    return avg_metrics
   

     