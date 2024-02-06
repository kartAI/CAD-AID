from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from fastapi import FastAPI, File, UploadFile
import cv2
from ultralytics import YOLO
from pdf2image import convert_from_path
from pathlib import Path
import uvicorn

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
UPLOAD_DIRECTORY = Path("/static/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


def check_confidence(label_conf):
    high_conf_drawings = []
    low_conf_drawings = []

    for label, conf in label_conf:
        if conf > 0.60:
            high_conf_drawings.append(label)

        # Decide how to handle drawings with lower confidence
        elif 0.20 < conf < 0.59:
            low_conf_drawings.append([label, conf])

    return high_conf_drawings, low_conf_drawings


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
    if len(find_value(detections_json[0], "name", "confidence")) == 0:
        return {"Er du sikker på at dette er riktig tegning?"}

    else:
        label_conf_combined=find_value(detections_json[0], "name", "confidence")
        # check if confidence is above a threshold value
        high_conf_drawings, low_conf_drawings = check_confidence(label_conf_combined)
        return high_conf_drawings


@app.get("/")
async def root():
    return JSONResponse({"message": "Hello World!!"})

@app.post("/detect/")
async def detect_objects (uploaded_file: UploadFile = File(...)):
    model_path = r"../runs/detect/train/weights/best.pt"

    if os.path.exists(model_path):
        print("File exists.")
    else:
        print("File does not exist.")

    model = YOLO(model_path)
    # Process the uploaded image for object detection
    file_path = UPLOAD_DIRECTORY/uploaded_file.filename

    # store uploaded file in temp folder
    with open(file_path, "wb") as file_object:
        # read file into memory in bytes
        file_object.write(uploaded_file.file.read())

    detections_json = []

    print(uploaded_file.filename.lower().endswith('.pdf'))
    # convert file to image if pdf
    if uploaded_file.filename.lower().endswith('.pdf'):
        input_images = convert_from_path(file_path)
        for image in input_images:
            results = model.predict(image)
            for r in results:
                detections = r.tojson()

                detections_json.append(detections)

    # read file directly as an image from folder
    elif uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        image = cv2.imread(str(file_path))
        results = model.predict(image)
        for r in results:
            detections = r.tojson()
            detections_json.append(detections)

    # Check detections in drawing and return message
    drawing_check = check_detections(detections_json)

    print(drawing_check)

    return {"message": drawing_check}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)