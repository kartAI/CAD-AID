import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Optional
from shapely.geometry import Point, Polygon
from utils.regex_patterns import scale_pattern, cardinal_direction_pattern, room_pattern
from utils.text_manager import TextDetection
from utils.models_manager import ObjectDetection, Segmentation
from utils.data_structures import Detection, TextInfo, PolygonInfo
from utils.logger import cadaid_logger
import base64
import cv2
import numpy as np

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
    def __init__(self):
        self.model = ObjectDetection()
        self.results = None
        self.detection = None
        self.prediction_image = None
        self.confidences = []
        self.logger = cadaid_logger(__name__)

    def run_detection(self, image_path):
        # Run object detection on the given image
        #self.results = self.model.predictions(image_path)
        # self.results = self.model.predictions(self.model.prediction_image)
        #self.results = self.model(image_path)
        self.prediction_image = image_path
        self.results = self.model.predictions(image_path)
        self.detection = self._create_detection()
    
    def _get_drawing_type(self) -> List[str]:
        """
        Helper method to extract predicted class labels from the results.
        """
        drawing_types = []
        for result in self.results:
            boxes = result.boxes
            for box, cls, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
                class_name = self.model.names[int(cls)]
                self.logger.info(f"Detected: {class_name} with confidence {conf:.2f}")
                if conf >= self.model.model_conf:
                    drawing_types.append(class_name)
                    self.confidences.append(conf.item())
                else:
                    self.logger.info(f"Detection below threshold: {class_name} with confidence {conf:.2f}")
        self.logger.info(f"Final drawing types: {drawing_types}")
        return drawing_types
    
    def _create_detection(self) -> Detection:
        """
        Stores the detected drawing types in a Detection object.
        """
        drawing_types = self._get_drawing_type()
        return Detection(drawing_type=drawing_types)

    def get_detection(self):
        return self.detection.drawing_type, self.confidences

class SegmentationHandler:
    def __init__(self):
        self.model = Segmentation()
        self.seg_results = None
        self.rooms_found = []
        self.logger = cadaid_logger(__name__)
        self.prediction_image = None
        
    def set_prediction_image(self, image_path):
        self.prediction_image = image_path

    def run_segmentation(self, image_path=None):
        if image_path is None:
            image_path = self.prediction_image
        if image_path is None:
            raise ValueError("No image path provided for segmentation.")
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

    def visualize_segmentation(self, filename):
        if not self.seg_results:
            self.logger.warning("No segmentation results available for visualization.")
            return None

        image = cv2.imread(filename)
        if image is None:
            self.logger.warning(f"Failed to read image from {filename}")
            return None

        for i, room in enumerate(self.rooms_found):
            color = (0, 255, 0) if room.room else (0, 0, 255)
            points = np.array(room.polygon.exterior.coords, np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.polylines(image, [points], True, color, 2)

        # Add text for room counts
        true_count, false_count = self.count_rooms()
        cv2.putText(image, f"Rooms with labels: {true_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(image, f"Rooms without labels: {false_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Convert the image to base64
        _, buffer = cv2.imencode('.png', image)
        base64_image = base64.b64encode(buffer).decode('utf-8')

        return base64_image

class TextHandler:
    def __init__(self, ocr: TextDetection):
        # Initialize text handler with OCR model
        self.ocr = ocr

    def get_cardinal_direction(self, patterns: List[str]) -> Optional[str]:
        text_infos = self.ocr.get_target_text(patterns)
        return text_infos[0].text if text_infos else None

    def get_scale(self, patterns: List[str]) -> Optional[str]:
        text_infos = self.ocr.get_target_text(patterns)
        return text_infos[0].text if text_infos else None

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
        self.object_detection = ObjectDetectionHandler()
        self.segmentation_handler = SegmentationHandler()
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
        self.detection.drawing_type, self.detection.confidences = self.object_detection.get_detection()

        if not self.detection.drawing_type:
            self.logger.warning("No drawing type available.")
            return

        
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
                self.segmentation_handler.run_segmentation(self.prediction_image_path)
                self.segmentation_results = self.segmentation_handler.find_text_segments(room_text_infos)

                true_count, false_count = self.segmentation_handler.count_rooms()
                self.logger.info(f"Number of rooms with room label: {true_count}")
                self.logger.info(f"Number of rooms without room label: {false_count}")

        self.logger.info("Detection and segmentation completed.")

    def get_segmentation_results(self):
        return self.segmentation_results

    def visualize_detection(self, filename):
        if not self.prediction_image_path:
            self.logger.warning("No prediction image path set for visualization.")
            return None

        image = cv2.imread(self.prediction_image_path)
        if image is None:
            self.logger.warning(f"Failed to read image from {self.prediction_image_path}")
            return None

        for dtype, confidence in zip(self.detection.drawing_type, self.detection.confidences):
            cv2.putText(image, f"{dtype}: {confidence:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if self.detection.cardinal_direction:
            cv2.putText(image, f"Cardinal Direction: {self.detection.cardinal_direction}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        if self.detection.scale:
            cv2.putText(image, f"Scale: {self.detection.scale}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        if self.detection.room_names:
            for i, room in enumerate(self.detection.room_names):
                cv2.putText(image, room, (10, 150 + i*40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Convert the image to base64
        _, buffer = cv2.imencode('.png', image)
        base64_image = base64.b64encode(buffer).decode('utf-8')

        return base64_image


            


