import os
from dotenv import load_dotenv
from pathlib import Path

# Load env from both backend/.env and project/.env if present.
BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
PROJECT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=BACKEND_ENV_PATH)
load_dotenv(dotenv_path=PROJECT_ENV_PATH)

class Settings:
    # Database configuration
    MONGO_URL: str = os.getenv("MONGO_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    
    # JWT configuration
    JWT_SECRET_KEY: str = (
        os.getenv("JWT_SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or "CHANGE_ME_DEV_ONLY_JWT_SECRET_2026"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Token refresh
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()
