from ultralytics import YOLO
import json


def find_value(detection: {}, key: str) -> str | float | None:
    if key in detection:
        value = detection[key]
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        else:
            return str(value)
    return None


def confidence_status(confidence: float) -> bool:
    if confidence > 0.60:
        return True
    return False
    #elif 0.20 < confidence < 0.59:
    #    return False


def nora_detection(image) -> dict:
    model = YOLO(r"../runs/detect/Nora/train/weights/best.pt")

    drawing_types = {}

    predict_results = model.predict(image)

    for d in json.loads(predict_results[0].tojson()):
        drawing_type: str | None = find_value(d, "name")
        if drawing_type:
            confidence_value = find_value(d, "confidence")
            is_confident = confidence_status(confidence_value)
            if is_confident:
                drawing_types = {
                    **drawing_types,
                    drawing_type: True
                }
    return drawing_types
