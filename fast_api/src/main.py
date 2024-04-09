from fastapi.middleware.cors import CORSMiddleware
import cv2
import os
from fastapi import FastAPI, UploadFile
from pathlib import Path
from pdf2image import convert_from_path
from typing import List
from .nora_detection import nora_detection
from .ada_detection import ada_detection
from .eva_segmentation import eva_segmentation
from .json_response_converter import json_response_converter

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

    detection_response = []
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
                nora: list = nora_detection(image)

                ada = {}
                eva = {}
                
                if 'fasade' in nora or 'plantegning' in nora:
                    ada, detected_text, detected_text_coordinates = ada_detection(image, nora)
                    eva = eva_segmentation(image, detected_text, detected_text_coordinates)

                detection_response.append({
                    'drawing_types': nora,
                    'file_name': uploaded_file.filename,
                    **ada,
                    **eva
                })

        # read file directly as an image from folder
        elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(str(file_path))

            nora: list = nora_detection(image)
            ada = {}
            eva = {}
            if 'fasade' in nora or 'plantegning' in nora:
                ada, detected_text, detected_text_coordinates = ada_detection(image, nora)
                eva = eva_segmentation(image, detected_text, detected_text_coordinates)

            detection_response.append({
                'drawing_types': nora,
                'file_name': uploaded_file.filename,
                **ada,
                **eva
            })

        os.remove(file_path)
    return json_response_converter(detection_response)
