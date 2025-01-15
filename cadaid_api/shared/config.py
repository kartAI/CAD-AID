import os
from dotenv import load_dotenv



#OCR_MODEL = config("OCR_MODEL", default = "pytesseract_ocr")

class Config:
    def __init__(self):
        # Load environment variables from .env.dev file
        load_dotenv(".env.dev")
        
        # Object Detection model configuration
        self.OBJECT_DETECTION_MODEL_NAME = os.getenv('OBJECT_DETECTION_MODEL_NAME')
        self.OBJECT_DETECTION_MODEL_PATH = os.getenv('OBJECT_DETECTION_MODEL_PATH')
        self.OBJECT_DETECTION_CONFIDENCE = float(os.getenv('OBJECT_DETECTION_CONFIDENCE', 0.6))
       

        # Segmentation model configuration
        self.SEGMENTATION_MODEL_NAME = os.getenv('SEGMENTATION_MODEL_NAME')
        self.SEGMENTATION_MODEL_PATH = os.getenv('SEGMENTATION_MODEL_PATH')
        self.SEGMENTATION_CONFIDENCE = float(os.getenv('SEGMENTATION_CONFIDENCE', 0.6))

        # Configuration for pytesseract
        self.OCR_MODEL = os.getenv("OCR_MODEL")
        PYTESSERACT_NUMBERS = r'--oem 3 --psm 11 -c tessedit_char_whitelist=0123456789.,m '
     