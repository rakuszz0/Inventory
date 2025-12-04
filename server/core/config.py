from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
from functools import lru_cache
import json


class Settings(BaseSettings):
    # Database 
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False      # ⬅ FIX

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = Field(default_factory=list)

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [v]
        return v

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    
    # Application
    APP_NAME: str = "Inventory Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
