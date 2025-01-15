from dataclasses import dataclass, field
from typing import List
from shapely.geometry import Polygon
from typing import List, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel

@dataclass
class TextInfo:
    text: str
    bbox: List[tuple]
    probability: float

"""class DrawingInstance(BaseModel):
    drawing_type: str
    bbox: List[float]
    confidence: float
    cardinal_direction: Optional[str] = None
    scale: Optional[str] = None
    room_names: Optional[List[dict]] = None
    gnr_bnr: Optional[str] = None"""

@dataclass
class DrawingInstance:
    drawing_type: str
    bbox: List[float]
    confidence: float
    cardinal_direction: Optional[List[str]]= None
    #cardinal_direction = None
    scale: Optional[str] = None
    room_names: Optional[List[dict]] = None
    num_of_rooms: Optional[int] = None
    gnr_bnr: Optional[str] = None

    def convert_to_dict(self):
        return {
            'drawing_type': self.drawing_type,
            'bbox': self.bbox,
            'confidence': self.confidence,
            'cardinal_direction': self.cardinal_direction,
            'scale': self.scale,
            'room_names': self.room_names,
            'num_of_rooms': self.num_of_rooms,
            'gnr_bnr': self.gnr_bnr

        }

@dataclass
class Metadata:
    def __init__(self,
        filename: str = None,
        detections: List[DrawingInstance] = None,
        store: Optional[dict] = None
    ):
        self.filename = filename
        self.detections = detections or []
        self.store = store or {}
    
    def convert_to_dict(self):
        return {
            'filename': self.filename,
            'detections': [
                {
                    'drawing_type': det.drawing_type,
                    'bbox': det.bbox,
                    'confidence': det.confidence,
                    'cardinal_direction': det.cardinal_direction,
                    'scale': det.scale,
                    'room_names': det.room_names,
                    'num_of_rooms': det.num_of_rooms,
                    'gnr_bnr': det.gnr_bnr
                } for det in self.detections
            ],
            'store': self.store
        }


class DrawingType(Enum):
    """
    Enum class for drawing types.
    """
    # Define drawing types as class attributes
    FASADE = 'fasade'
    SITUASJONSKART = 'situasjonskart'
    PLANTEGNING = 'plantegning'
    SNITT = 'snitt'




@dataclass
class FeedbackData:
    filename: str
    user_response: bool
    original_detection: DrawingInstance
    corrected_detection: Optional[DrawingInstance] = None
    correction_type: Optional[str] = None  # e.g., "wrong_type", "missed_field", "wrong_field"
    correction_notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'filename': self.filename,
            'user_response': self.user_response,
            'original_detection': self.original_detection.convert_to_dict(),
            'corrected_detection': self.corrected_detection.convert_to_dict() if self.corrected_detection else None,
            'correction_type': self.correction_type,
            'correction_notes': self.correction_notes,
            'timestamp': self.timestamp.isoformat()
        }