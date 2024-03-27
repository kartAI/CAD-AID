from ultralytics import YOLO
import numpy as np
import cv2
from ultralytics.utils.plotting import Annotator, colors
from Levenshtein import distance as levenshtein_distance
import regex
from .regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern


def eva_segmentation(image, detected_text):
    model = YOLO(r"./models/Eva/best.pt")

    results = model.track(image, persist=False,conf=0.4)

    #if not any(regex.search(room_pattern, ocr_label.lower()) for ocr_label in detected_text):
    
    return {}
