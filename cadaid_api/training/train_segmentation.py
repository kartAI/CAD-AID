import os
from ultralytics import YOLO
from shared.config import Config

def train_segmentation():
    config = Config()
    model = YOLO(config.SEGMENTATION_MODEL_PATH)
    model.train(
        data='shared/models/segmentation_model/data_seg.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='segmentation'
    )
    
if __name__ == '__main__':
    train_segmentation()