
import cv2
import numpy as np
from PIL import Image
from typing import List
from shapely.geometry import Polygon, Point
from dataclasses import dataclass
import matplotlib.pyplot as plt
from ultralytics.utils.plotting import colors, Annotator

from utils.data_structures import TextInfo, PolygonInfo  


class TextPlotter:
    def __init__(self, ocr_instance):
        self.image = ocr_instance.image

    def plot_text_bboxes(self, text_infos: List['TextInfo'], window_title: str = 'Detected Text'):
        for text_info in text_infos:
            bbox = text_info.bbox
            top_left = tuple(map(int, bbox[0]))
            bottom_right = tuple(map(int, bbox[2]))
            cv2.rectangle(self.image, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(self.image, text_info.text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow(window_title, self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def plot_rooms(self, rooms_found: List['PolygonInfo'], text_infos: List['TextInfo']):
        for room_info in rooms_found:
            polygon = room_info.polygon
            exterior_coords = np.array(polygon.exterior.coords, dtype=np.int32)

            # Draw the polygon on the image
            cv2.polylines(self.image, [exterior_coords], isClosed=True, color=(255, 0, 0), thickness=2)

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
                        cv2.circle(self.image, (cx, cy), radius=5, color=(0, 0, 255), thickness=-1)
                        label = f"({cx},{cy})"
                        cv2.putText(self.image, label, (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        break

        # Show the image with polygons and centroids
        cv2.imshow('Rooms and Text Centroids', self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


