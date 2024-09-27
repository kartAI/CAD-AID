from typing import List
from .data_structures import Metadata


def json_response_converter(detection_response: List[Metadata]) -> list:
    response = []
    #drawing_types = []
    for file in detection_response:

        if isinstance(file, Metadata):
            obj = file.convert_to_dict()
            drawing_types = []
            if not file.drawing_types:
                obj['drawing_types'] = 'Er du sikker på at dette en byggesakstegning'
            else:
                for drawing_type in file.drawing_types:
                    if drawing_type not in drawing_types:
                        drawing_types.append(drawing_type)
                obj['drawing_type'] = drawing_types
            
            if bool(obj):
                response.append(obj)
    
    return response

