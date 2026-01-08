import os
from functools import lru_cache
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Oloy11"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./oloy11.db")
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    
    MODEL_PATH: str = "yolo11n.pt" 

    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings():
    return Settings()
