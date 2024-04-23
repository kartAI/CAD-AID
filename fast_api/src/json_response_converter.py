from typing import List
from .models import Detection
import json


def json_response_converter(file: Detection) -> Detection:
    response = []
    #drawing_types = []
    # for file in detection_response:
    obj = {
        "file_name": file["file_name"]
    }
    drawing_types = []
    if not file["drawing_types"]:
        obj = {
            **obj,
            "drawing_type": "Er dette er en byggesakstegning?"
        }
    else:
        for drawing_type in file["drawing_types"]:
            if drawing_type not in drawing_types:
                drawing_types.append(drawing_type)
        obj = {
            **obj,
            "drawing_type": drawing_types
        }
    for key in ["scale", "room_names", "cardinal_direction"]:
        if file.get(key):
            obj[key] = file[key]

    return json.dumps(obj)
    #         response.append(obj)

    # #for key in drawing_types:
    # #    response.append(key)
    # return response
