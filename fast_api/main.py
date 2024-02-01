from fastapi import FastAPI
from enum import Enum
import io
import json
from typing import Annotated
from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from pdf2image import convert_from_path, convert_from_bytes
from pathlib import Path
import shutil
import uvicorn


app = FastAPI()

# store uploaded images temporary folder
UPLOAD_DIRECTORY = Path("fast_api/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
class ModelName(str,Enum):
    yolov8 = "yolov8"
    unet = "unet"



@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.yolov8:
        return {"model_name": model_name, "message": "Using YOLOv8 for object detection"}
    if model_name is ModelName.unet:
        return {"model_name": model_name, "message": "Using U-net!"}



def check_confidence(detections_json):
    data = json.loads(detections_json)

    for detections in data:
        print(detections)


@app.post("/detect/")
async def detect_objects (uploaded_file: UploadFile = File(...)):
    model = YOLO("runs/detect/train/weights/best.pt")
    # Process the uploaded image for object detection
    file_path = UPLOAD_DIRECTORY/uploaded_file.filename

    # store uploaded file in temp folder
    with open(file_path,"wb") as file_object:
        # read file into memory in bytes
        file_object.write(uploaded_file.file.read())


    detections_json = []

    # convert file to image if pdf
    if uploaded_file.filename.lower().endswith('.pdf'):
        input_images = convert_from_path(file_path)
        for image in input_images:
            results = model.predict(image)
            for r in results:
                detections = r.tojson()
                detections_json.append(detections)

    # read file directly as an image from folder
    elif uploaded_file.filename.lower().endswith(('.jpg','.jpeg', '.png')):
        image = cv2.imread(str(file_path))
        results = model.predict(image)
        for r in results:
            detections = r.tojson()
            detections_json.append(detections)

    check_confidence(detections_json)

    return {"detections": detections_json}
