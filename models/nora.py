
import cv2
import pandas as pd
from ultralytics import YOLO
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
import tempfile
import sys
from ultralytics.utils.plotting import plot_results

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
def plot_loss_curves(csv_file):
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()

    fig, axes = plt.subplots(2, 1, figsize=(10, 12))

    # Plot for Box Loss
    axes[0].plot(df['epoch'], df['train/box_loss'], label='Training Box Loss')
    axes[0].plot(df['epoch'], df['val/box_loss'], label='Validation Box Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Box Loss')
    axes[0].set_title('Training and Validation Box Loss')
    axes[0].legend()
    axes[0].grid(True)

    # Plot for Classification Loss
    axes[1].plot(df['epoch'], df['train/cls_loss'], label='Training Classification Loss')
    axes[1].plot(df['epoch'], df['val/cls_loss'], label='Validation Classification Loss')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Classification Loss')
    axes[1].set_title('Training and Validation Classification Loss')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    img_path = "../data/test/images/Rådhusgata 45_foto.PNG"

    csv_file_path = "../runs/detect/nora/train2/results.csv"

    #plot_loss_curves(csv_file_path)
    model = YOLO("../runs/detect/nora/train4/weights/best.pt")
    results = prediction_nora(img_path, model)
    plot_detected_drawings(results)