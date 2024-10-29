from typing import List
from shared.utils.models_manager import ObjectDetection
from shared.utils.data_structures import DrawingType


class ObjectDetectionHandler:
    def __init__(self):
        self.model = ObjectDetection()
    def run_detection(self, image):
        # Run object detection on the given image
        self.results = self.model.predictions(image)
        drawing_types, bboxes, confidences = self._create_detection()
        return drawing_types, bboxes, confidences

    def _find_value(self,detection, key: str):
        if key in detection:
            value = detection[key]
            if isinstance(value, (int, float)):
                return round(float(value), 2)
            else:
                return str(value)
        return None
    
    def _get_drawing_type(self) -> List[str]:
        """
        Helper method to extract predicted class labels from the results.
        """
        drawing_types = []
        bbox = []
        confidence = []

        for result in self.results:
            boxes = result.boxes
            for box, cls, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
                class_name = self.model.names[int(cls)]
                drawing_types.append(cls)
                confidence.append(conf)
                bbox.append(box)
                
        return drawing_types, bbox, confidence
  
    def _create_detection(self):
        """
        Stores the detected drawing types in a Detection object.
        """
        drawing_types, bbox, confidence = self._get_drawing_type()
        return drawing_types, bbox, confidence
        #return ObjDetData(drawing_type=drawing_types, confidence=confidence, bbox=bbox)


