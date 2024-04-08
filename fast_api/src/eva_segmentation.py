from ultralytics import YOLO
import numpy as np
import cv2
from ultralytics.utils.plotting import Annotator, colors
from Levenshtein import distance as levenshtein_distance
import regex
from .regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from cv2.typing import MatLike

def plot_bboxes_roomname_missing(detected_text_list, yolo_results, image):
    for r in yolo_results:
        yolo_bboxes = r.boxes.xyxy.numpy()  # Convert to NumPy array for easier handling

        for yolo_bbox in yolo_bboxes:
            found_text_in_room = False

            for text_info in detected_text_list:
                text_x_min, text_y_min = text_info[0]  # Top-left corner
                text_x_max, text_y_max = text_info[2]  # Bottom-right corner

                # Check if the text bounding box is inside the YOLO bounding box
                if (text_x_min >= yolo_bbox[0] and text_x_max <= yolo_bbox[2] and
                    text_y_min >= yolo_bbox[1] and text_y_max <= yolo_bbox[3]):
                    found_text_in_room = True
                    break  # Found a text box inside the room, no need to check further

            if not found_text_in_room:
                return {'room_names': 'Mangler rombenevnelse'}
    return {}

    

def eva_segmentation(image: MatLike, detected_text, detected_text_position):
    img_copy = image.copy()
    model = YOLO(r"./models/Eva/best.pt")

    results = model.track(image, persist=False,conf=0.4)

    return plot_bboxes_roomname_missing(detected_text_position, results, img_copy)
