from ultralytics import YOLO
import easyocr
import pytesseract
from typing import List
from dataclasses import dataclass

from config import Config
from .data_structures import TextData


class Segmentation:
    def __init__(self):
        self._config = Config()
        self.model_path = self._config.SEGMENTATION_MODEL_PATH
        self.model_conf = self._config.SEGMENTATION_CONFIDENCE
        
        self.model = YOLO(self.model_path)

    
    def process_results(self,image):
        results = self.model(image,
                          save=False, 
                          stream=True, 
                          visualize=False, 
                          conf=self.model_conf)
        
        return results
    


class OCRModel:
    def __init__(self):
        self.config = Config()
        #self.model = self.config.OCR_MODEL
        self.model = "pytesseract_ocr"
        

    def perform_ocr(self,image, language='nor'):
        if self.model == "easy_ocr":
            return self._easy_ocr(image)
        elif self.model == "pytesseract_ocr":
            return self._pytesseract_ocr(image, language=language)
            
        else:
            raise ValueError(f"Unsupported OCR model: {self.model}")
    
    def _easy_ocr(self,image):
        detected_text = []
        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)
        for result in results:
            bbox, text, prob = result
            x1, y1 = bbox[0][0], bbox[0][1]  # Bottom-left corner
            x2, y2 = bbox[2][0], bbox[2][1]  # top right corner

            bbox = (x1,y1,x2,y2)
            
            text_info = TextData(text=text, bbox=bbox, probability=prob)
            detected_text.append(text_info)
        return detected_text
    
    def _pytesseract_ocr(self, image, language) -> List[TextData]:
        detected_text = []
        
        custom_config = r'--oem 3 --psm 11'
        results = pytesseract.image_to_data(image, config=custom_config, lang=language, output_type = pytesseract.Output.DICT)
        
        for i in range(len(results['text'])):
            text = results['text'][i]
            if results['text'][i].strip():
            #if text.strip():
                x1, y1, w, h = results['left'][i], results['top'][i], results['width'][i], results['height'][i]
                x2 = x1 + w
                y2 = y1 + h
                #confidence = int(results['conf'][i]) / 100.0
                confidence = results['conf'][i]
                #bbox = [(x,y), (x + w,y), (x + w, y+h), (x, y +h)]
                bbox = (x1,y1,x2,y2)
                text_info = TextData(text=text, bbox=bbox, probability=confidence)
                detected_text.append(text_info)


        return detected_text


        

    