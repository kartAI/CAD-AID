from fastapi import APIRouter, UploadFile
import os
from typing import List
from pdf2image import convert_from_path
import cv2
from app.classification.model import ObjectDetection
from app.classification.utils import Detection, FileDetections

UPLOAD_DIRECTORY = "/app/upload_files"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

router = APIRouter()

classifier = ObjectDetection()

@router.post("/")
async def detect_objects(uploaded_files: List[UploadFile]):
    all_detections = []
    for uploaded_file in uploaded_files:
        file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"
        with open(file_path, "wb") as file_object:
            file_object.write(uploaded_file.file.read())
        
        if uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(file_path)
            drawing_types, bbox, confidence = classifier.process_results(image)
            detections = [Detection(drawing_type=drawing_types[i]) for i in range(len(drawing_types))]
            all_detections.append(FileDetections(filename=uploaded_file.filename, detections=detections))
            

    return all_detections
            


