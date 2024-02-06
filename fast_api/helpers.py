import json
from models import Detection, Feedback, Status


# support int and str value
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


def confidence_status(confidence: float, drawing_type: str) -> Feedback:
    if confidence > 0.60:
        return {
            "status": Status.success.value,
            "message": f"AI modellen er ganske sikker på at dette er en {drawing_type}"
        }
    elif 0.20 < confidence < 0.59:
        return {
            "status": Status.warning.value,
            "message": f"AI modellen er usikker på om dette er en {drawing_type}"
        }


def check_detections(detections: []) -> Detection:
    drawing_type: str | None = find_value(detections, "name")
    if not drawing_type:
        return {
            "type": {
                "status": Status.error.value,
                "message": "Er du sikker på at dette er riktig tegning?"
            }
        }
    else:
        confidence = find_value(detections, "confidence")
        confidence_response = confidence_status(confidence, drawing_type)
        return {
            "type": confidence_response
        }
