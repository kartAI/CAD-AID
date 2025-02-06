from pydantic import BaseModel
from typing import List, Optional
from dataclasses import dataclass
import os
from difflib import SequenceMatcher
import numpy as np
import cv2
from shapely.geometry import Point, Polygon
import re

from .data_structures import TextData, RoomArea
from config import Config


def load_txt_files(file_path):
    with open(file_path, "r") as f:
        text = [line.strip() for line in f.readlines()]
        #text = [line.strip() for line in f]
    return text


class StringMatcher:
        
    def find_matches(self,target_text, ocr_text: List[TextData]) -> List[TextData]:
        
        matches = []
        target_sorted = sorted(target_text, key=len, reverse=True)

        pattern = r'\b(' + '|'.join(target_sorted) + r')\b'

        for text in ocr_text:
            match = re.search(pattern, text.text, re.IGNORECASE)
            if match:
                matches.append(text)

        return matches

def regex_area(ocr_text: List[TextData]) -> List[TextData]:
    matches= []
    float_pattern = r'-?\d+(\.\d+)?(e-?\d+)?'
    #float_pattern = r'^\d+,\d+m\??$|^\d+m2$'
    for ocr in ocr_text:
        match = re.search(float_pattern, ocr.text, re.IGNORECASE)
        if match:
            matches.append(ocr)
    return matches


def crop_image(image,bbox):
    x_min, y_min, x_max, y_max = bbox
    x_min = max(0, int(x_min))
    y_min = max(0, int(y_min))
    x_max = min(image.shape[1], int(x_max))  # Width of the image
    y_max = min(image.shape[0], int(y_max))
    cropped_image = image[y_min:y_max, x_min:x_max]

    return cropped_image

def filter_text_within_object(extracted_text: List[TextData], object_bbox) -> List[TextData]:
    """
    Check if the text is within floorplan drawing using the bbox from object detection
    """
    object_left_x, object_top_y, object_right_x, object_bottom_y = object_bbox

    filtered_text = []
    for ocr_info in extracted_text:
        text_bbox = ocr_info.bbox
        text_left_x, text_top_y, text_right_x, text_bottom_y = text_bbox
        # Check if the text_bbox is within the object_bbox
        is_within = (text_left_x >= object_left_x and 
                    text_top_y >= object_top_y and 
                    text_right_x <= object_right_x and 
                    text_bottom_y <= object_bottom_y)
        if is_within:
            text_info = TextData(text=ocr_info.text, bbox=ocr_info.bbox, probability=ocr_info.probability)
            filtered_text.append(text_info)
    return filtered_text

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(3,3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    return thresh

def extract_float(text):
    match = re.search(r"\d+(\.\d+)?", text)
    return float(match.group()) if match else None

class Floorplan:
    def __init__(self):
        self.matcher = StringMatcher()
    
    def get_rooms_text(self, ocr_results, file_path):
        text_path = os.path.join(os.path.dirname(__file__), file_path)
        valid_rooms = load_txt_files(text_path)
        matched_text = self.matcher.find_matches(valid_rooms, ocr_results)
        return matched_text
    
    def get_BRA_info(self, extracted_text: List[TextData]):
        float_pattern = r'^\d+,\d+(\s*m\??)?$'
        bra_pattern = r'BRA'

        for i, ocr in enumerate(extracted_text):
            text = ocr.text
            text_bbox = ocr.bbox
            center_x = (text_bbox[0] + text_bbox[2]) / 2
            center_y = (text_bbox[1] + text_bbox[3]) / 2

            if re.search(bra_pattern, text, re.IGNORECASE):
                closest_area = None
                closest_prob = None
                closest_bbox = None
            
                closest_distance = float('inf')

                for j in range(i + 1, len(extracted_text)):
                    next_text = extracted_text[j].text
                    next_bbox = extracted_text[j].bbox
                    next_prob = extracted_text[j].probability
                    next_center_x = (next_bbox[0] + next_bbox[2]) / 2
                    next_center_y = (next_bbox[1] + next_bbox[3]) / 2

                    if re.match(float_pattern, next_text):
                      
                        distance = ((center_x - next_center_x) ** 2 + (center_y - next_center_y) ** 2) ** 0.5
                        
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_area = next_text
                            closest_bbox = next_bbox
                            closest_prob = next_prob
                        

                if closest_area:
                    return TextData(text=closest_area, probability=closest_prob, bbox=closest_bbox)
                    #return closest_area
                
    def get_BYA_info(self, extracted_text: List[TextData]):
        float_pattern = r'^\d+,\d+(\s*m\??)?$'
        bra_pattern = r'BYA'

        for i, ocr in enumerate(extracted_text):
            text = ocr.text
            text_bbox = ocr.bbox
            center_x = (text_bbox[0] + text_bbox[2]) / 2
            center_y = (text_bbox[1] + text_bbox[3]) / 2

            if re.search(bra_pattern, text, re.IGNORECASE):
                closest_area = None
                losest_prob = None
                closest_bbox = None
                closest_distance = float('inf')

                for j in range(i + 1, len(extracted_text)):
                    next_text = extracted_text[j].text
                    next_bbox = extracted_text[j].bbox
                    next_prob = extracted_text[j].probability
                    next_center_x = (next_bbox[0] + next_bbox[2]) / 2
                    next_center_y = (next_bbox[1] + next_bbox[3]) / 2

                    if re.match(float_pattern, next_text):
                      
                        distance = ((center_x - next_center_x) ** 2 + (center_y - next_center_y) ** 2) ** 0.5
                        
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_area = next_text
                            closest_bbox = next_bbox
                            closest_prob = next_prob

                if closest_area:
                    return TextData(text=closest_area, probability=closest_prob, bbox=closest_bbox)
                    #return closest_area
    
    def is_point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon."""
        return polygon.contains(Point(point))

    
    def get_area_info(self, ocr_text: List[TextData], all_rooms: List[TextData], seg_masks: List[List[List[float]]]) -> List[RoomArea]:
        areas = []
        float_pattern = r'^\d+,\d+(\s*m\??)?$'  #To match e.g "17,5", "15,0m?", "2,0m"

        for room_data in all_rooms:
            room_text = room_data.text
            room_bbox = room_data.bbox
            room_center_x = (room_bbox[0] + room_bbox[2]) / 2
            room_center_y = (room_bbox[1] + room_bbox[3]) / 2
            room_point = (room_center_x, room_center_y)

            closest_area = None
            closest_distance = float('inf')

            for text_data in ocr_text:
                text = text_data.text
                bbox = text_data.bbox

                if re.match(float_pattern, text):
                    center_x = (bbox[0] + bbox[2]) / 2
                    center_y = (bbox[1] + bbox[3]) / 2
                    point = (center_x, center_y)

                    for mask in seg_masks:
                        polygon = Polygon(mask)
                        if self.is_point_in_polygon(point, polygon) and self.is_point_in_polygon(room_point, polygon):
                            
                            distance = ((room_center_x - center_x) ** 2 + (room_center_y - center_y) ** 2) ** 0.5
                            
                          
                            if distance < closest_distance:
                                closest_distance = distance
                                closest_area = RoomArea(room=room_text, areal=text)

            if closest_area:
                areas.append(closest_area)

        return areas
    
    

    



