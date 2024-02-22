import json

from sympy import false, true

from models import Detection, Feedback, Status
import easyocr


def easy_ocr_detection(image):
	reader = easyocr.Reader(['no'])
	results = reader.readtext(image)

	bounding_boxes = []
	decoded_labels = []

	for result in results:
		bounding_boxes.append(result[0])
		decoded_labels.append(result[1])

	print(decoded_labels)
	print(bounding_boxes)
	return decoded_labels


def confidence_status(confidence: float) -> bool:
    if confidence > 0.60:
        return True
    elif 0.20 < confidence < 0.59:
        return False


def check_detections(detections: []) -> Detection:
    print('detections', detections)

    detections_res: Detection = {
        'plantegning': False,
        'snitt': False,
        'situasjonskart': False,
        'fasade': False
    }

    for d in json.loads(detections):
        drawing_type = d["name"]
        confidence = d["confidence"]
        validate = confidence_status(confidence)
        detections_res[drawing_type] = validate

    return detections_res
