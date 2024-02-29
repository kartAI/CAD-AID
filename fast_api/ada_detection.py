import easyocr
import regex
from regex_patterns import scale_pattern, cardinal_direction_pattern


def ada_detection(image, file_type):
    obj = {}

    # dette skal fikses
    if 'fasade' in file_type and file_type['fasade']:

        reader = easyocr.Reader(['no'])
        results = reader.readtext(image)

        decoded_labels = []

        for result in results:
            decoded_labels.append(result[1])

        include = False
        include_direction = False

        for ocr_label in decoded_labels:
            if regex.search(scale_pattern, ocr_label):
                include = True
            if regex.search(cardinal_direction_pattern, ocr_label.lower()):
                include_direction = True

        print(include, include_direction)
        if not include:
            obj = {
                **obj,
                'scale': 'Mangler målestokk'
            }
        if not include_direction:
            obj = {
                **obj,
                'cardinal_direction': 'Mangler himmelretning'
            }
        print(obj)
    return obj
