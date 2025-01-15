
import cv2
import numpy as np
from PIL import Image
from typing import List
from shapely.geometry import Polygon, Point
from dataclasses import dataclass
import matplotlib.pyplot as plt
from ultralytics.utils.plotting import colors, Annotator

from utils.data_structures import TextInfo, PolygonInfo  
from shapely.geometry import Point, Polygon
import easyocr
import pytesseract
import cv2
import re

@dataclass
class TextInfo:
    text: str
    bbox: List[tuple]
    probability: float

@dataclass
class PolygonInfo:
    room: bool
    polygon: Polygon

def plot_text_bboxes(image,text_infos: List['TextInfo'], window_title: str = 'Detected Text'):
    for text_info in text_infos:
        bbox = text_info.bbox
        top_left = tuple(map(int, bbox[0]))
        bottom_right = tuple(map(int, bbox[2]))
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(image, text_info.text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    cv2.imshow(window_title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def plot_rooms(image,rooms_found: List['PolygonInfo'], text_infos: List['TextInfo']):
    for room_info in rooms_found:
        polygon = room_info.polygon
        exterior_coords = np.array(polygon.exterior.coords, dtype=np.int32)

        # Draw the polygon on the image
        cv2.polylines(image, [exterior_coords], isClosed=True, color=(255, 0, 0), thickness=2)

        if room_info.room:
            for text_info in text_infos:
                text_bboxes = text_info.bbox
                text_x_min, text_y_min = text_bboxes[0]
                text_x_max, text_y_max = text_bboxes[2]
                cx = int((text_x_min + text_x_max) / 2)
                cy = int((text_y_min + text_y_max) / 2)
                centroid = Point(cx, cy)
                if polygon.contains(centroid):
                    # Draw the centroid on the image
                    cv2.circle(image, (cx, cy), radius=5, color=(0, 0, 255), thickness=-1)
                    label = f"({cx},{cy})"
                    cv2.putText(image, label, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    break

    # Show the image with polygons and centroids
    cv2.imshow('Rooms and Text Centroids', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def easy_ocr(image):
        detected_text = []
        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)
        for result in results:
            bbox, text, prob = result
            text_info = TextInfo(text=text, bbox=bbox, probability=prob)
            detected_text.append(text_info)
        return detected_text
    
def pytesseract_ocr(image) -> List[TextInfo]:
    detected_text = []
    custom_config = r'--oem 3 --psm 11' # TODO: Move this to a config file
    results = pytesseract.image_to_data(image, config=custom_config, lang='nor', output_type = pytesseract.Output.DICT)
    for i in range(len(results['text'])):
        text = results['text'][i]
        if text.strip():
            x, y, w, h = results['left'][i], results['top'][i], results['width'][i], results['height'][i]
            confidence = int(results['conf'][i]) / 100.0
            bbox = [(x,y), (x + w,y), (x + w, y+h), (x, y +h)]
            text_info = TextInfo(text=text, bbox=bbox, probability=confidence)
            detected_text.append(text_info)

    return detected_text

def main():
    image_path = "path/to/image"
    text = pytesseract_ocr(image_path)
    