# Design Document - Oloy11

## 1. Class Diagram

```mermaid
classDiagram
    class Config {
        +str MODEL_PATH
        +str UPLOAD_DIR
        +str DB_URL
        +get_settings()
    }

    class ModelManager {
        -static _instance: ModelManager
        -model: YOLO
        +__new__(cls)
        +get_model(model_name: str) : YOLO
        +predict(source, conf, iou, max_det, agnostic_nms) : Results
    }

    class ImagePreprocessor {
        +resize(image, size)
        +normalize(image)
        +process(image_path) : processed_image
    }

    class VideoProcessor {
        +process_video(video_path, model_settings) : json_results
        -extract_frames(video_path)
    }

    class User {
        +int id
        +str username
        +str email
        +str hashed_password
    }

    class UserHistory {
        +int id
        +int user_id
        +str action_type
        +str resource_path
        +datetime timestamp
        +json result_summary
    }

    class AuthHandler {
        +get_password_hash(password)
        +verify_password(plain, hashed)
        +create_access_token(data)
    }

    Config <|-- ModelManager
    ModelManager --> ImagePreprocessor : uses
    ModelManager --> VideoProcessor : uses
```

## 2. Pseudocode

### Singleton Model Loader
```python
class ModelManager:
    _instance = None
    _model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self, model_name="yolo11n.pt"):
        if self._model is None:
            self._model = YOLO(model_name)
        return self._model
    
    def run_inference(self, source, **kwargs):
        model = self.load_model()
        return model(source, **kwargs)
```

### API Endpoints Logic

#### Image Inference
```python
def predict_image(file, settings):
    # 1. Save uploaded file/Validate URL
    # 2. Preprocess image (ImagePreprocessor)
    # 3. Get Model (ModelManager)
    # 4. Run Inference
    # 5. Process Results (to_json)
    # 6. Save User History
    return results_json
```

#### Video Inference
```python
def predict_video(file, settings):
    # 1. Save video file 
    # 2. Open Video Capture
    # 3. Loop frames
        # Run Inference per frame
        # Accumulate results
    # 4. Save processed video (optional) or return metadata
    # 5. Save User History
    return analysis_summary
```

#### Auth
```python
def login(username, password):
    user = db.get_user(username)
    if verify_password(password, user.password):
        return token
    raise Unauthorized
```
