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
    Inference on Image (Upload or URL).
    Includes preprocessing (resize) and model argument tweaking.
    """
    # 1. Validation: Either file or url
    if not file and not image_url:
        raise HTTPException(status_code=400, detail="Either file or image_url is required")
    
    # 2. Get Image Path / Content
    temp_filename = f"{uuid.uuid4()}"
    file_path = settings.UPLOAD_DIR / f"{temp_filename}.jpg"
    
    try:
        if file:
            # Basic extension check (Can be improved with magic numbers)
            file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
            if file_ext not in ["bmp", "dng", "jpeg", "mpo", "png", "tif", "tiff", "webp", "heic", "jpg"]:
                 # Just a warning or strict check? Prompt says "supported image formats".
                 pass 
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            # Download from URL
            async with httpx.AsyncClient() as client:
                resp = await client.get(image_url)
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail="Could not retrieve image from URL")
                with open(file_path, "wb") as f:
                    f.write(resp.content)
        
        # 3. Preprocessing
        # Read image with cv2 to preprocess
        img = cv2.imread(str(file_path))
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        if resize_w and resize_h:
            img = preprocess_image(img, target_size=(resize_w, resize_h))
            # If resized, we can save it back or just use the numpy array.
            # model_manager.predict accepts numpy array.

        # 4. Inference
        results = model_manager.predict(
            source=img, # Passing numpy array (preprocessed) or original file path could also work if no resize
            conf=conf,
            iou=iou,
            max_det=max_det,
            agnostic_nms=agnostic_nms,
            save=False 
        )
        
        # 5. Process Result
        result_json = []
        for result in results:
            json_str = result.tojson()
            result_js = json.loads(json_str) 
            result_json.extend(result_js)

        if current_user:
            try:
                history = History(
                    user_id=current_user.id,
                    action_type="image_inference",
                    resource_path=str(file_path),
                    result_summary=result_json 
                )
                db.add(history)
                db.commit()
            except Exception as e:
                print(f"Failed to log history: {e}")

        return {
            "file_path": str(file_path), # Returning path for reference/debug
            "results": result_json
        }
    except Exception as e:
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
    Inference on Video.
    """
    # Validate extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ["asf", "mp4", "mpeg", "mov", "mkv", "avi", "webm"]:
         raise HTTPException(status_code=400, detail="Unsupported video format")

    temp_filename = f"{uuid.uuid4()}.{file_ext}"
    video_path = settings.UPLOAD_DIR / temp_filename
    
    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process Video (Based on official snippet)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video")

        frame_count = 0
        results_summary = []
        
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                frame_count += 1
                # Run inference per frame
                results = model_manager.predict(
                    source=frame,
                    conf=conf,
                    iou=iou,
                    max_det=max_det,
                    agnostic_nms=agnostic_nms,
                    save=False,
                    verbose=False
                )
                
                # Aggregate results
                # Simplify output for "wrapping results informatively"
                det_count = len(results[0].boxes) if results and results[0].boxes else 0
                if det_count > 0:
                     # Only log frames with detections to save space? Or all?
                     # Let's log brief info
                    frame_summary = {
                        "frame": frame_count,
                        "detections": det_count
                    }
                    results_summary.append(frame_summary)
                
            else:
                break
                
        cap.release()
        
        if current_user:
            try:
                history = History(
                    user_id=current_user.id,
                    action_type="video_inference",
                    resource_path=str(video_path),
                    result_summary=results_summary 
                )
                db.add(history)
                db.commit()
            except Exception as e:
                print(f"Failed to log history: {e}")

        return {
            "video_path": str(video_path),
            "total_frames": frame_count,
            "frame_analysis": results_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
