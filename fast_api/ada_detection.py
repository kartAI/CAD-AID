import easyocr
import regex
from regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern


def ada_detection(image, file_types):
    obj = {}

    # midlertidig if
    if 'fasade' in file_types or 'plantegning' in file_types:
        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)

        decoded_labels = []

        for result in results:
            decoded_labels.append(result[1])

        conditions = {
            'fasade': {
                'scale': (scale_pattern, 'Mangler målestokk'),
                'cardinal_direction': (cardinal_direction_pattern, 'Mangler himmelretning')
            },
            'plantegning': {
                'room_names': (room_pattern, 'Mangler romnavn')
            }
        }

        for file_type in file_types:
            for drawing_type, sub_conditions in conditions.items():
                if drawing_type == file_type:
                    for condition, (pattern, message) in sub_conditions.items():
                        if not any(regex.search(pattern, ocr_label.lower()) for ocr_label in decoded_labels):
                            obj[condition] = message

    return obj
