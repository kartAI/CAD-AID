

import cv2
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
import tempfile
import sys
sys.path.append('/Users/juliajorstad/Sinhala-ParSeq-main')

from pretrained_model import pretrained



# Load model
model = YOLO("yolov8s.pt")


def prediction(img_path):
    image = Image.open(img_path)
    #img = "data_old/test/images/Scan 19 Oct 2023 at 15.51_page_1.jpg"
    results = model.predict(image, save=False, stream=True)

    image = cv2.imread(img)

    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
        im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
        im.show()  # show image

def crop_text(img_path, model):
    # Load the image
    image = Image.open(img_path)

    # Get model predictions
    results = model.predict(image, save=False, stream=True)

    # Initialize a list to hold cropped text images


    # Iterate through detection results
    for r in results:
        r_array = r.numpy()

        if r_array.names[4]:
            text_bbox = r_array.boxes.xyxy
            for bbox in text_bbox:
                x_min, y_min, x_max, y_max = map(int, bbox[:4])
                cropped_img = image.crop((x_min, y_min, x_max, y_max))
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    cropped_img.save(tmp.name, format='PNG')
                    tmp_path = tmp.name  # Store the temporary file path to use with the pretrained function

                # Use the temporary PNG file with the pretrained function
                pretrained(tmp_path)


                plt.figure(figsize=(5, 5))
                plt.imshow(cropped_img)
                plt.axis('off')  # Hide axes ticks
                #plt.show()


img= "data/test/images/Kalkveien_21_U_page_1.jpg"
#prediction(img)

#crop_text(img,model)