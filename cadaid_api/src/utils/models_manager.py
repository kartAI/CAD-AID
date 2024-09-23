import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ultralytics import YOLO
from config import Config


"""
Core functionality of the models wich includes training and predictions

"""

class ModelsManager:
    def __init__(self, 
                 model_path: str, 
                 model_conf: float, 
                
                 ):
        """
        Base class for managing models, including training and predictions.

        :param model_name: Name of the model.
        :param model_path: Path to the model file.
        :param model_conf: Confidence threshold for predictions.
        :param data_yaml: Path to the data YAML file.
        """

        self._config = Config()
        self.model_path = model_path
        self.model_conf = model_conf
      
        #self.prediction_image = self._config.PREDICTION_IMAGE_PATH
        self.prediction_image = None

        self.model = YOLO(self.model_path)
       


    def predictions(self, image):
        return self.model(image,
                          save=False, 
                          stream=True, 
                          visualize=False, 
                          conf=self.model_conf)
 
    

# Get model name and confidence from config
class ObjectDetection(ModelsManager):
    def __init__(self):
        self._config = Config()
        super().__init__(
                         model_path=self._config.OBJECT_DETECTION_MODEL_PATH,
                         model_conf=self._config.OBJECT_DETECTION_CONFIDENCE,
                        
                        )
        self.names = self.model.names  # Add this line to include the names attribute

    def predictions(self, image_path):
        return self.model(image_path,
                          save=False, 
                          stream=True, 
                          visualize=False, 
                          conf=self.model_conf)
                         
class Segmentation(ModelsManager):
    def __init__(self):
        self._config = Config()
        super().__init__(
                         model_path=self._config.SEGMENTATION_MODEL_PATH,
                         model_conf=self._config.SEGMENTATION_CONFIDENCE,
                         
                         )
    
    def predictions(self, image_path):
        return self.model(image_path,
                          save=False, 
                          stream=True, 
                          visualize=False, 
                          conf=self.model_conf)

