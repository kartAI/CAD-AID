from typing import List,Optional
from pydantic import BaseModel

class Metadata(BaseModel):
    filename: str = None
    drawing_types: Optional[List[str]] = None
    bbox: Optional[List[float]] = None
    confidence: Optional[List[float]] = None
    cardinal_direction: Optional[List[str]] = None
    scale: Optional[str] = None
    room_names: Optional[List[str]]= None
    total_rooms_detected: Optional[int] = None
    store: Optional[dict] = None