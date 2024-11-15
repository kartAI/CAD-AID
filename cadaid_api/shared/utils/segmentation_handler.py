from typing import List
from .models_manager import Segmentation

class SegmentationHandler:
    def __init__(self):
        self.model = Segmentation()
       
        self.rooms_found = []
       

    def run_segmentation(self, image_path):
        # Run segmentation on the given image
        seg_results = list(self.model.predictions(image_path))  # Konverter til liste
        return seg_results
    


    
    

