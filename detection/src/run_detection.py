from ultralytics import YOLO
import os
from PIL import Image
from typing import List, Dict

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "detection_model", "best.pt")
model = YOLO(MODEL_PATH)

def predict_drawings(image: Image.Image, conf_threshold: float = 0.25) -> List[Dict]:
    
    results = model.predict(image, conf=conf_threshold)

    detections = []

    for result in results:
        boxes = result.boxes
      
        names = result.names
        classes = boxes.cls

        # Extract all detections
        for i in range(len(boxes)):
            class_id = int(boxes.cls[i].item())
            confidence = float(boxes.conf[i].item())
            bounding_box = boxes.xyxy[i].tolist()
         
            x1, y1, x2, y2 = map(int, bounding_box)
            
            
            detections.append({
                "class_name": names[class_id],
                "bounding_box": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                },
                "confidence": round(confidence, 4)
            })
    
    return detections