from ultralytics import YOLO

from config import Config


class ObjectDetection:
    def __init__(self):
        self._config = Config()
        self.model_path = self._config.OBJECT_DETECTION_MODEL_PATH
        self.model_conf = self._config.OBJECT_DETECTION_CONFIDENCE
        
        self.model = YOLO(self.model_path)
    
   
    def process_results(self, image):
        results = self.model(image,
                          save=False, 
                          stream=True, 
                          visualize=False, 
                          conf=self.model_conf)
        
        drawing_types = []
        bbox = []
        confidence = []

        for result in results:
            boxes = result.boxes
            for box, cls, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
                class_name = self.model.names[int(cls)] # Get class name from class ID
                box = box.tolist() # Convert from tensor to list
                conf = conf.item() # Get value from tensor
                drawing_types.append(class_name)
                confidence.append(conf)
                bbox.append(box)
        
        return drawing_types, bbox, confidence