# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://user:password@localhost/commercial_calls")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    RECORDINGS_DIR: str = "recordings"
    
    # App
    APP_NAME: str = "Commercial Calls Manager"
    VERSION: str = "1.0.0"

settings = Settings()