from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import os
from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from pathlib import Path
from pdf2image import convert_from_path
from helpers import check_detections
from typing import Dict, List
from models import Detection

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# store uploaded images temporary folder
UPLOAD_DIRECTORY = Path("static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


@app.post("/detect/")
async def detect_objects(uploaded_files: List[UploadFile]):
    model_path = r"../runs/detect/Nora/train/weights/best.pt"

    # os.path.exists(model_path)

    model = YOLO(model_path)

    response_json: Dict[str | None, Dict[str, Detection]] = {}

    for uploaded_file in uploaded_files:
        # Process the uploaded image for object detection
        file_path = UPLOAD_DIRECTORY/uploaded_file.filename

        # store uploaded file in temp folder
        with open(file_path, "wb") as file_object:
            # read file into memory in bytes
            file_object.write(uploaded_file.file.read())

        # convert file to image if pdf
        if uploaded_file.filename.lower().endswith('.pdf'):
            input_images = convert_from_path(file_path)
            for image in input_images:
                results = model.predict(image)
                for r in results:
                    detections = r.tojson()
                    response_json = {
                        **response_json,
                        uploaded_file.filename: check_detections(detections)
                    }

        # read file directly as an image from folder
        elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(str(file_path))
            results = model.predict(image)
            for r in results:
                detections = r.tojson()
                print("debugger jpg")
                print(check_detections(detections))
                response_json = {
                    **response_json,
                    uploaded_file.filename: check_detections(detections)
                }

    return response_json


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
