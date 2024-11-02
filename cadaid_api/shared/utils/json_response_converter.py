from typing import List
from .data_structures import Metadata


def json_response_converter(detection_response: List[Metadata]) -> list:
    response = []
    #drawing_types = []
    for file in detection_response:

        if isinstance(file, Metadata):
            obj = file.convert_to_dict()
            drawing_types = []
            if not file.drawing_type:
                obj['drawing_type'] = 'Er du sikker på at dette en byggesakstegning'
            else:
                for dtype in file.drawing_type:
                    if dtype not in drawing_types:
                        drawing_types.append(drawing_types)
                obj['drawing_type'] = dtype
            
            if bool(obj):
                response.append(obj)
    
    return response

