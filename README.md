# Oloy11 - YOLOv11 Inference System

A FastAPI based backend for YOLOv11 object detection and segmentation.

## Features
- **Image Inference**: Upload image or provide URL.
- **Video Inference**: Upload video for frame-by-frame analysis.
- **Preprocessing**: Resize images before inference.
- **Model Configuration**: Tweak confidence, IoU, and max detections.
- **Authentication**: JWT based Login/Registration.
- **User History**: Track inference requests.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app/main.py
   ```
   Or use uvicorn directly:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Access Documentation:
   open http://localhost:8000/docs for Swagger UI.

## Usage

### Authentication
1. Register at `/api/v1/users/register`.
2. Login at `/api/v1/token` to get Access Token.
3. Use the token in Authorization header: `Bearer <token>` for endpoints (optional but required for history logging).

### Inference
- POST `/api/v1/predict/image`: Upload file or `image_url`. Tweak `conf`, `iou`, etc.
- POST `/api/v1/predict/video`: Upload video file.

## Testing
Run tests using pytest (requires creating tests in `tests/` folder based on `TEST_PLAN.md`).
```bash
pytest
```
