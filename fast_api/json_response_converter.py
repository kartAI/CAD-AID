from typing import List
from models import Detection


def json_response_converter(detection_response: List[Detection]) -> list:
    response = []
    drawing_types = []
    for file in detection_response:
        obj = {}

        if not file['drawing_types']:
            obj = {
                **obj,
                'drawing_type': 'Er du sikker på at dette er riktig tegning?'
            }
        else:
            for drawing_type in file['drawing_types']:
                print('type: ', drawing_type)
                #if not drawing_types or not drawing_types[drawing_type]:
                drawing_types.append(drawing_type)

        for key in ['scale', 'room_names', 'cardinal_direction']:
            if file.get(key):
                obj[key] = file[key]

        if bool(obj):
            response.append({
                file['file_name']: obj
            })
    print(drawing_types)
    return response
