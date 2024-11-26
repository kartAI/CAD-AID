from typing import List, Optional

import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shapely.geometry import Point, Polygon
import easyocr
import pytesseract
import cv2
import re
from shared.config import Config
import math
from .data_structures import TextInfo 
from .regex_patterns import areal_pattern, room_pattern
from shared.utils.logger import cadaid_logger

logger = cadaid_logger(__name__)


""""
Core functionality for OCR extraction and text detection

"""

		
class TextDetection():
    def __init__(self ):
        
        self.target_words: List[TextInfo] = []
        self.detected_text = []
        

    def easy_ocr(self,image):
        detected_text = []
        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)
        for result in results:
            bbox, text, prob = result
            text_info = TextInfo(text=text, bbox=bbox, probability=prob)
            detected_text.append(text_info)
        return detected_text
    
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


    def get_target_text(self,detected_text: List[TextInfo], patterns: List[str])-> List[TextInfo]:
        """
        Filters all detected text in image based on regex pattern
        """
        target_text = []

        for text_info in detected_text:
            text = text_info.text
            bbox = text_info.bbox
            prob = text_info.probability

            if re.search(patterns, text, re.IGNORECASE):
                target_text_info = TextInfo(text=text, bbox=bbox, probability=prob)
                target_text.append(target_text_info)
                   
        return target_text

    def get_cardinal_direction(self, detected_text, patterns) -> List[TextInfo]:
        target_text = self.get_target_text(detected_text, patterns)
        return target_text

    def get_scale(self, detected_text,patterns: List[str]) -> List[TextInfo]:
        return self.get_target_text(detected_text, patterns)
        

    def get_room_names(self, detected_text, room_pattern: List[str]) -> List[TextInfo]:
        """
        Args:
            detected_text: List of TextInfo objects containing all detected text
            room_pattern: List of patterns to match room names
        Returns:
            List of TextInfo objects containing rooms
        """
        return self.get_target_text(detected_text, room_pattern)
    
    def get_gnr_bnr(self, detected_text, patterns) -> List[TextInfo]:
        """Get gnr/bnr from detected text"""
        return self.get_target_text(detected_text, patterns)
    
    def append_areas_to_rooms(self, rooms: List[TextInfo], detected_text: List[TextInfo]) -> List[TextInfo]:
        """
        Append areas to room names if found nearby
        """
        logger.info("Starting area appending")
        result = []
        
        # First find all areas in the detected text
        areas = []
        for text_info in detected_text:
            area_match = re.search(areal_pattern, text_info.text)
            if area_match:
                # Get the full original text including the unit
                original_area = area_match.group(0)
                # Get just the number part
                number_part = original_area.split('m')[0].strip()
                
                try:
                    # Convert to float just for validation
                    test_value = float(number_part.replace(',', '.'))
                    
                    # Check if it's likely a misread decimal (e.g., 45 when it should be 4.5)
                    if test_value > 30:
                        # Check if there's a larger room nearby that might justify this size
                        is_large_room = False
                        for room in rooms:
                            if "stue" in room.text.lower() or "kjøkken" in room.text.lower():
                                room_center = ((room.bbox[0][0] + room.bbox[2][0])/2, (room.bbox[0][1] + room.bbox[2][1])/2)
                                area_center = ((text_info.bbox[0][0] + text_info.bbox[2][0])/2, (text_info.bbox[0][1] + text_info.bbox[2][1])/2)
                                distance = ((room_center[0] - area_center[0])**2 + (room_center[1] - area_center[1])**2)**0.5
                                if distance < 100:  # If area is close to a large room
                                    is_large_room = True
                                    break
                        
                        if not is_large_room and ',' not in number_part and '.' not in number_part:
                            test_value = test_value / 10
                            number_part = f"{test_value:.1f}".replace('.', ',')
                    
                    if test_value > 0 and test_value < 1000:  # Reasonable room size limits
                        areas.append({
                            'text': f"{number_part} m²",
                            'bbox': text_info.bbox,
                            'value': test_value
                        })
                        logger.info(f"Found valid area: {number_part} m²")
                except ValueError:
                    logger.warning(f"Invalid area value: {number_part}")
        
        logger.info(f"Total areas found: {len(areas)}")
        
        for room_info in rooms:
            room_text = room_info.text
            room_bbox = room_info.bbox
            
            # Find closest area by comparing bounding boxes
            closest_area = None
            min_distance = float('inf')
            
            for area in areas:
                try:
                    # Calculate distance between room bbox and area bbox
                    room_center = ((room_bbox[0][0] + room_bbox[2][0])/2, (room_bbox[0][1] + room_bbox[2][1])/2)
                    area_center = ((area['bbox'][0][0] + area['bbox'][2][0])/2, (area['bbox'][0][1] + area['bbox'][2][1])/2)
                    
                    # Calculate horizontal and vertical distances separately
                    horizontal_dist = abs(room_center[0] - area_center[0])
                    vertical_dist = abs(room_center[1] - area_center[1])
                    
                    # Prefer areas that are closer horizontally and slightly below or beside the room name
                    if horizontal_dist < 100 and vertical_dist < 50:  # Adjust thresholds as needed
                        total_distance = horizontal_dist + (vertical_dist * 2)  # Weight vertical distance more
                        if total_distance < min_distance:
                            min_distance = total_distance
                            closest_area = area
                    
                except Exception as e:
                    logger.error(f"Error calculating distance: {str(e)}")
            
            if closest_area:
                combined_text = f"{room_text} ({closest_area['text']})"
                logger.info(f"Combined room and area: {combined_text}")
            else:
                combined_text = room_text
                logger.info(f"No area found for room: {room_text}")
                
            result.append(TextInfo(text=combined_text, bbox=room_bbox, probability=room_info.probability))
        
        return result

