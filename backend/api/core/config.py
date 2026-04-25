import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database configuration
    MONGO_URL: str = os.getenv("MONGO_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    
    # JWT configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Token refresh
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()
