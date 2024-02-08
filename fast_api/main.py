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
import re

app = FastAPI()

# store uploaded images temporary folder
UPLOAD_DIRECTORY = Path("fast_api/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

def check_confidence(label_conf):
    high_conf_drawings = []
    low_conf_drawings = []

    for label, conf in label_conf:
        if conf > 0.60:
            high_conf_drawings.append(label)

        # Decide how to handle drawings with lower confidence
        elif 0.20 < conf < 0.60:
            low_conf_drawings.append([label,conf])

    return high_conf_drawings,low_conf_drawings


# Get the predicted key-value pairs from json
def find_value(detections_res: str, drawing_name: str, conf: str):
    try:
        json_data = json.loads(detections_res)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    if isinstance(json_data, list):
        labelname_conf_combined = []

        for item in json_data:
            temp = []
            if drawing_name in item:
                value = item[drawing_name]
                temp.append(value)
            if conf in item:
                value = item[conf]
                if isinstance(value, (int, float)):
                    temp.append(round(float(value), 2))
            labelname_conf_combined.append(temp)

        return labelname_conf_combined

    else:
        print("Invalid JSON format or not a list.")
        return None

def check_detections(detections_json):
    # Return message if no detections
    if len(find_value(detections_json[0], "name","confidence")) == 0:
        return {"Er du sikker på at dette er riktig tegning?"}

    else:
        label_conf_combined=find_value(detections_json[0],"name","confidence")
        # check if confidence is above a threshold value
        high_conf_drawings, low_conf_drawings = check_confidence(label_conf_combined)
        return high_conf_drawings


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

    # Check detections in drawing and return message
    drawing_check = check_detections(detections_json)

    return {"message": drawing_check}

