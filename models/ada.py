import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
import tempfile
import sys


# YOLOV8 MODEL TO DETECT TEXT IN IMAGES - UTGÅR?

# Load model
model = YOLO("../runs/detect/Ada/train12/weights/best.pt")

# Train model
def train_model(model):
    model.train(data='data/data.yaml', classes=[4],epochs=10)

def prediction(img_path):
    image = Image.open(img_path)

    results = model.predict(image, save=False, stream=True)

    image = cv2.imread(img)

    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.show()  # show image

def crop_text(img_path,model):
    image = Image.open(img_path)
    results = model.predict(image, save = False, stream = True)

    for r in results:
        r_array = r.numpy()
        bboxes = r_array.boxes.xyxy
        for bbox in bboxes:
            x_min, y_min, x_max, y_max = map(int, bbox[:4])
            cropped_img = image.crop((x_min, y_min, x_max, y_max))
            plt.figure(figsize=(5, 5))
            plt.imshow(cropped_img)
            plt.axis('off')  # Hide axes ticks
            plt.show()




img= "data/test/images/fasade37.jpg"


prediction(img)
#train_model()
#crop_text(img,model)