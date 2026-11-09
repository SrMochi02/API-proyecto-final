import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "API REST Sistema Bibliotecario"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Configuracion de seguridad JWT
    SECRET_KEY: str = "clave_secreta_jwt_biblioteca_itca_2026_segura"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Base de datos (Soporta PostgreSQL o SQLite)
    DATABASE_URL: str = "sqlite:///./biblioteca.db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
