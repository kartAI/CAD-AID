
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


# Train model
def train_model(model):
    model.train(data='data/data.yaml', classes=[0,1,2,3], epochs=10)
def prediction_nora(img_path,model):
    image = Image.open(img_path)
    results = model.predict(image, save=False, stream=True)

    return results

def plot_detected_drawings(results):

    for r in results:
        img_array = r.plot()
        img = Image.fromarray(img_array[..., :: -1]) # RGB image
        img.show()

if __name__ == "__main__":
    img_path = "../data/test/images/Brunsbykollen9_fasade_page_1.jpg"

    model = YOLO("../runs/detect/Ada/train12/weights/best.pt")
    results = prediction_nora(img_path, model)
    plot_detected_drawings(results)