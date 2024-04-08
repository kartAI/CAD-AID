from ultralytics import YOLO
import numpy as np
import cv2
from ultralytics.utils.plotting import Annotator, colors
import regex
from .regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from cv2.typing import MatLike
    

def eva_segmentation(image: MatLike, detected_text, detected_text_coordinates):
    model = YOLO(r"./models/Eva/best.pt")

    results = model.track(image, persist=False,conf=0.4)

    for r in results:
        yolo_bboxes = r.boxes.xyxy.numpy()  # Convert to NumPy array for easier handling

        for yolo_bbox in yolo_bboxes:
            found_text_in_room = False
            detected_index = []

            for index, text_info in enumerate(detected_text_coordinates):
                text_x_min, text_y_min = text_info[0]  # Top-left corner
                text_x_max, text_y_max = text_info[2]  # Bottom-right corner

                # Check if the text bounding box is inside the YOLO bounding box
                if (text_x_min >= yolo_bbox[0] and text_x_max <= yolo_bbox[2] and
                    text_y_min >= yolo_bbox[1] and text_y_max <= yolo_bbox[3]):
                    # detected_index.append(index)
                    found_text_in_room = True
                    break  # Found a text box inside the room, no need to check further

            if not found_text_in_room:
                return {'room_names': 'Mangler rombenevnelse'}
            # for i in detected_index:
            #     print(detected_text[i])
            #     if not regex.search(room_pattern, detected_text[i]):
            #         print('ikke rombenevnelse')
    return {}
