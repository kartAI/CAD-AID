from dataclasses import dataclass

from shapely.geometry import Polygon
from typing import List, Optional

@dataclass
class TextInfo:
    text: str
    bbox: List[tuple]
    probability: float

@dataclass
class PolygonInfo:
    room: bool
    polygon: Polygon

@dataclass
class Detection:
    drawing_type: Optional[List[str]] = None
    cardinal_direction: Optional[List[str]] = None
    scale: Optional[str] = None
    room_names: Optional[List[str]]= None
