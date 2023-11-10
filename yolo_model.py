
import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os

# Load model
model = YOLO("runs/detect/train/weights/best.pt")

# Train model
def train_model():
    model.train(data="data/data.yaml", epochs=30,batch=8)
    metrics = model.val()
def prediction(img):

    #img = "data/test/images/Scan 19 Oct 2023 at 15.51_page_1.jpg"
    results = model.predict(img, save=False, stream=True)

    image = cv2.imread(img)

    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.show()  # show image



#train_model()
#prediction(img)