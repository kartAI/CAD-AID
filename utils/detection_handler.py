import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Optional
from shapely.geometry import Point, Polygon
from utils.regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from utils.text_manager import TextDetection
from utils.models_manager import ObjectDetection
from utils.models_manager import Segmentation
from utils.data_structures import Detection, TextInfo, PolygonInfo
from utils.logger import cadaid_logger

# Import necessary modules and classes

class DrawingType:
    """
    Enum class for drawing types.
    """
    # Define drawing types as class attributes
    FASADE = 'fasade'
    SITUASJONSKART = 'situasjonskart'
    PLANTEGNING = 'plantegning'
    SNITT = 'snitt'


class ObjectDetectionHandler:
    """
    Class for handling object detection.
    """
    def __init__(self, model: ObjectDetection):
        # Initialize object detection handler with model
        self.model = model
        # self.results = self.model.predictions(self.model.prediction_image)
        self.results = None
        self.detection = None
    
    def run_detection(self, image_path):
        # Run object detection on the given image
        self.results = self.model.predictions(image_path)
        # self.results = self.model.predictions(self.model.prediction_image)
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
        # Initialize segmentation handler with model and logger
        self.model = model
        # self.results = self.model.predictions(self.model.prediction_image)
        self.seg_results = None
        self.rooms_found = []
        self.logger = cadaid_logger(__name__)  # Legg til denne linjen

    def run_segmentation(self, image_path):
        # Run segmentation on the given image
        self.seg_results = list(self.model.predictions(image_path))  # Konverter til liste

    def find_text_segments(self, target_words: List[TextInfo]) -> List[PolygonInfo]:
        """
        Checks if the text is inside the polygon/segmented room and returns a list of PolygonInfo objects.
        """
        rooms_found = []
        if not self.seg_results:
            self.logger.warning("No segmentation results found.")
            return rooms_found

        for r in self.seg_results:
            if not hasattr(r, 'masks') or r.masks is None:
                self.logger.warning("No masks found in segmentation results.")
                continue

            masks = r.masks.xy
            if not masks:
                self.logger.warning("Masks are empty.")
                continue

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

    def count_rooms(self) -> tuple[int, int]:
        true_count = sum(1 for room in self.rooms_found if room.room)
        false_count = sum(1 for room in self.rooms_found if not room.room)
        return true_count, false_count
	
class TextHandler:
    def __init__(self, ocr: TextDetection):
        # Initialize text handler with OCR model
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
        # Initialize detection handler with necessary components
        self.logger = cadaid_logger(__name__)
        self.detection = Detection()
        self.object_detection = ObjectDetectionHandler(ObjectDetection())
        self.segmentation_handler = SegmentationHandler(Segmentation())
        # self.segmentation_results = None
        self.prediction_image_path = None

    def set_prediction_image(self, image_path):
        # Set the path for the prediction image
        self.prediction_image_path = image_path

    def check_and_execute(self):
        # Main method to run detection and process results
        if not self.prediction_image_path:
            raise ValueError("Prediction image path is not set")

        self.logger.info("Starting object detection...")
        self.object_detection.run_detection(self.prediction_image_path)
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
                self.segmentation_results = self.segmentation_handler.find_text_segments(room_text_infos)

                true_count, false_count = self.segmentation_handler.count_rooms()
                self.logger.info(f"Number of rooms with room label: {true_count}")
                self.logger.info(f"Number of rooms without room label: {false_count}")


        
                self.logger.info("Segmentation completed.")

    
    def get_segmentation_results(self):
        return self.segmentation_results


            


