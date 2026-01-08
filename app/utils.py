from ultralytics import YOLO
from .config import get_settings
import cv2
import numpy as np

class ModelManager:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.initialize_model()
        return cls._instance

    def initialize_model(self):
        settings = get_settings()
        if self._model is None:
            # Singleton instance for class such as a Model loading
            print(f"Loading model from {settings.MODEL_PATH}...")
            self._model = YOLO(settings.MODEL_PATH)

    @property
    def model(self):
        return self._model
    
    def predict(self, source, **kwargs):
        """
        Run inference on the source provided.
        """
        return self._model(source, **kwargs)

model_manager = ModelManager()

def preprocess_image(image: np.ndarray, target_size: tuple = None) -> np.ndarray:
    """
    Image preprocessing pipeline.
    Resize and other yolo supported pre-processing steps.
    """
    processed_image = image.copy()
    if target_size:
        processed_image = cv2.resize(processed_image, target_size)
    
    # Add other preprocessing as needed
    return processed_image
