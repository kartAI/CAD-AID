from typing import List
from .data_structures import Metadata


def json_response_converter(detection_response: List[Metadata]) -> list:
    response = []
    for file in detection_response:
        if isinstance(file, Metadata):
            

            obj = {
                'filename': file.filename,
                'drawing_types': file.drawing_types,
            }

            if not file.drawing_types:
                obj['drawing_types'] = 'Er du sikker på at dette er en byggesakstegning?'

            else:
                if 'fasade' in file.drawing_types:
                    if file.cardinal_direction:
                        obj['cardinal_direction'] = file.cardinal_direction
                    else:
                        obj['cardinal_direction'] = 'Fasade mangler målestokk'

                if 'plantegning' in file.drawing_types:
                    if file.room_names:
                        obj['room_names'] = file.room_names
                    else:
                        obj['room_names'] = 'Plantegning mangler romnavn'

                if 'situasjonskart' in file.drawing_types and file.scale:
                    obj['scale'] = file.scale
            
            
            response.append(obj)
    
    return response

