"""
Pydantic Schemas Module
========================

This module defines Pydantic models for request/response validation.

**CRITICAL CONCEPT - Data Models vs Database Models:**
- Database Models (SQLAlchemy): Define database tables (user.py, history.py)
- Pydantic Schemas (here): Define API request/response structure

**Why separate?**
1. Security: Don't expose sensitive fields (like hashed_password)
2. Validation: Validate input data before it reaches database
3. Documentation: Automatically generates OpenAPI/Swagger docs
4. Flexibility: API structure can differ from database structure

**RECURRING PATTERN (You'll see this in every FastAPI project):**
- Pydantic models for input validation
- Separate models for create vs read operations
- Config class with from_attributes=True for ORM compatibility

**ALTERNATIVES:**
- dataclasses with validation libraries
- marshmallow schemas (older, more verbose)
- attrs with validators
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

# ===== USER SCHEMAS =====
# These define the structure of user data in API requests/responses

class UserBase(BaseModel):
    """
    Base user schema with common fields.
    
    **RECURRING PATTERN:** Base classes avoid repeating fields.
    
    **Design Pattern:**
    - UserBase: Common fields (username, email)
    - UserCreate: Adds password (for registration)
    - UserOut: Adds id, removes password (for responses)
    
    This ensures:
    - Password is never returned in responses
    - Different validation for create vs read operations
    """
    username: str
    email: EmailStr  # EmailStr validates email format automatically
    # **RECURRING:** Email validation is common
    # Alternatives: str with regex, custom validator


class UserCreate(UserBase):
    """
    Schema for user registration requests.
    
    **Used in:** app/api/v1/users.py - create_user() endpoint
    
    **Example request:**
    POST /api/v1/users/register
    {
        "username": "john",
        "email": "john@example.com",
        "password": "secretpass123"
    }
    
    **Security:** Password is received in plain text here, but:
    - Only in HTTPS request body (encrypted in transit)
    - Immediately hashed before storage
    - Never logged or stored in plain text
    """
    password: str
    # **Alternative validations:**
    # password: str = Field(..., min_length=8, max_length=100)
    # Or custom validator for password strength


class UserOut(UserBase):
    """
    Schema for user data in API responses.
    
    **Used in:** app/api/v1/users.py - create_user() response
    
    **SECURITY CRITICAL:** Notice hashed_password is NOT included!
    Never expose password hashes in API responses.
    
    **Example response:**
    {
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    }
    
    **RECURRING:** Response models exclude sensitive data.
    """
    id: int
    username: str
    email: EmailStr
    
    class Config:
        """
        Pydantic configuration.
        
        **CRITICAL:** from_attributes=True allows Pydantic to read SQLAlchemy models.
        
        **Why needed?**
        SQLAlchemy models use attributes (user.username)
        By default, Pydantic expects dictionaries (user["username"])
        from_attributes=True makes Pydantic compatible with ORM objects
        
        **RECURRING:** Every response model that maps to ORM needs this.
        
        **Note:** In older Pydantic versions, this was:
        class Config:
            orm_mode = True
        """
        from_attributes = True


# ===== AUTHENTICATION SCHEMAS =====
# JWT token structures

class Token(BaseModel):
    """
    Schema for JWT token responses.
    
    **RECURRING:** Standard OAuth2 token response format.
    
    **Used in:** app/api/v1/auth.py - login_for_access_token() response
    
    **Example response:**
    POST /api/v1/token
    {
        "access_token": "eyJhbGc...",
        "token_type": "bearer"
    }
    
    **How clients use it:**
    Authorization: Bearer eyJhbGc...
    """
    access_token: str
    token_type: str  # Always "bearer" for OAuth2


class TokenData(BaseModel):
    """
    Schema for data stored inside JWT tokens.
    
    **Used internally:** When decoding tokens in get_current_user()
    
    **Payload structure:**
    {
        "sub": "john",      # username (subject)
        "exp": 1234567890   # expiration timestamp
    }
    
    **Note:** "sub" is a standard JWT claim for subject (user identifier)
    """
    username: Optional[str] = None


# ===== INFERENCE SCHEMAS (PROJECT-SPECIFIC) =====
# These are specific to YOLO object detection API

class InferenceConfig(BaseModel):
    """
    Configuration parameters for YOLO inference.
    
    **PROJECT-SPECIFIC:** These parameters are specific to YOLO models.
    
    **RECURRING CONCEPT:** Config objects with defaults and validation.
    
    **Field parameters explained:**
    - default: Value if not provided
    - ge/le: Greater/less than or equal (validation)
    - description: Shows in OpenAPI docs
    
    **YOLO Parameters:**
    - conf: Confidence threshold (0.0-1.0)
      Higher = fewer but more confident detections
      Lower = more detections but less confident
    
    - iou: Intersection over Union threshold for NMS (Non-Max Suppression)
      Removes overlapping boxes for same object
      Higher = keeps more boxes, Lower = more aggressive filtering
    
    - max_det: Maximum detections per image
      Limits output size
    
    - agnostic_nms: If True, treats all classes the same for NMS
      If False, NMS is per-class (default is usually better)
    
    - save: If True, saves annotated images with bounding boxes
    """
    conf: float = Field(
        0.25, 
        ge=0.0,  # Greater or equal to 0
        le=1.0,  # Less or equal to 1
        description="Confidence threshold"
    )
    
    iou: float = Field(
        0.7, 
        ge=0.0, 
        le=1.0, 
        description="NMS IoU threshold"
    )
    
    max_det: int = Field(
        300, 
        ge=1,  # At least 1 detection
        description="Maximum number of detections per image"
    )
    
    agnostic_nms: bool = Field(
        False, 
        description="Class-agnostic NMS"
    )
    
    save: bool = Field(
        False, 
        description="Save annotated images result"
    )


class InferenceResult(BaseModel):
    """
    Schema for inference results responses.
    
    **PROJECT-SPECIFIC:** Tailored to this API's response format.
    
    **Example response:**
    {
        "file_path": "/uploads/abc123.jpg",
        "detections_count": 5,
        "results_json": [
            {
                "class": "person",
                "confidence": 0.95,
                "box": {"x": 100, "y": 200, "w": 50, "h": 100}
            }
        ]
    }
    
    **RECURRING CONCEPT:** Result objects with optional fields.
    """
    file_path: Optional[str] = None
    detections_count: int
    results_json: Optional[Any] = None  # Any allows flexible JSON structure
    # Alternative: Define detailed structure with nested models
