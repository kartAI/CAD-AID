from ultralytics import YOLO
import json
from cv2.typing import MatLike


def find_value(detection: {}, key: str) -> str | float | None:
    if key in detection:
        value = detection[key]
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        else:
            return str(value)
    return None


def nora_detection(image: MatLike) -> list:
    model = YOLO(r"./models/Nora/best.pt")

    drawing_types = []

    predict_results = model.predict(image)

    for d in json.loads(predict_results[0].tojson()):
        drawing_type: str | None = find_value(d, "name")
        if drawing_type:
            confidence = find_value(d, "confidence")
            if confidence > 0.60:
                drawing_types.append(drawing_type)
    return drawing_types