class TextProximityFilter:
    def filter_text_within_polygons(self, seg_results, target_words: List[TextInfo]) -> List[TextInfo]:
        """
        Filters text information to check if room names exists within segmented masks
        """
        
        text_inside_poly = []
        num_rooms = 0
        for result in seg_results:
            for mask in result.masks.xy:
                num_rooms +=1
                polygon = Polygon(mask)
                text_inside_poly.extend(self._find_text_in_polygons(polygon, target_words))
        
        return text_inside_poly
    
    def check_text_within_object(self, text_inside_poly: List[TextInfo], objdet_bbox) -> List[str]:
        """
        Retrieve only the text inside current detected object to avoid duplicate room names

        Returns:
            room names: room names as string
        """
        x_min,y_min,x_max,y_max = objdet_bbox
        room_names = []
        for text_info in text_inside_poly:
            text_bboxes = text_info.bbox
            cx, cy = self._calculate_centroid(text_bboxes)
            
            if(x_min <=cx <=x_max) and (y_min <=cy <=y_max):
                room = text_info.text
                room_names.append(room)
        
        return room_names
    
    def _find_text_in_polygons(self, polygon: Polygon, target_words: List[TextInfo]) -> List[TextInfo]:
        """
        Helper function to find text within polygons
        """
        texts_in_polygon = []
        for word in target_words:
            text_boxes = word.bbox
            if not text_boxes:
                continue
            cx,cy = self._calculate_centroid(text_boxes)
            centroid = Point(cx,cy)
            if polygon.contains(centroid):
                texts_in_polygon.append(word)
        
        return texts_in_polygon
    
    def text_proximity_to_object(self, detected_text: List[TextInfo], objdet_bbox):
        """
        Function to determine the correct text label to current object by calculating distance to object detecion bbox
        """
        min_distance = float('inf')
        
        closest_text = None
        cx_obj, cy_obj = self._calculate_centroid_objectdet(objdet_bbox)

        for text_info in detected_text:
            text_bbox = text_info.bbox

            cx_text,cy_text = self._calculate_centroid(text_bbox)
            distance = math.sqrt((cx_text - cx_obj)**2 + (cy_text - cy_obj)**2)
            text = text_info.text
            if distance < min_distance:
                min_distance = distance
                closest_text = text
                
        
        return [closest_text]
        
        
    def _calculate_centroid_objectdet(self, objdet_bbox):
        x_min,y_min,x_max,y_max = objdet_bbox

        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) /2

        return cx, cy
    
    def _calculate_centroid(self, text_boxes: List[List[float]]):
        """
        Calculate centroid of bounding box

        """
        cx = (text_boxes[0][0] + text_boxes[2][0]) / 2
        cy = (text_boxes[0][1] + text_boxes[2][1]) / 2

        return cx,cy
		


    