"""Configurações centrais da aplicação."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""

    # App
    app_name: str = "Fleet Route Optimizer"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://fleet:fleet@localhost:5432/fleet_optimizer"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Waze Integration
    waze_api_key: str = ""
    waze_api_url: str = "https://www.waze.com/live-map/api"
    waze_polling_interval_seconds: int = 30

    # Route Optimization
    max_deliveries_per_driver: int = 20
    re_route_on_incident_severity: int = 3  # 1-5, re-roteia se >= este valor
    default_speed_kmh: float = 40.0

    # WebSocket
    ws_heartbeat_seconds: int = 10

    # Auth
    secret_key: str = "change-me-in-production-please"
    access_token_expire_minutes: int = 480

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
