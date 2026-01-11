"""
Authentication Routes Module
============================

This module handles authentication-related API endpoints.

**RECURRING PATTERN (You'll see this in every FastAPI project with auth):**
- /token endpoint for login
- OAuth2PasswordRequestForm for username/password
- Returns JWT token on successful authentication

**PROJECT-SPECIFIC:**
- The specific token generation logic
- Database query for user lookup

**ALTERNATIVES:**
- OAuth2 with third-party providers (Google, GitHub)
- Session-based authentication
- API key authentication
- Multi-factor authentication (2FA)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import create_access_token, verify_password
from app.models.user import User
from app.models.schemas import Token

# ===== ROUTER =====
# APIRouter groups related endpoints together
# **RECURRING:** Every FastAPI app organizes routes with APIRouter
router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    User login endpoint - returns JWT access token.
    
    **CRITICAL ENDPOINT - This is how users authenticate!**
    
    **RECURRING:** Every authentication system needs a login endpoint.
    
    **How it works:**
    1. Client sends username + password (form data, not JSON!)
    2. Query database for user with matching username
    3. Verify password against stored hash
    4. If valid, create and return JWT token
    5. If invalid, return 401 Unauthorized
    
    **OAuth2PasswordRequestForm:**
    FastAPI's built-in form for username/password login.
    
    **Why form data, not JSON?**
    OAuth2 spec requires form data (application/x-www-form-urlencoded)
    
    **Request format:**
    POST /api/v1/token
    Content-Type: application/x-www-form-urlencoded
    
    username=john&password=secretpass123
    
    **Response format:**
    {
        "access_token": "eyJhbGc...",
        "token_type": "bearer"
    }
    
    **How clients use the token:**
    Authorization: Bearer eyJhbGc...
    
    **Security considerations:**
    - Always use HTTPS in production (protects password in transit)
    - Rate limit this endpoint (prevent brute force attacks)
    - Consider adding account lockout after N failed attempts
    - Log failed login attempts for security monitoring
    
    **Used by:**
    - Frontend login forms
    - Mobile apps
    - CLI tools
    - Other services that need API access
    
    **Related files:**
    - app/security.py: create_access_token(), verify_password()
    - app/models/user.py: User database model
    - app/models/schemas.py: Token response schema
    
    Args:
        form_data: Username and password from login form
                   Automatically parsed by OAuth2PasswordRequestForm
        db: Database session (injected by FastAPI)
        
    Returns:
        dict: Access token and token type
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Query database for user with matching username
    # .first() returns None if not found (instead of raising exception)
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Check if user exists AND password is correct
    # Using 'or' ensures we check password only if user exists (avoid None error)
    # verify_password compares plain password with hashed password
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Return 401 Unauthorized
        # **SECURITY:** Don't specify whether username or password was wrong
        # (Prevents username enumeration attacks)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
            # WWW-Authenticate header tells client what auth method to use
        )
    
    # Create JWT access token
    # data={"sub": user.username}: "sub" is standard JWT claim for subject (user)
    access_token = create_access_token(data={"sub": user.username})
    
    # Return token in OAuth2 standard format
    # FastAPI automatically validates against Token schema
    return {"access_token": access_token, "token_type": "bearer"}
