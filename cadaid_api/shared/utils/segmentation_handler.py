from typing import List
from .models_manager import Segmentation
from shapely.geometry import Point, Polygon
from .data_structures import TextInfo, PolygonInfo

class SegmentationHandler:
    def __init__(self):
        self.model = Segmentation()
       
        self.rooms_found = []
       

    def run_segmentation(self, image_path):
        # Run segmentation on the given image
        seg_results = list(self.model.predictions(image_path))  # Konverter til liste
        return seg_results
    
    
    
    def filter_text_within_polygons(self, seg_results, target_words: List[TextInfo]) -> List[TextInfo]:
        """
        Check if room names exists in segmented masks
        """
        text_inside_poly = []
        num_rooms = 0
    
        for r in seg_results:
            for mask in r.masks.xy:
                num_rooms +=1
                polygon = Polygon(mask)
                for word in target_words:
                    text_boxes = word.bbox
                    if text_boxes:
                        cx = (text_boxes[0][0] + text_boxes[2][0]) / 2
                        cy = (text_boxes[0][1] + text_boxes[2][1]) / 2
                        centroid = Point(cx,cy)

                        if polygon.contains(centroid):
                            text_inside_poly.append(word)
        
        return text_inside_poly
    