from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon
from typing import List, Optional
from pydantic import BaseModel

@dataclass
class TextInfo:
    text: str
    bbox: List[tuple]
    probability: float

@dataclass
class PolygonInfo:
    room: bool
    polygon: Polygon


class Metadata(BaseModel):
    detection_id: Optional[str] = None
    filename: Optional[str] = None
    drawing_types: Optional[List[str]] = None
    bbox: Optional[List[List[float]]] = None
    confidence: Optional[List[float]] = None
    cardinal_direction: Optional[List[str]] = None
    scale: Optional[str] = None
    room_names: Optional[List[str]] = None
    room_count: Optional[int] = None
    rooms_with_label: Optional[List[str]] = None

    detection_message: Optional[str] = None
    #is_detection_correct: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True
    

@dataclass
class ObjDetData:
    drawing_type: Optional[List[str]] = None
    bbox: Optional[List[float]] = None
    confidence: Optional[List[float]] = None

class DrawingType:
    """
    Enum class for drawing types.
    """
    # Define drawing types as class attributes
    FASADE = 'fasade'
    SITUASJONSKART = 'situasjonskart'
    PLANTEGNING = 'plantegning'
    SNITT = 'snitt'
