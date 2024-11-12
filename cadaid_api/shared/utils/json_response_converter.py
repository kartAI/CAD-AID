from typing import List
from .data_structures import Metadata


def json_response_converter(detection_response: List[Metadata]) -> list:
    response = []
    for file in detection_response:
        if isinstance(file, Metadata):
            obj = file.convert_to_dict()
            if not file.drawing_type:
                obj['drawing_type'] = 'Er du sikker på at dette en byggesakstegning'
            else:
                drawing_types = []
                for dtype in file.drawing_type:
                    if dtype not in drawing_types:
                        drawing_types.append(dtype)
                obj['drawing_type'] = drawing_types[0] if drawing_types else None
            
            if bool(obj):
                response.append(obj)
        elif isinstance(file, dict):
            response.append(file)
    
    return response if response else [{"filename": "unknown", "detections": [], "store": {}}]

