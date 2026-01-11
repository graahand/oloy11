"""
Configuration Management Module
================================

This module handles all application configuration using a Settings class.

**RECURRING PATTERN (You'll see this in almost every FastAPI project):**
- Centralized configuration in a Settings class
- Using environment variables with fallback defaults
- Settings as a dependency injection (DI) pattern

**PROJECT-SPECIFIC (May vary):**
- The specific settings names and values
- MODEL_PATH is specific to ML projects

**ALTERNATIVES:**
1. pydantic.BaseSettings - More robust with type validation and .env file support
   from pydantic import BaseSettings
   class Settings(BaseSettings):
       class Config:
           env_file = ".env"
           
2. python-decouple - Simpler environment variable management
   from decouple import config
   SECRET_KEY = config('SECRET_KEY', default='supersecretkey')
   
3. dynaconf - Advanced configuration with multiple environments
"""

import os
from functools import lru_cache
from pathlib import Path

class Settings:
    """
    Application Configuration Class
    
    This class stores all configuration parameters for the application.
    Uses environment variables with sensible defaults for flexibility.
    
    **Why this approach?**
    - Easy to change settings without code modification
    - Different configs for dev/staging/production environments
    - Secure: sensitive data (SECRET_KEY) can be set via environment variables
    
    **RECURRING:** Every FastAPI app needs configuration management.
    """
    
    # ===== API Metadata =====
    # These appear in OpenAPI/Swagger documentation
    PROJECT_NAME: str = "Oloy11"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"  # API version prefix for all routes
    
    # ===== Security Settings =====
    # CRITICAL: In production, always set SECRET_KEY via environment variable!
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    
    # JWT Algorithm - HS256 is standard for symmetric key signing
    # Alternative: RS256 (asymmetric, more secure but requires key pair)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Token expiration in minutes - balances security vs user convenience
    # Shorter = more secure, Longer = better UX
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # ===== Database Configuration =====
    # Default: SQLite (file-based, good for dev/small projects)
    # Production alternatives:
    #   - PostgreSQL: "postgresql://user:pass@localhost/dbname"
    #   - MySQL: "mysql://user:pass@localhost/dbname"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./oloy11.db")
    
    # ===== File Storage =====
    # Directory for uploaded images/videos
    # Alternative: Cloud storage (AWS S3, Azure Blob, Google Cloud Storage)
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    
    # ===== ML Model Configuration (PROJECT-SPECIFIC) =====
    # Path to YOLO model weights
    # This is specific to computer vision projects
    MODEL_PATH: str = "yolo11n.pt"  # 'n' = nano (smallest, fastest)
    # Other YOLO11 variants: yolo11s.pt, yolo11m.pt, yolo11l.pt, yolo11x.pt
    # Tradeoff: smaller = faster/less accurate, larger = slower/more accurate

    def __init__(self):
        """
        Initialize settings and create necessary directories.
        
        **RECURRING:** Directory creation is common in projects with file uploads.
        """
        # Create upload directory if it doesn't exist
        # parents=True: create parent directories if needed (like mkdir -p)
        # exist_ok=True: don't error if directory already exists
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings():
    """
    Get cached settings instance.
    
    **CRITICAL PATTERN - You'll see this everywhere!**
    @lru_cache() decorator ensures Settings is created only once (singleton).
    
    **Why?**
    - Performance: Settings is created once, reused everywhere
    - Consistency: Same settings object across all requests
    - Memory efficient: Only one instance in memory
    
    **Usage in FastAPI:**
    settings = Depends(get_settings)  # In route functions
    settings = get_settings()         # In modules
    
    **RECURRING:** This exact pattern is in most FastAPI projects.
    
    Returns:
        Settings: Application settings singleton
    """
    return Settings()
