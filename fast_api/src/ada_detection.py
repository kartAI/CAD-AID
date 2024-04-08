import easyocr
import regex
from .regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from cv2.typing import MatLike

def ada_detection(image: MatLike, file_types):
    obj = {}

    reader = easyocr.Reader(['no'], gpu=False)
    results = reader.readtext(image, width_ths=0.7)

    detected_text = []
    detected_text_coordinates = []

    for result in results:
        bbox,text,prob = result
        detected_text.append(text)
        detected_text_coordinates.append(bbox)

    conditions = {
        'fasade': {
            'scale': (scale_pattern, 'Mangler målestokk'),
            'cardinal_direction': (cardinal_direction_pattern, 'Mangler himmelretning')
        },
        # 'plantegning': {
        #     'room_names': (room_pattern, 'Mangler romnavn')
        # }
    }
    
    for file_type in file_types:
        for drawing_type, sub_conditions in conditions.items():
            if drawing_type == file_type:
                for condition, (pattern, message) in sub_conditions.items():
                    if not any(regex.search(pattern, ocr_label.lower()) for ocr_label in detected_text):
                        obj[condition] = message

    return obj, detected_text, detected_text_coordinates
