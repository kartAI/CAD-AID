from fastapi.middleware.cors import CORSMiddleware
import cv2
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile
from pathlib import Path
from pdf2image import convert_from_path
from typing import List
from .nora_detection import nora_detection
from .ada_detection import ada_detection
from .eva_segmentation import eva_segmentation
from .json_response_converter import json_response_converter
from fastapi.responses import Response, StreamingResponse
from sse_starlette import EventSourceResponse
import json
import queue
from fastapi import BackgroundTasks
import time

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

#detected_drawings = []
detected_drawings_queue = asyncio.Queue()

def detect_and_validate(image, uploaded_file): 
    nora: list = nora_detection(image)

    ada = {}
    eva = {}
    
    if 'fasade' in nora or 'plantegning' in nora:
        ada, detected_text, detected_text_coordinates = ada_detection(image, nora)
        if 'plantegning' in nora:
            eva = eva_segmentation(image, detected_text, detected_text_coordinates)

    print('ferdig med detection')
    detected_drawings_queue.put_nowait(json_response_converter({
        "drawing_types": nora,
        "file_name": uploaded_file.filename,
        **ada,
        **eva
    }))


def process_file(uploaded_file):
    # detection_response = []
    file_path = f"{UPLOAD_DIRECTORY}/{uploaded_file.filename}"

    with open(file_path, "wb") as file_object:
        file_object.write(uploaded_file.file.read())

    if uploaded_file.filename.lower().endswith('.pdf'):
        input_images = convert_from_path(file_path)
        for image in input_images:
            detect_and_validate(image, uploaded_file)
            # detection_response.append(detect_and_validate(image, uploaded_file))

    elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        image = cv2.imread(file_path)
        detect_and_validate(image, uploaded_file)
        # detection_response.append(detect_and_validate(image, uploaded_file))

    os.remove(file_path)

    detected_drawings_queue.put_nowait('DONE')
    # yield json_response_converter(detection_response[0])
    # detected_drawings.append(json_response_converter(detection_response[0]))
@app.get('/stream')
async def strem_detected_drawings(): 
    async def event_generator():
        try:
            while True:
                drawing = await detected_drawings_queue.get()
                if drawing == 'DONE':
                    break
                print(drawing)
                yield f"{drawing}"
                await asyncio.sleep(0.9)
        except asyncio.CancelledError:
            print('canceled')

    return EventSourceResponse(event_generator(), media_type="text/event-stream")

@app.post("/detect/")
async def detect_objects(uploaded_files: List[UploadFile]):
    start_time = time.time()
    detected_drawings_queue = asyncio.Queue()
    with ThreadPoolExecutor() as executor:
     
        executor.map(process_file, uploaded_files)
    
    end_time = time.time()  # Stopp tidtakingen
    execution_time = end_time - start_time
    print(f"Total tid for oppgave: {execution_time} sekunder")


