from dataclasses import dataclass
from typing import List, Optional, Union
from pydantic import BaseModel
from shapely.geometry import Point, Polygon, box
import re

class ObjectDetectionResults(BaseModel):
    drawing_type: str
    bbox: List[float]
    probability: float


class RoomArea(BaseModel):
    room: str
    areal: str



class TextData(BaseModel):
    text: str
    probability: float
    bbox: List[int]

class FloorplanDetection(BaseModel):
    rooms_count: Optional[int] = None
    bathrooms_count: Optional[int] = None
    kitchen_count: Optional[int] = None

class OCRDetections(BaseModel):
    rooms: Optional[List[TextData]] = None 
    all_rooms: Optional[List[TextData]] = None
    bathrooms: Optional[List[TextData]] = None  
    kitchens: Optional[List[TextData]] = None
    arealer: Optional[List[RoomArea]] = None
    total_rooms: Optional[int] = None
    total_bathrooms: Optional[int] = None
    #BRA: Optional[str] = None
    #BRA: Optional[Union[str, TextData]] = None
    #BRA: Union[str, List[TextData]] = "default"
    BRA: Optional[TextData] = None
    
    #BYA: Optional[Union[str, TextData]] = None
    BYA: Optional[TextData] = None


    def count_rooms(self) -> int:
        return len(self.rooms)  

    def update_total_rooms(self):
        self.total_rooms = self.count_rooms()

    def count_bathrooms(self):
        return len(self.bathrooms)
    
    def update_bathroom_count(self):
        self.total_bathrooms = self.count_bathrooms()
    
    def update_BRA(self):
        arealer = []
        for areal in self.arealer:
            text = areal.areal
            match = re.search(r"([\d.]+)", text)
            if match:
                arealer.append(float(match.group(1)))
        
        self.BRA = sum(arealer)



class SegmentationResults(BaseModel):
    rooms_count: Optional[int] = None
    masks: Optional[List] = None 
    probability: Optional[List[float]] = None

    def count_rooms(self, results, bbox):
        x_min, y_min, x_max, y_max = bbox
        bounding_box = box(x_min, y_min, x_max, y_max)
        num_rooms = 0
        masks = []
        prob = []
        for result in results:
            confidence = result.boxes.conf.tolist()
            prob.extend(confidence)
            
            for mask in result.masks.xy:
                polygon = Polygon(mask)
                if bounding_box.contains(polygon):
                    num_rooms += 1
                    masks.append(mask.tolist())
                
        self.rooms_count=num_rooms
        self.masks = masks
        #self.probability = prob

class FileDetections(BaseModel):
    filename: str
    objdet: ObjectDetectionResults # contains category, bbox and conf
    ocr: OCRDetections
    segmentation: SegmentationResults