import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List
from shapely.geometry import Point, Polygon
from utils.regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from utils.text_manager import TextDetection
from utils.models_manager import ObjectDetection
from utils.models_manager import Segmentation
from utils.data_structures import Detection, TextInfo, PolygonInfo
from utils.logger import cadaid_logger

class DrawingType:
    """
    Enum class for drawing types.
    """
    FASADE = 'fasade'
    SITUASJONSKART = 'situasjonskart'
    PLANTEGNING = 'plantegning'
    SNITT = 'snitt'


class ObjectDetectionHandler:
    """
    Class for handling object detection.
    """
    def __init__(self, model: ObjectDetection):
        self.model = model
        self.results = self.model.predictions(self.model.prediction_image)
        self.detection = self._create_detection()
    
    def _get_drawing_type(self) -> List[str]:
        """
        Helper method to extract predicted class labels from the results.
        """
        drawing_types = []
        for result in self.results:
            boxes = result.boxes  
            class_indices = boxes.cls  
            class_names = [result.names[int(cls)] for cls in class_indices]  
            drawing_types.extend(class_names)  
        return drawing_types
    
    def _create_detection(self) -> Detection:
        """
        Stores the detected drawing types in a Detection object.
        """
        drawing_types = self._get_drawing_type()
        return Detection(drawing_type=drawing_types)

    def get_detection(self) -> Detection:
        return self.detection.drawing_type

class SegmentationHandler:
    def __init__(self, model: Segmentation):
        self.model = model
        self.seg_results = self.model.predictions(self.model.prediction_image)
        self.rooms_found = []
        
    
    def find_text_segments(self, target_words: List[TextInfo]) -> List[PolygonInfo]:
        """
        Checks if the text is inside the polygon/segmented room and returns a list of PolygonInfo objects.
        """
        rooms_found = []
        for r in self.seg_results:
            masks = r.masks.xy
            for mask in masks:
                polygon = Polygon(mask)
                is_name_found = False
                for i in target_words:
                    text_bboxes = i.bbox
                    text_x_min, text_y_min = text_bboxes[0]
                    text_x_max, text_y_max = text_bboxes[2]
                    cx = (text_x_min + text_x_max)/2
                    cy = (text_y_min + text_y_max)/2
                    centroid = Point(cx, cy)
                    is_inside = polygon.contains(centroid)
                    if is_inside:
                        is_name_found = True
                        break
                
                
                rooms_polygons = PolygonInfo(room=is_name_found, polygon=polygon)
                rooms_found.append(rooms_polygons)

        self.rooms_found = rooms_found
        
        return self.rooms_found
    
    def count_rooms(self):
        true_count = sum(1 for room in self.rooms_found if room.room)
        false_count = sum(1 for room in self.rooms_found if not room.room)
        return true_count, false_count
	
class TextHandler:
    def __init__(self, ocr: TextDetection):
        self.ocr = ocr
      
    def get_cardinal_direction(self, patterns: List[str]) -> List[str]:
        """
        Args:
            patterns: List of patterns to search for in the detected text.
        returns:
            List of cardinal directions found in the detected text.
        """
        #self.detection.cardinal_direction = [text.text for text in self.ocr.get_target_text(patterns)]
        return [text.text for text in self.ocr.get_target_text(patterns)]
        
    
    def get_scale(self, patterns: List[str]) -> List[str]:
        return [text.text for text in self.ocr.get_target_text(patterns)]
        
    
    def get_room_names(self, patterns: List[str]) -> List[TextInfo]:
        """
        Args:
            patterns: List of room patterns to search for in the detected text.
        Returns:
            List of TextInfo objects containing the room
        """
        return self.ocr.get_target_text(patterns)
        
    
    

class DetectionHandler:
    def __init__(self):
        self.logger = cadaid_logger(__name__)
        self.detection = Detection()
        self.object_detection = ObjectDetectionHandler(ObjectDetection())
        self.segmentation_handler = SegmentationHandler(Segmentation())

    
    def check_and_execute(self):
        self.logger.info("Starting object detection...")
        self.detection.drawing_type = self.object_detection.get_detection()
        # object_detection = ObjectDetectionHandler(ObjectDetection())
        
        # self.detection.drawing_type = object_detection.get_detection()
    
       
        if not self.detection.drawing_type:
            self.logger.warning("No drawing type available.")
            return  # No drawing type available

        
        # Define actions based on drawing types
        for dtype in self.detection.drawing_type:
            text_extractor = TextHandler(TextDetection())
            self.logger.info(f"Processing drawing type: {dtype}")

            if dtype == DrawingType.FASADE:
                # Find cardinal direction
                cardinal_direction = text_extractor.get_cardinal_direction([cardinal_direction_pattern])
                self.detection.cardinal_direction = cardinal_direction

                #self.detection.cardinal_direction = [text.text for text in perform_ocr.get_target_text([cardinal_direction_pattern])]
                self.logger.debug(f"Found cardinal direction: {self.detection.cardinal_direction}")

            elif dtype == DrawingType.SITUASJONSKART:
                # Find scale
                scale = text_extractor.get_scale([scale_pattern])
                self.detection.scale = scale
                self.logger.debug(f"Found scale: {self.detection.scale}")

            elif dtype == DrawingType.PLANTEGNING:
                room_text_infos = text_extractor.get_room_names([room_pattern])
                self.detection.room_names = [text.text for text in room_text_infos]
                self.logger.debug(f"Found room names: {self.detection.room_names}")

                
                #segmentation = SegmentationHandler(Segmentation())
                self.logger.info("Performing segmentation...")
                self.segmentation_handler.find_text_segments(room_text_infos)

                true_count, false_count = self.segmentation_handler.count_rooms()
                self.logger.info(f"Number of rooms with room label: {true_count}")
                self.logger.info(f"Number of rooms without room label: {false_count}")


        
                self.logger.info("Segmentation completed.")


            


