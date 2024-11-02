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
        text_inside_poly = []
        added_texts = set()

        for r in seg_results:
            #if not hasattr(r, 'masks') or r.masks is None:
            #    continue
            for mask in r.masks.xy:
                polygon = Polygon(mask)
                for word in target_words:
                    text_boxes = word.bbox
                    if text_boxes:
                        cx = (text_boxes[0][0] + text_boxes[2][0]) / 2
                        cy = (text_boxes[0][1] + text_boxes[2][1]) / 2
                        centroid = Point(cx,cy)

                        if polygon.contains(centroid):
                            unique_key = (word.text, tuple(map(tuple, word.bbox)))
                            if unique_key not in added_texts:
                                text_inside_poly.append(word)
                                added_texts.add(unique_key)
        
        return text_inside_poly
    