import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import easyocr
import cv2
import re
from typing import List
from utils.config import Config
from utils.plotting.text_plotter import TextPlotter
from utils.data_structures import TextInfo, PolygonInfo 


""""
Core functionality for OCR extraction and text detection

"""


class OCR:
	def __init__(self):
		self._config = Config()
		self.image_path = self._config.PREDICTION_IMAGE_PATH
		self.image = cv2.imread(self.image_path)
		self.detected_text: List[TextInfo] = self.easy_ocr_detection()
		

	def easy_ocr_detection(self) -> List[TextInfo]:
		reader = easyocr.Reader(['no'])
		results = reader.readtext(self.image)
		detected_text = []

		for result in results:
			bbox, text, prob = result
			text_info = TextInfo(text=text, bbox=bbox, probability=prob)
			detected_text.append(text_info)

		return detected_text
	
	

	
class TextDetection(OCR):
	def __init__(self ):
		super().__init__()
		
		self.target_words: List[TextInfo] = [] 
		self.plotter = TextPlotter(self)

	def get_target_text(self,patterns: List[str])-> List[TextInfo]:
		
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
	
	def plot_text_bboxes(self, window_title: str = 'Detected Text') -> None:
		self.plotter.plot_text_bboxes(self.target_words, window_title)
	
	def plot_rooms(self,rooms_found: List[PolygonInfo]) -> None:
		self.plotter.plot_rooms(rooms_found, self.target_words)
	
	
