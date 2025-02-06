
from pydantic import BaseModel
from typing import List

class Detection(BaseModel):
    drawing_type: str

class FileDetections(BaseModel):
    filename: str
    detections: List[Detection]