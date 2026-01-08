from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    username: str
    email: EmailStr
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class InferenceConfig(BaseModel):
    conf: float = Field(0.25, ge=0.0, le=1.0, description="Confidence threshold")
    iou: float = Field(0.7, ge=0.0, le=1.0, description="NMS IoU threshold")
    max_det: int = Field(300, ge=1, description="Maximum number of detections per image")
    agnostic_nms: bool = Field(False, description="Class-agnostic NMS")
    save: bool = Field(False, description="Save annotated images result")

class InferenceResult(BaseModel):
    file_path: Optional[str] = None
    detections_count: int
    results_json: Optional[Any] = None
