import os
from ultralytics import YOLO
from shared.config import Config

def train_object_detection():
    config = Config()
    model = YOLO(config.OBJECT_DETECTION_MODEL_PATH)
    model.train(
        data='shared/models/detection_model/data.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='object_detection'
    )
    
if __name__ == '__main__':
    train_object_detection()