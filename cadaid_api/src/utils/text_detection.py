from typing import List, Optional
from .data_structures import TextInfo

import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import easyocr
import cv2
import re
from typing import List
from config import Config

from .data_structures import TextInfo, PolygonInfo 


""""
Core functionality for OCR extraction and text detection

"""


		
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
        

    def get_target_text(self,patterns: List[str])-> List[TextInfo]:
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
        return self.target_words

    def get_cardinal_direction(self, patterns: List[str]) -> Optional[str]:
        text_infos = self.get_target_text(patterns)
        return text_infos[0].text if text_infos else None

    def get_scale(self, patterns: List[str]) -> Optional[str]:
        text_infos = self.get_target_text(patterns)
        return text_infos[0].text if text_infos else None

    def get_room_names(self, patterns: List[str]) -> List[TextInfo]:
        """
        Args:
            patterns: List of room patterns to search for in the detected text.
        Returns:
            List of TextInfo objects containing the room
        """
        return self.get_target_text(patterns)

        
		


    