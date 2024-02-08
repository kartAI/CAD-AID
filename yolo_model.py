
import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import json

# Load model
model = YOLO("runs/detect/train3/weights/best.pt")

# Train model
def train_model():
    model.train(data="data/data.yaml", epochs=30,batch=8)
    metrics = model.val()
def prediction(img):


    results = model(img, save=False, stream=True)

    image = cv2.imread(img)

    for r in results:

        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.show()  # show image

#train_model()

img="data/test/images/fasade43.jpg"

#img= "fast_api/static/uploads/04771a42106a75cfbbc2bc021823aaf5.jpg"
results = model(img,save=False)
detections_json = []
for r in results:
    print(r)
    detections = r.tojson()
    detections_json.append(detections)

print(detections_json)