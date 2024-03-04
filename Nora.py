
import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
import tempfile
import sys

# YOLOV8 MODEL TO DETECT DRAWING TYPES

# Load model
model = YOLO("runs/detect/Nora/train/weights/best.pt")

# Train model
def train_model():
    model.train(data='data/data.yaml', classes=[0,1,2,3], epochs=10)
    metrics = model.val()
def prediction(img_path):
    image = Image.open(img_path)
    #img = "data_old/test/images/Scan 19 Oct 2023 at 15.51_page_1.jpg"
    results = model.predict(image, save=False, stream=True)

    image = cv2.imread(img)

    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.show()  # show image



img= "data/test/images/Brunsbykollen9_plan_snitt_page_1.jpg"
prediction(img)
#train_model()
