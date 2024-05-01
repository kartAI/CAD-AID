from typing import List
from .models import Detection


def json_response_converter(detection_response: List[Detection]) -> list:
    response = []
    #drawing_types = []
    for file in detection_response:
        if len(file) > 1:
            obj = {
                'file_name': file['file_name']
            }
            drawing_types = []
            if not file['drawing_types']:
                obj = {
                    **obj,
                    'drawing_type': 'Er du sikker på at dette er en byggesakstegning?'
                }
            else:
                for drawing_type in file['drawing_types']:
                    if drawing_type not in drawing_types:
                        drawing_types.append(drawing_type)
                obj = {
                    **obj,
                    'drawing_type': drawing_types
                }
            for key in ['scale', 'room_names', 'cardinal_direction']:
                if file.get(key):
                    obj[key] = file[key]

            if bool(obj):
                response.append(obj)

    #for key in drawing_types:
    #    response.append(key)
    return response
