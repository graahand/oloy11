"""
Utility Functions Module
=========================

This module provides utility functions for ML model management and image processing.

**PROJECT-SPECIFIC (You won't see this exact code elsewhere):**
- YOLO model management
- Image preprocessing for object detection

**RECURRING CONCEPTS:**
- Singleton pattern for expensive resources (models)
- Preprocessing pipelines
- Model management abstractions

**ALTERNATIVES:**
Model Management:
  - Load model on each request (simple but slow)
  - Singleton (used here - load once, reuse)
  - Model serving frameworks (TensorFlow Serving, TorchServe)
  - Separate model service (microservices architecture)
  
Image Processing:
  - PIL/Pillow
  - OpenCV (used here)
  - scikit-image
  - albumentations (advanced augmentation)
"""

from ultralytics import YOLO
from .config import get_settings
import cv2
import numpy as np

class ModelManager:
    """
    Singleton class for managing ML model lifecycle.
    
    **CRITICAL PATTERN - Singleton for expensive resources!**
    
    **Why Singleton?**
    Loading ML models is slow (can take seconds) and memory-intensive.
    Singleton ensures model is loaded only once and shared across all requests.
    
    **RECURRING:** You'll see singleton pattern for:
    - ML models
    - Database connections
    - Configuration objects
    - Cache managers
    
    **How Singleton works:**
    1. First instantiation: ModelManager() → loads model
    2. Subsequent calls: ModelManager() → returns existing instance
    3. Model stays in memory for the lifetime of the application
    
    **Alternative patterns:**
    - Dependency injection with lifecycle management
    - Global variable (simpler but less control)
    - Lazy loading (load on first use)
    
    **Memory consideration:**
    YOLO11n (~6MB): Small, can keep in memory
    Larger models (100MB+): Consider:
      - Loading on first request (lazy)
      - Unloading after inactivity
      - Using GPU for faster inference
      - Model quantization (reduce size)
    """
    
    # Class-level attributes (shared across all instances)
    _instance = None  # Singleton instance
    _model = None     # YOLO model
    
    def __new__(cls):
        """
        Control instance creation to implement Singleton pattern.
        
        **RECURRING:** Standard Singleton implementation in Python.
        
        __new__ is called before __init__ and controls object creation.
        
        How it works:
        1. Check if _instance already exists
        2. If not, create new instance using super().__new__()
        3. Initialize model
        4. Return instance (new or existing)
        """
        if cls._instance is None:
            # First time creation
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.initialize_model()
        return cls._instance
    
    def initialize_model(self):
        """
        Load the YOLO model (called only once).
        
        **How it works:**
        1. Get settings (model path)
        2. Check if model already loaded (_model is None)
        3. Load YOLO model from file
        4. Store in _model attribute
        
        **Loading time:**
        - YOLO11n: ~0.5-2 seconds
        - Larger models: ~5-10 seconds
        
        **Memory usage:**
        - YOLO11n: ~6MB
        - YOLO11x: ~200MB+
        
        **Error handling:**
        If model file not found, YOLO raises error.
        Consider adding try-except for production:
        try:
            self._model = YOLO(settings.MODEL_PATH)
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        """
        settings = get_settings()
        if self._model is None:
            # Log loading (helpful for debugging startup time)
            print(f"Loading model from {settings.MODEL_PATH}...")
            
            # Load YOLO model
            # This reads the .pt file and initializes the neural network
            self._model = YOLO(settings.MODEL_PATH)
    
    @property
    def model(self):
        """
        Property to access the loaded model.
        
        **RECURRING:** Using @property for controlled access.
        
        Usage:
        manager = ModelManager()
        results = manager.model(image)  # Access via property
        
        **Why @property?**
        - Cleaner syntax: manager.model vs manager.get_model()
        - Can add validation/logic later without changing usage
        - Read-only access (can't accidentally overwrite)
        """
        return self._model
    
    def predict(self, source, **kwargs):
        """
        Run inference on an image/video.
        
        **PROJECT-SPECIFIC:** This wraps YOLO's predict method.
        
        **Parameters:**
        source: Image/video to process
          - File path: "/path/to/image.jpg"
          - numpy array: cv2.imread() result
          - PIL Image
          - URL: "https://example.com/image.jpg"
        
        **kwargs: YOLO inference parameters
          - conf: Confidence threshold (0.0-1.0)
          - iou: IoU threshold for NMS (0.0-1.0)
          - max_det: Maximum detections per image
          - agnostic_nms: Class-agnostic NMS
          - save: Save results with annotations
          - verbose: Print inference details
        
        **Returns:**
        List of Results objects with:
          - boxes: Bounding boxes
          - names: Class names
          - conf: Confidence scores
          - to_json(): Convert to JSON
        
        **Example:**
        results = model_manager.predict(
            "image.jpg",
            conf=0.5,
            iou=0.7
        )
        
        **Performance:**
        - CPU: ~50-200ms per image (YOLO11n)
        - GPU: ~10-30ms per image (YOLO11n)
        
        **Related files:**
        - app/api/v1/inference.py: Uses this for image/video inference
        """
        return self._model(source, **kwargs)


# Create singleton instance
# This is loaded when the module is imported
# **RECURRING:** Module-level singleton instance
model_manager = ModelManager()


def preprocess_image(image: np.ndarray, target_size: tuple = None) -> np.ndarray:
    """
    Preprocess image for YOLO inference.
    
    **PROJECT-SPECIFIC:** Tailored for this API's needs.
    
    **RECURRING CONCEPT:** Preprocessing pipelines are common in ML APIs.
    
    **Current preprocessing:**
    - Resize to target size (if specified)
    - That's it! YOLO handles most preprocessing internally
    
    **Why minimal preprocessing?**
    YOLO models have built-in preprocessing:
    - Resizing to model input size
    - Normalization (pixel values 0-255 → 0-1)
    - Padding to maintain aspect ratio
    
    **When to add more preprocessing:**
    - Image quality enhancement (denoising, sharpening)
    - Color correction
    - Orientation correction
    - Letterboxing for aspect ratio preservation
    
    **Common preprocessing operations:**
    # Normalization
    image = image.astype(np.float32) / 255.0
    
    # Grayscale conversion
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Denoising
    image = cv2.fastNlMeansDenoisingColored(image)
    
    # Histogram equalization
    image = cv2.equalizeHist(image)
    
    **Alternatives:**
    - Albumentations (advanced augmentation library)
    - TorchVision transforms
    - PIL.ImageOps
    - scikit-image preprocessing
    
    **Related files:**
    - app/api/v1/inference.py: Uses this before inference
    
    Args:
        image: Input image as numpy array (from cv2.imread())
        target_size: Tuple (width, height) to resize to, or None
        
    Returns:
        np.ndarray: Preprocessed image
    """
    # Copy image to avoid modifying original
    # **Good practice:** Don't modify function arguments
    processed_image = image.copy()
    
    # Resize if target size specified
    if target_size:
        # cv2.resize expects (width, height)
        # target_size should be (width, height)
        processed_image = cv2.resize(processed_image, target_size)
        
        # **Note:** cv2.resize() uses bilinear interpolation by default
        # Alternatives:
        # cv2.INTER_NEAREST (fastest, blocky)
        # cv2.INTER_LINEAR (fast, smooth)
        # cv2.INTER_CUBIC (slower, smoother)
        # cv2.INTER_LANCZOS4 (slowest, best quality)
    
    # Add other preprocessing steps here as needed
    
    return processed_image
