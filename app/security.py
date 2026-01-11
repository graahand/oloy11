"""
Security & Authentication Module
=================================

This module handles all security-related functionality:
- Password hashing and verification (using bcrypt)
- JWT token creation and validation
- User authentication via Bearer tokens

**RECURRING PATTERN (Standard in most secure web APIs):**
- Password hashing before storage
- JWT tokens for stateless authentication
- Dependency injection for current user retrieval

**PROJECT-SPECIFIC:**
- Specific token expiration times
- Choice of bcrypt over alternatives (argon2, scrypt)

**SECURITY BEST PRACTICES:**
1. Never store plain passwords - always hash
2. Use strong, randomly generated SECRET_KEY in production
3. Set appropriate token expiration (balance security vs UX)
4. Use HTTPS in production to protect tokens in transit

**ALTERNATIVES:**
Password Hashing:
  - argon2 (newer, more secure, recommended by OWASP)
  - scrypt (memory-hard, good against GPU attacks)
  - bcrypt (older but battle-tested, used here)

Authentication:
  - OAuth2 + JWT (used here - stateless, scalable)
  - Session-based (requires server-side storage)
  - API Keys (simpler but less secure)
  - OAuth2 with third-party (Google, GitHub)
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models.user import User

# ===== CONSTANTS =====

# Bcrypt can only hash passwords up to 72 bytes.
# Longer passwords are truncated to prevent errors and ensure consistency.
# **Why 72?** It's a bcrypt limitation due to its underlying Blowfish cipher.
# **RECURRING:** This appears in most bcrypt implementations.
MAX_PASSWORD_BYTES = 72

# ===== CONFIGURATION =====

# Get application settings (singleton)
settings = get_settings()

# ===== PASSWORD HASHING CONTEXT =====
# CryptContext manages password hashing algorithms.
# 
# **RECURRING:** You'll see this in most Python auth implementations.
#
# schemes=["bcrypt"]: Use bcrypt algorithm
#   - Alternatives: ["argon2", "bcrypt"], ["scrypt", "bcrypt"]
#   - List order matters: first is preferred, others for backward compatibility
# 
# deprecated="auto": Automatically rehash passwords using deprecated algorithms
#   - Useful when upgrading hash algorithms without breaking existing passwords
#
# **How it works:**
# 1. Hash: Takes plain password → generates random salt → produces hash
# 2. Verify: Takes plain password + stored hash → checks if they match
# 3. Salt is embedded in the hash output, so you don't store it separately
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===== OAUTH2 BEARER TOKEN SCHEME =====
# OAuth2PasswordBearer extracts the Bearer token from HTTP requests.
#
# **RECURRING:** Standard pattern for JWT-based authentication.
#
# **How it works:**
# 1. Client logs in → receives JWT token
# 2. Client includes token in subsequent requests: 
#    Header: Authorization: Bearer <token>
# 3. oauth2_scheme automatically extracts <token> from the header
# 4. Token is passed to get_current_user() for validation
#
# **Parameters:**
# - tokenUrl: Where clients can get tokens (login endpoint)
#   Format: "http://api.example.com/api/v1/token"
# - auto_error=False: Don't automatically return 401 if token is missing
#   Why? Allows optional authentication (some endpoints work with/without user)
#   Alternative: auto_error=True (stricter, always require token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token", auto_error=False)


# ===== HELPER FUNCTIONS =====

def _truncate_password(password: str) -> str:
    """
    Internal helper: Truncate password to MAX_PASSWORD_BYTES (72 bytes).
    
    **Why needed?**
    Bcrypt silently truncates passwords longer than 72 bytes.
    We do it explicitly to be consistent and predictable.
    
    **How it works:**
    1. Encode password to UTF-8 bytes
    2. Check if length exceeds 72 bytes
    3. If yes, truncate to 72 bytes and decode back to string
    4. errors="ignore" handles incomplete multi-byte characters at boundary
    
    **RECURRING:** Any bcrypt implementation should handle this.
    
    **Security note:**
    This doesn't weaken security. Bcrypt would truncate anyway.
    We just make it explicit and handle encoding properly.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Password truncated to 72 bytes if necessary
    """
    # Convert string to bytes using UTF-8 encoding
    encoded = password.encode("utf-8")
    
    # Check if password fits within bcrypt's limit
    if len(encoded) <= MAX_PASSWORD_BYTES:
        return password  # No truncation needed
    
    # Truncate to 72 bytes
    truncated = encoded[:MAX_PASSWORD_BYTES]
    
    # Decode back to string
    # errors="ignore": Skip invalid bytes at truncation boundary
    # (UTF-8 multi-byte characters might be cut in the middle)
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    **RECURRING:** Every authentication system needs this.
    
    **How it works:**
    1. Truncate plain password to 72 bytes (bcrypt requirement)
    2. Use pwd_context to compare plain vs hashed
    3. pwd_context extracts salt from hashed_password
    4. Hashes plain_password with same salt
    5. Compares the two hashes
    
    **Security:**
    - Constant-time comparison (prevents timing attacks)
    - Salt is unique per password (prevents rainbow tables)
    
    **Used in:**
    - app/api/v1/auth.py: login_for_access_token() - verifying user credentials
    
    Args:
        plain_password: User-provided password (from login form)
        hashed_password: Stored password hash (from database)
        
    Returns:
        bool: True if password matches, False otherwise
    """
    # Normalize password (truncate to 72 bytes)
    normalized = _truncate_password(plain_password)
    
    # Verify using bcrypt
    # Returns True if passwords match, False otherwise
    return pwd_context.verify(normalized, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password for secure storage.
    
    **RECURRING:** Every user registration/password reset needs this.
    
    **How it works:**
    1. Truncate password to 72 bytes
    2. Generate random salt
    3. Hash password with salt using bcrypt
    4. Return hash (salt is embedded in the hash string)
    
    **Security:**
    - Each call generates a different hash (even for same password)
    - Salt prevents rainbow table attacks
    - Bcrypt is slow by design (prevents brute force)
    
    **Hash format example:**
    $2b$12$KIXxnJLvBEZaGQVPZqYTx.h9jZ8u9LjVQP3vK5xF7YwKHhEq5E8xW
    |  |  |                    |
    |  |  cost factor (2^12)   |
    |  algorithm (2b=bcrypt)   salt + hash
    
    **Used in:**
    - app/api/v1/users.py: create_user() - hashing password during registration
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Bcrypt password hash (includes salt)
    """
    # Normalize password (truncate to 72 bytes)
    normalized = _truncate_password(password)
    
    # Hash using bcrypt
    # Generates new salt automatically
    return pwd_context.hash(normalized)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for authentication.
    
    **RECURRING:** Standard pattern for JWT-based authentication.
    
    **How JWT works:**
    1. Create payload (data) containing user info
    2. Add expiration time
    3. Sign payload with SECRET_KEY
    4. Return encoded token (three Base64 strings separated by dots)
    
    **JWT Structure:**
    header.payload.signature
    
    Example token:
    eyJhbGc.eyJzdWI.h3jH7k
    |       |       |
    metadata user    signature
             info
    
    **Security:**
    - Token is signed (can't be tampered with)
    - Token is NOT encrypted (don't put sensitive data in it)
    - Always use HTTPS to protect token in transit
    - Short expiration time limits damage from stolen tokens
    
    **Used in:**
    - app/api/v1/auth.py: login_for_access_token() - creating token after successful login
    
    **Alternatives:**
    - Refresh tokens: Long-lived tokens to get new access tokens
    - Opaque tokens: Random strings, validated against database
    - Session-based: Store authentication server-side
    
    Args:
        data: Dictionary with user info (typically {"sub": username})
              "sub" (subject) is standard JWT claim for user identifier
        expires_delta: Optional custom expiration time
                      If None, uses default from settings
        
    Returns:
        str: Encoded JWT token
    """
    # Copy data to avoid modifying the original
    to_encode = data.copy()
    
    # Calculate expiration time
    if expires_delta:
        # Use custom expiration if provided
        expire = datetime.now() + expires_delta
    else:
        # Use default expiration from settings
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration to payload
    # "exp" is a standard JWT claim for expiration time
    to_encode.update({"exp": expire})
    
    # Encode and sign the JWT
    # Uses SECRET_KEY and ALGORITHM from settings
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to get the current authenticated user.
    
    **CRITICAL PATTERN - You'll see this in every protected FastAPI endpoint!**
    
    **How it works:**
    1. oauth2_scheme extracts token from Authorization header
    2. Decode and validate the JWT token
    3. Extract username from token payload
    4. Query database to get user object
    5. Return user object (or None if token missing, or raise error if invalid)
    
    **Why async?**
    - FastAPI supports both sync and async functions
    - Async allows non-blocking operations (good for scalability)
    - Even with sync database, marking as async allows future async DB migration
    - Compatible with FastAPI's async request handling
    
    **Usage in routes:**
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        if not current_user:
            raise HTTPException(401, "Not authenticated")
        return {"user": current_user.username}
    
    **Used in:**
    - app/api/v1/users.py: read_history() - getting user's history
    - app/api/v1/inference.py: predict_image(), predict_video() - logging user's actions
    
    **RECURRING:** This pattern (or similar) is in every FastAPI auth tutorial.
    
    **Error handling:**
    - Token missing → Returns None (allows optional authentication)
    - Token invalid → Raises 401 Unauthorized
    - User not found → Raises 401 Unauthorized
    
    Args:
        token: JWT token from Authorization header (extracted by oauth2_scheme)
        db: Database session (injected by get_db dependency)
        
    Returns:
        Optional[User]: User object if authenticated, None if no token provided
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    # If no token provided, return None (optional authentication)
    if not token:
        return None
    
    # Prepare exception for authentication failures
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # Tells client to send Bearer token
    )
    
    try:
        # Decode the JWT token
        # This verifies the signature using SECRET_KEY
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract username from payload
        # "sub" (subject) is standard JWT claim for user identifier
        username: str = payload.get("sub")
        
        # If no username in token, it's invalid
        if username is None:
            raise credentials_exception
            
    except JWTError:
        # Token is malformed, expired, or signature invalid
        raise credentials_exception
    
    # Query database for user
    user = db.query(User).filter(User.username == username).first()
    
    # If user doesn't exist, token is invalid (user was deleted?)
    if user is None:
        raise credentials_exception
    
    # Return the authenticated user
    return user
