"""
User Management Routes Module
==============================

This module handles user-related API endpoints.

**RECURRING PATTERNS:**
- User registration endpoint
- Protected endpoints requiring authentication
- CRUD operations on user data

**PROJECT-SPECIFIC:**
- History tracking integration
- Specific fields in user model

**ALTERNATIVES:**
- Email verification during registration
- Password reset functionality
- User profile updates
- Admin endpoints for user management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.history import History
from app.models.schemas import UserCreate, UserOut
from app.security import get_password_hash, get_current_user
from typing import List

# ===== ROUTER =====
# APIRouter for user-related endpoints
# **RECURRING:** Grouping related endpoints in routers
router = APIRouter()


@router.post("/register", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    User registration endpoint.
    
    **RECURRING:** Almost every app needs user registration.
    
    **How it works:**
    1. Receive user data (username, email, password)
    2. Check if username already exists
    3. If exists, return 400 error
    4. If not, hash password
    5. Create user in database
    6. Return created user (without password!)
    
    **Request example:**
    POST /api/v1/users/register
    Content-Type: application/json
    
    {
        "username": "john",
        "email": "john@example.com",
        "password": "secretpass123"
    }
    
    **Response example:**
    {
        "id": 1,
        "username": "john",
        "email": "john@example.com"
    }
    
    **Security considerations:**
    - Password is immediately hashed (never stored in plain text)
    - Response doesn't include password hash
    - Check for existing username prevents duplicates
    - Consider: Email verification, CAPTCHA, rate limiting
    
    **Improvements you might add:**
    - Email verification (send confirmation email)
    - Username validation (length, allowed characters)
    - Password strength requirements
    - Rate limiting (prevent spam registrations)
    
    **Related files:**
    - app/models/user.py: User database model
    - app/models/schemas.py: UserCreate (input), UserOut (output)
    - app/security.py: get_password_hash()
    
    Args:
        user: UserCreate schema with username, email, password
        db: Database session (dependency injection)
        
    Returns:
        UserOut: Created user without password
        
    Raises:
        HTTPException: 400 if username already exists
    """
    # Check if username already exists
    # .first() returns None if not found
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if db_user:
        # Username is taken, return 400 Bad Request
        # **ALTERNATIVE:** Check email too and provide specific error message
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password using bcrypt
    # **SECURITY CRITICAL:** Never store plain passwords!
    hashed_password = get_password_hash(user.password)
    
    # Create User object
    # Note: We use hashed_password, not user.password
    db_user = User(
        email=user.email, 
        username=user.username, 
        hashed_password=hashed_password
    )
    
    # Add to database session
    db.add(db_user)
    
    # Commit transaction (actually save to database)
    # **Important:** Until commit(), changes are only in memory
    db.commit()
    
    # Refresh to get the generated id from database
    # After commit, db_user.id is populated with auto-generated value
    db.refresh(db_user)
    
    # Return the created user
    # FastAPI automatically converts User model to UserOut schema
    # UserOut excludes hashed_password (security!)
    return db_user


@router.get("/history")
def read_history(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get user's inference history.
    
    **RECURRING:** Protected endpoints that return user-specific data.
    
    **How it works:**
    1. get_current_user extracts and validates JWT token
    2. If invalid/missing token, raises 401 error
    3. Query History table for records belonging to current user
    4. Apply pagination (skip/limit)
    5. Return results
    
    **Authentication:**
    Requires valid JWT token in Authorization header:
    Authorization: Bearer eyJhbGc...
    
    **Request example:**
    GET /api/v1/users/history?skip=0&limit=10
    Authorization: Bearer eyJhbGc...
    
    **Response example:**
    [
        {
            "id": 1,
            "user_id": 5,
            "action_type": "image_inference",
            "resource_path": "/uploads/abc123.jpg",
            "timestamp": "2025-01-11T10:30:00",
            "result_summary": {"detections": 5}
        },
        ...
    ]
    
    **Pagination parameters:**
    - skip: Number of records to skip (for pagination)
    - limit: Maximum records to return
    
    **Example pagination:**
    Page 1: skip=0, limit=10   (records 0-9)
    Page 2: skip=10, limit=10  (records 10-19)
    Page 3: skip=20, limit=10  (records 20-29)
    
    **Security:**
    - Only returns history for authenticated user
    - Can't access other users' history
    - Token is validated before query runs
    
    **Improvements you might add:**
    - Filter by action_type: ?action_type=image_inference
    - Date range filtering: ?from=2025-01-01&to=2025-01-31
    - Sorting: ?sort_by=timestamp&order=desc
    - Response pagination metadata: {"total": 50, "page": 1}
    
    **Related files:**
    - app/models/history.py: History database model
    - app/security.py: get_current_user()
    - app/api/v1/inference.py: Creates history records
    
    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100)
        db: Database session (dependency injection)
        current_user: Authenticated user (dependency injection)
        
    Returns:
        List[History]: User's history records
    """
    # Query History table
    # .filter(): Only records for this user
    # .offset(): Skip first N records (pagination)
    # .limit(): Return at most N records (pagination)
    # .all(): Execute query and return all matching records
    history = db.query(History)\
        .filter(History.user_id == current_user.id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Return results
    # FastAPI automatically converts SQLAlchemy objects to JSON
    return history
