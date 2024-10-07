from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon
from typing import List, Optional
from enum import Enum



@dataclass
class TextInfo:
    text: str
    bbox: List[tuple]
    probability: float

@dataclass
class PolygonInfo:
    room: bool
    polygon: Polygon


class Metadata:
    def __init__(self,
    filename: str = None,
    drawing_types: Optional[List[str]] = None,
    bbox: Optional[List[float]] = None,
    confidence: Optional[List[float]] = None,
    cardinal_direction: Optional[List[str]] = None,
    scale: Optional[str] = None,
    room_names: Optional[List[str]]= None,
    store: Optional[dict] = None):

        self.filename = filename
        self.drawing_types = drawing_types
        self.bbox = bbox
        self.confidence = confidence
        self.cardinal_direction = cardinal_direction
        self.scale = scale
        self.room_names = room_names
        self.store = store or {}
    
    def convert_to_dict(self):
        return {
            'filename': self.filename,
            'drawing_types': self.drawing_types,
            'bbox': self.bbox,
            'confidence': self.confidence,
            'cardinal_direction': self.cardinal_direction,
            'scale': self.scale,
            'room_names': self.room_names,
            'store': self.store
        }

@dataclass
class ObjDetData:
    drawing_type: Optional[List[str]] = None
    bbox: Optional[List[float]] = None
    confidence: Optional[List[float]] = None

class DrawingType(Enum):
    """
    Enum class for drawing types.
    """
    # Define drawing types as class attributes
    FASADE = 'fasade'
    SITUASJONSKART = 'situasjonskart'
    PLANTEGNING = 'plantegning'
    SNITT = 'snitt'
