import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
   
        load_dotenv(".env.dev")
        
        # Object Detection model configuration
        self.OBJECT_DETECTION_MODEL_PATH = os.getenv('OBJECT_DETECTION_MODEL_PATH')
        self.OBJECT_DETECTION_CONFIDENCE = float(os.getenv('OBJECT_DETECTION_CONFIDENCE', 0.6))
       
        # Segmentation model configuration
        self.SEGMENTATION_MODEL_PATH = os.getenv('SEGMENTATION_MODEL_PATH')
        self.SEGMENTATION_CONFIDENCE = float(os.getenv('SEGMENTATION_CONFIDENCE', 0.6))

        # Configuration for pytesseract
        self.OCR_MODEL = os.getenv("OCR_MODEL")
        
        
     