""" 
Configuración centralizada de la aplicación
Los valores se pueden sobrescribir con variables de entorno o un archivo .env
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Aplicación ---
    APP_NAME: str = "Mi Finanza"
    APP_VERSION: str = "0.3.3"
    DEBUG: bool = False

    # --- Servidores ---
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DASH_HOST: str = "127.0.0.1"
    DASH_PORT: int = 8050
 
    # --- Base de Datos ---
    DATABASE_URL: str = "sqlite:///./finance_app.db"
 
    # --- CORS (para la API REST) ---
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8050",
        "http://localhost:8050",
    ]
 
    # --- Finanzas ---
    DEFAULT_CURRENCY: str = "EUR"
 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
 
 
@lru_cache
def get_settings() -> Settings:
    return Settings()
 
 
settings = get_settings()