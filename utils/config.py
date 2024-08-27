import os
class Config():
    def __init__(self):
        self.OBJECT_DETECTION_MODEL_NAME = os.environ.get('OBJECT_DETECTION_MODEL')
        self.OBJECT_DETECTION_MODEL_PATH = os.environ.get('OBJECT_DETECTION_MODEL_PATH')
        self.OBJECT_DETECTION_CONFIDENCE = float(os.environ.get('OBJECT_DETECTION_CONFIDENCE', 0.6))
        self.OBJECT_DETECTION_YAML  = os.environ.get('OBJECT_DETECTION_YAML')

        self.SEGMENTATION_MODEL_NAME = os.environ.get('SEGMENTATION_MODEL')
        self.SEGMENTATION_MODEL_PATH = os.environ.get('SEGMENTATION_MODEL_PATH')
        self.SEGMENTATION_CONFIDENCE = float(os.environ.get('SEGMENTATION_CONFIDENCE', 0.6))
        self.SEGMENTATION_YAML = os.environ.get('SEGMENTATION_YAML')

        self.PREDICTION_IMAGE_PATH = os.environ.get('PREDICTION_IMAGE_PATH')