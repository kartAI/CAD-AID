from typing import List, Optional

import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import easyocr
import pytesseract
import cv2
import re
from shared.config import Config
import math
from .data_structures import TextInfo, PolygonInfo 


""""
Core functionality for OCR extraction and text detection

"""

class BoundingBox:
    def __init__(self, bbox: List[tuple]):
        self.bbox = bbox
    
    def get_centroid(self):
        x_coord = self.bbox[0]
        y_coord = self.bbox[1] 
        centroid = (sum(x_coord) / len(x_coord), sum(y_coord) / len(y_coord))

        return centroid

		
class TextDetection():
    def __init__(self ):
        
        self.target_words: List[TextInfo] = []
        self.detected_text = []
        

    def easy_ocr(self,image):
        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)
        for result in results:
            bbox, text, prob = result
            text_info = TextInfo(text=text, bbox=bbox, probability=prob)
            self.detected_text.append(text_info)
        return self.detected_text
    
    def pytesseract_ocr(self, image) -> List[TextInfo]:
        detected_text = []
        custom_config = r'--oem 3 --psm 11' # TODO: Move this to a config file
        results = pytesseract.image_to_data(image, config=custom_config, lang='eng', output_type = pytesseract.Output.DICT)
        for i in range(len(results['text'])):
            text = results['text'][i]
            if text.strip():
                x, y, w, h = results['left'][i], results['top'][i], results['width'][i], results['height'][i]
                confidence = int(results['conf'][i]) / 100.0
                bbox = [(x,y), (x + w,y), (x + w, y+h), (x, y +h)]
                text_info = TextInfo(text=text, bbox=bbox, probability=confidence)
                detected_text.append(text_info)

        return detected_text


    def get_target_text(self,detected_text, pattern: List[str])-> List[TextInfo]:
        """
        Filters all detected text in image based on regex pattern
        """
        # Log all detected text before applying regex
        logging.info(f"All detected text from OCR: {[text.text for text in detected_text]}")

        target_text = []
        added_text = set()
        for text_info in detected_text:
            text = text_info.text
            bbox = text_info.bbox
            prob = text_info.probability

            if re.search(pattern, text, re.IGNORECASE):
                unique_key = (text, tuple(map(tuple, bbox)))
                if unique_key not in added_text:
                    target_text_info = TextInfo(text=text, bbox=bbox, probability=prob)
                    target_text.append(target_text_info)
                    added_text.add(unique_key)
                
        return target_text

    """def get_target_text(self,patterns: List[str])-> List[TextInfo]:
        # Log all detected text before applying regex
        logging.info(f"All detected text from OCR: {[text.text for text in self.detected_text]}")


        for text_info in self.detected_text:
            text = text_info.text
            bbox = text_info.bbox
            prob = text_info.probability

            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    target_text_info = TextInfo(text=text, bbox=bbox, probability=prob)
                    self.target_words.append(target_text_info)
                    break
        return self.target_words"""

    def get_cardinal_direction(self, detected_text, patterns: List[str], obj_bbox) -> List[TextInfo]:
        
        target_text = self.get_target_text(detected_text, patterns)
        return target_text


        #return self.get_target_text(detected_text, patterns)

    def get_scale(self, detected_text,patterns: List[str]) -> List[TextInfo]:
        return self.get_target_text(detected_text, patterns)
        #return text_infos[0].text if text_infos else None

    #def get_room_names(self, patterns: List[str]) -> List[TextInfo]:
        """
        Args:
            patterns: List of room patterns to search for in the detected text.
        Returns:
            List of TextInfo objects containing the room
        """
       # return self.get_target_text(patterns)
    
    def get_text_in_region(self, detected_text, patterns: List[str], bbox: List[float]) -> List[TextInfo]:
        """Search for text patterns only within a specific bounding box region"""
        region_text = []
        for text_info in detected_text:
            text_bbox = text_info.bbox
            # Check if text center point is within detection bbox
            text_center_x = (text_bbox[0][0] + text_bbox[2][0]) / 2
            text_center_y = (text_bbox[0][1] + text_bbox[2][1]) / 2
            
            if (bbox[0] <= text_center_x <= bbox[2] and 
                bbox[1] <= text_center_y <= bbox[3]):
                for pattern in patterns:
                    if re.search(pattern, text_info.text, re.IGNORECASE):
                        region_text.append(text_info)
                        break
        return region_text

    def get_cardinal_direction_in_region(self, detected_text,patterns: List[str], bbox: List[float]) -> Optional[str]:
        text_infos = self.get_text_in_region(detected_text,patterns, bbox)
        print(text_infos)
        return text_infos[0].text if text_infos else None

    def get_scale_in_region(self, detected_text,patterns: List[str], bbox: List[float]) -> Optional[str]:
        text_infos = self.get_text_in_region(detected_text,patterns, bbox)
        return text_infos[0].text if text_infos else None

    def get_room_names_in_region(self, patterns: List[str], bbox: List[float]) -> List[TextInfo]:
        """
        Args:
            patterns: List of room patterns to search for in the detected text.
        Returns:
            List of TextInfo objects containing the room
        """
        return self.get_text_in_region(patterns, bbox)
    
    def get_rom_areal(self, detected_text, areal_pattern):
        """
        Filter text in image based on areal
        """

        return self.get_target_text(detected_text, areal_pattern)
    
    def get_room_names(self, detected_text, room_pattern: List[str]) -> List[TextInfo]:
        """
        Args:
            patterns: List of room patterns to search for in the detected text.
        Returns:
            List of TextInfo objects containing the room
        """
        return self.get_target_text(detected_text, room_pattern)

        
		


    