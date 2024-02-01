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
UPLOAD_DIRECTORY = Path("/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


# Get the predicted values from json
def find_value(detections_res: [], key: str):
    try:
        json_data = json.loads(detections_res)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    if isinstance(json_data, list):
        for item in json_data:
            if key in item:
                value = item[key]
                if isinstance(value, (int, float)):
                    print(f"{key} value: {value}, {round(float(value), 2)}")
                    return round(float(value), 2)
                else:
                    print(f"{key} value: {value}")
                    return str(value)
        print(f"{key} not found in any item of the JSON.")
        return None
    else:
        print("Invalid JSON format or not a list.")
        return None


def check_detections(detections_json):
    # Return message if no detections or if conf. < some value
    if find_value(detections_json[0], "name") is None or find_value(detections_json[0],"confidence") < 0.60:
        return {"Er du sikker på at dette er riktig tegning?"}

    else:
        drawing_type=find_value(detections_json[0],"name")
        return drawing_type
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)