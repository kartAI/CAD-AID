from typing import List
from .models_manager import Segmentation
from shapely.geometry import Point, Polygon
from .data_structures import TextInfo, PolygonInfo

class SegmentationHandler:
    def __init__(self):
        self.model = Segmentation()
        self.seg_results = None
        self.rooms_found = []
       

    def run_segmentation(self, image_path):
        # Run segmentation on the given image
        self.seg_results = list(self.model.predictions(image_path))  # Konverter til liste

    def find_text_segments(self, target_words: List[TextInfo]) -> List[PolygonInfo]:
        """
        Checks if the text is inside the polygon/segmented room and returns a list of PolygonInfo objects.
        """
        rooms_found = []
        if not self.seg_results:
           
            return rooms_found

        for r in self.seg_results:
            if not hasattr(r, 'masks') or r.masks is None:
               
                continue

            masks = r.masks.xy
            if not masks:
               
                continue

            for mask in masks:
                polygon = Polygon(mask)
                is_name_found = False
                for i in target_words:
                    text_bboxes = i.bbox
                    text_x_min, text_y_min = text_bboxes[0]
                    text_x_max, text_y_max = text_bboxes[2]
                    cx = (text_x_min + text_x_max)/2
                    cy = (text_y_min + text_y_max)/2
                    centroid = Point(cx, cy)
                    is_inside = polygon.contains(centroid)
                    if is_inside:
                        is_name_found = True
                        break
                
                rooms_polygons = PolygonInfo(room=is_name_found, polygon=polygon)
                rooms_found.append(rooms_polygons)

        self.rooms_found = rooms_found
        return self.rooms_found

    def count_rooms(self) -> tuple[int, int]:
        true_count = sum(1 for room in self.rooms_found if room.room)
        false_count = sum(1 for room in self.rooms_found if not room.room)
        return true_count, false_count