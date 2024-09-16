import os
from dotenv import load_dotenv
class Config():
    def __init__(self):
        self.OBJECT_DETECTION_MODEL_NAME = os.getenv('OBJECT_DETECTION_MODEL_NAME')
        self.OBJECT_DETECTION_MODEL_PATH = os.getenv('OBJECT_DETECTION_MODEL_PATH')
        self.OBJECT_DETECTION_CONFIDENCE = float(os.getenv('OBJECT_DETECTION_CONFIDENCE', 0.6))
        self.OBJECT_DETECTION_YAML  = os.getenv('OBJECT_DETECTION_YAML')

        self.SEGMENTATION_MODEL_NAME = os.getenv('SEGMENTATION_MODEL_NAME')
        self.SEGMENTATION_MODEL_PATH = os.getenv('SEGMENTATION_MODEL_PATH')
        self.SEGMENTATION_CONFIDENCE = float(os.getenv('SEGMENTATION_CONFIDENCE', 0.6))
        self.SEGMENTATION_YAML = os.getenv('SEGMENTATION_YAML')

        self.PREDICTION_IMAGE_PATH = os.getenv('PREDICTION_IMAGE_PATH')