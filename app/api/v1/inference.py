"""
Inference Routes Module
=======================

This module handles ML inference endpoints for YOLO object detection.

**PROJECT-SPECIFIC (This exact code won't appear in other projects):**
- YOLO-specific inference logic
- Image and video processing for object detection

**RECURRING CONCEPTS:**
- File upload handling
- URL-based input
- Preprocessing pipelines
- Error handling for ML operations
- Optional authentication

**ALTERNATIVES:**
- Separate microservice for inference
- Batch processing endpoints
- WebSocket for real-time inference
- Background tasks (Celery, RQ)
- Cloud ML services (AWS SageMaker, Google AI Platform)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from typing import Optional
from app.utils import model_manager, preprocess_image
from app.config import get_settings
from app.security import get_current_user
from app.database import get_db
from app.models.history import History
from app.models.user import User
from sqlalchemy.orm import Session
import httpx
import shutil
from pathlib import Path
import cv2
import numpy as np
import uuid
import json

# ===== ROUTER =====
router = APIRouter()
settings = get_settings()


@router.post("/predict/image")
async def predict_image(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    conf: float = Form(0.25),
    iou: float = Form(0.7),
    max_det: int = Form(300),
    agnostic_nms: bool = Form(False),
    resize_w: Optional[int] = Form(None),
    resize_h: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Run YOLO object detection on a single image.
    
    **PROJECT-SPECIFIC:** YOLO inference endpoint.
    
    **RECURRING CONCEPTS:**
    - File upload handling
    - URL-based input
    - Optional authentication
    - Parameter validation
    
    **How it works:**
    1. Validate input (either file or URL required)
    2. Download/save image to disk
    3. Optional: Preprocess image (resize)
    4. Run YOLO inference
    5. Parse results to JSON
    6. Log to history (if authenticated)
    7. Return results
    
    **Input methods:**
    Method 1 - File Upload:
      POST /api/v1/predict/image
      Content-Type: multipart/form-data
      
      file: <image file>
      conf: 0.5
      
    Method 2 - Image URL:
      POST /api/v1/predict/image
      Content-Type: application/x-www-form-urlencoded
      
      image_url: https://example.com/image.jpg
      conf: 0.5
    
    **Parameters:**
    - file: Image file upload (jpg, png, etc.)
    - image_url: Alternative to file upload
    - conf: Confidence threshold (0.0-1.0)
    - iou: IoU threshold for NMS (0.0-1.0)
    - max_det: Maximum detections per image
    - agnostic_nms: Class-agnostic NMS
    - resize_w: Optional resize width
    - resize_h: Optional resize height
    
    **Response example:**
    {
        "file_path": "/uploads/abc123.jpg",
        "results": [
            {
                "name": "person",
                "class": 0,
                "confidence": 0.95,
                "box": {"x1": 100, "y1": 200, "x2": 150, "y2": 300}
            }
        ]
    }
    
    **Authentication:**
    Optional - endpoint works with or without auth.
    If authenticated, action is logged to history.
    
    **Security considerations:**
    - Validate file types (prevent uploading executables)
    - Limit file size (prevent DoS)
    - Rate limiting (prevent abuse)
    - Virus scanning for uploaded files
    
    **Improvements:**
    - Add file size validation
    - Better file type validation (magic numbers)
    - Return annotated image
    - Caching for repeated URLs
    - Async file I/O
    
    **Related files:**
    - app/utils.py: model_manager, preprocess_image
    - app/models/history.py: History logging
    
    Args:
        file: Optional uploaded image file
        image_url: Optional image URL
        conf: Confidence threshold
        iou: IoU threshold
        max_det: Maximum detections
        agnostic_nms: Class-agnostic NMS
        resize_w: Resize width
        resize_h: Resize height
        db: Database session
        current_user: Authenticated user (optional)
        
    Returns:
        dict: Detection results with file path
        
    Raises:
        HTTPException: 400 if no input, 400 if invalid image, 500 on error
    """
    # ===== 1. VALIDATION =====
    # Ensure at least one input method is provided
    if not file and not image_url:
        raise HTTPException(
            status_code=400, 
            detail="Either file or image_url is required"
        )
    
    # ===== 2. FILE HANDLING =====
    # Generate unique filename using UUID
    # **RECURRING:** UUID for unique filenames prevents collisions
    temp_filename = f"{uuid.uuid4()}"
    file_path = settings.UPLOAD_DIR / f"{temp_filename}.jpg"
    
    try:
        if file:
            # ===== FILE UPLOAD PATH =====
            # Validate file extension
            # **Security note:** Extension check is weak, use magic numbers in production
            # Magic numbers: Check actual file content, not just extension
            file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
            
            # Supported YOLO image formats
            supported_formats = [
                "bmp", "dng", "jpeg", "mpo", "png", 
                "tif", "tiff", "webp", "heic", "jpg"
            ]
            
            if file_ext not in supported_formats:
                # Just a warning here, could make this stricter
                # **Alternative:** raise HTTPException(400, "Unsupported format")
                pass 
            
            # Save uploaded file to disk
            # **Note:** FastAPI file uploads are in memory by default
            # For large files, consider streaming directly to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
                
        else:
            # ===== URL DOWNLOAD PATH =====
            # Download image from URL
            # **RECURRING:** httpx for async HTTP requests
            # **Alternative:** requests (sync), aiohttp (async)
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url)
                
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail="Could not retrieve image from URL"
                    )
                
                # Save downloaded content
                with open(file_path, "wb") as f:
                    f.write(resp.content)
        
        # ===== 3. PREPROCESSING =====
        # Read image with OpenCV
        img = cv2.imread(str(file_path))
        
        if img is None:
            # imread returns None if file is not a valid image
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Optional resize
        if resize_w and resize_h:
            img = preprocess_image(img, target_size=(resize_w, resize_h))
            # After resize, we pass numpy array to model
            # Could save resized image back to disk if needed

        # ===== 4. INFERENCE =====
        # Run YOLO model on image
        # **Note:** Can pass numpy array or file path to YOLO
        results = model_manager.predict(
            source=img,              # Numpy array (preprocessed) or file path
            conf=conf,               # Confidence threshold
            iou=iou,                 # IoU threshold for NMS
            max_det=max_det,         # Max detections per image
            agnostic_nms=agnostic_nms,  # Class-agnostic NMS
            save=False               # Don't save annotated images
        )
        
        # ===== 5. RESULT PROCESSING =====
        # Convert YOLO results to JSON format
        result_json = []
        for result in results:
            # result.to_json() returns JSON string
            json_str = result.to_json()
            result_js = json.loads(json_str)  # Parse JSON string to dict
            result_json.extend(result_js)  # Add to results list

        # ===== 6. HISTORY LOGGING =====
        # Log action if user is authenticated
        if current_user:
            try:
                history = History(
                    user_id=current_user.id,
                    action_type="image_inference",
                    resource_path=str(file_path),
                    result_summary=result_json  # Store JSON results
                )
                db.add(history)
                db.commit()
            except Exception as e:
                # Don't fail the request if logging fails
                # Just log the error
                print(f"Failed to log history: {e}")
                # **Production:** Use proper logging
                # import logging
                # logger.error(f"Failed to log history: {e}")

        # ===== 7. RETURN RESULTS =====
        return {
            "file_path": str(file_path),  # Where file is stored
            "results": result_json        # Detection results
        }
        
    except Exception as e:
        # Catch-all error handler
        # **Production:** More specific error handling
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/video")
async def predict_video(
    file: UploadFile = File(...),
    conf: float = Form(0.25),
    iou: float = Form(0.7),
    max_det: int = Form(300),
    agnostic_nms: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Run YOLO object detection on video frames.
    
    **PROJECT-SPECIFIC:** Video processing for YOLO inference.
    
    **RECURRING CONCEPTS:**
    - Video processing with OpenCV
    - Frame-by-frame inference
    - Result aggregation
    - Progress tracking
    
    **How it works:**
    1. Validate video format
    2. Save uploaded video file
    3. Open video with OpenCV
    4. Loop through frames
    5. Run inference on each frame
    6. Aggregate results
    7. Log to history
    8. Return summary
    
    **Request example:**
    POST /api/v1/predict/video
    Content-Type: multipart/form-data
    
    file: <video file>
    conf: 0.5
    
    **Response example:**
    {
        "video_path": "/uploads/abc123.mp4",
        "total_frames": 300,
        "frame_analysis": [
            {"frame": 10, "detections": 3},
            {"frame": 25, "detections": 2}
        ]
    }
    
    **Performance considerations:**
    - Video processing is SLOW (30fps video = 30 inferences/second)
    - Consider: Skip frames, reduce resolution, use GPU
    - For long videos, use background tasks (Celery)
    
    **Optimizations:**
    # Process every Nth frame
    if frame_count % 5 == 0:  # Process every 5th frame
        results = model_manager.predict(frame)
    
    # Reduce resolution
    small_frame = cv2.resize(frame, (640, 480))
    
    # Use GPU (automatically used if available)
    # Just ensure CUDA is installed and YOLO is GPU-enabled
    
    **Alternatives:**
    - Background task processing (Celery, RQ)
    - Streaming response (yield results as processed)
    - WebSocket for real-time progress
    - Cloud video processing (AWS MediaConvert, Google Video AI)
    
    **Related files:**
    - app/utils.py: model_manager
    - app/models/history.py: History logging
    
    Args:
        file: Uploaded video file
        conf: Confidence threshold
        iou: IoU threshold
        max_det: Maximum detections
        agnostic_nms: Class-agnostic NMS
        db: Database session
        current_user: Authenticated user (optional)
        
    Returns:
        dict: Video analysis summary
        
    Raises:
        HTTPException: 400 if unsupported format or can't open video, 500 on error
    """
    # ===== 1. VALIDATION =====
    # Validate video extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    # Supported video formats (YOLO/OpenCV compatible)
    supported_formats = ["asf", "mp4", "mpeg", "mov", "mkv", "avi", "webm"]
    
    if file_ext not in supported_formats:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported video format"
        )

    # ===== 2. FILE HANDLING =====
    # Save video with original extension
    temp_filename = f"{uuid.uuid4()}.{file_ext}"
    video_path = settings.UPLOAD_DIR / temp_filename
    
    try:
        # Save uploaded video to disk
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # ===== 3. VIDEO PROCESSING =====
        # Open video with OpenCV
        # **RECURRING:** cv2.VideoCapture for video processing
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            # Video file is invalid or can't be opened
            raise HTTPException(
                status_code=400, 
                detail="Could not open video"
            )

        # Initialize counters
        frame_count = 0
        results_summary = []
        
        # ===== 4. FRAME-BY-FRAME PROCESSING =====
        # Loop through all frames
        # **Note:** This is synchronous and blocking!
        # For production, use background tasks or async processing
        while cap.isOpened():
            # Read next frame
            success, frame = cap.read()
            
            if success:
                frame_count += 1
                
                # Run inference on this frame
                # **Performance note:** This runs on EVERY frame!
                # For optimization, process every Nth frame
                results = model_manager.predict(
                    source=frame,
                    conf=conf,
                    iou=iou,
                    max_det=max_det,
                    agnostic_nms=agnostic_nms,
                    save=False,
                    verbose=False  # Suppress YOLO output for each frame
                )
                
                # ===== 5. RESULT AGGREGATION =====
                # Count detections in this frame
                # results[0].boxes contains all detected objects
                det_count = len(results[0].boxes) if results and results[0].boxes else 0
                
                if det_count > 0:
                    # Only log frames with detections to save space
                    # **Alternative:** Log all frames for complete analysis
                    frame_summary = {
                        "frame": frame_count,
                        "detections": det_count
                    }
                    results_summary.append(frame_summary)
                
                # **Optional progress logging:**
                # if frame_count % 100 == 0:
                #     print(f"Processed {frame_count} frames...")
                
            else:
                # No more frames, exit loop
                break
                
        # Release video capture
        # **Important:** Always release to free resources
        cap.release()
        
        # ===== 6. HISTORY LOGGING =====
        # Log video processing if user is authenticated
        if current_user:
            try:
                history = History(
                    user_id=current_user.id,
                    action_type="video_inference",
                    resource_path=str(video_path),
                    result_summary=results_summary  # Summary of frames with detections
                )
                db.add(history)
                db.commit()
            except Exception as e:
                # Don't fail request if logging fails
                print(f"Failed to log history: {e}")

        # ===== 7. RETURN RESULTS =====
        return {
            "video_path": str(video_path),
            "total_frames": frame_count,
            "frame_analysis": results_summary
        }
        
    except Exception as e:
        # Catch-all error handler
        # **Production:** More specific error handling
        raise HTTPException(status_code=500, detail=str(e))
