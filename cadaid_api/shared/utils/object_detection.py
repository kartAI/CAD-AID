from typing import List
from .models_manager import ObjectDetection
from .data_structures import DrawingType
import json
class ObjectDetectionHandler:
    def __init__(self):
        self.model = ObjectDetection()
      
    def run_detection(self, image):
        # Run object detection on the given image
        self.results = self.model.predictions(image)
        drawing_types, bboxes, confidences = self._get_drawing_type()
        return drawing_types, bboxes, confidences
    
    def _get_drawing_type(self):
        """
        Helper method to extract predicted class labels from the results.

        Returns:
            Drawing types: class name as string
            bbox: Bounding box in xyxy format
            conf: Confidence from prediction

        """
        drawing_types = []
        bbox = []
        confidence = []

        for result in self.results:
            boxes = result.boxes
            for box, cls, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
                class_name = self.model.names[int(cls)] # Get class name from class ID
                box = box.tolist() # Convert from tensor to list
                conf = conf.item() # Get value from tensor
                drawing_types.append(class_name)
                confidence.append(conf)
                bbox.append(box)
        
        return drawing_types, bbox, confidence
  
        


