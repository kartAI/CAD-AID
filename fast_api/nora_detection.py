from ultralytics import YOLO
import json


def find_value(detections: [], key: str) -> str | float | None:
    try:
        json_data = json.loads(detections)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

    if isinstance(json_data, list):
        for item in json_data:
            if key in item:
                value = item[key]
                if isinstance(value, (int, float)):
                    return round(float(value), 2)
                else:
                    return str(value)
        print(f"{key} not found in any item of the JSON.")
        return None
    else:
        print("Invalid JSON format or not a list.")
        return None


def confidence_status(confidence: float) -> bool:
    if confidence > 0.60:
        return True
    elif 0.20 < confidence < 0.59:
        return False


def nora_detection(image) -> dict:
    model = YOLO(r"../runs/detect/Nora/train/weights/best.pt")

    drawing_types = {}

    predict_results = model.predict(image)

    for r in predict_results:
        detections = r.tojson()

        drawing_type: str | None = find_value(detections, "name")
        if drawing_type:
            confidence_value = find_value(detections, "confidence")
            is_confident = confidence_status(confidence_value)
            if is_confident:
                drawing_types = {
                    **drawing_types,
                    drawing_type: True
                }
    return drawing_types
