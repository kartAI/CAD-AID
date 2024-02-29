import easyocr
import regex
from regex_patterns import scale_pattern


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
        for ocr_label in decoded_labels:
            #print('målestokk: ', regex.search(scale_pattern, ocr_label))
            if regex.search(scale_pattern, ocr_label):
                print('kommer inn')
                include = True
        if not include:
            obj = {
                #**file,
                'scale': 'Mangler målestokk'
            }
        print(obj)
    return obj
