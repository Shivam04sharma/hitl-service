"""Local config - runs on developer machine / minikube."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env.example", extra="ignore")

    env: str = os.getenv("ENV", "")
    service_name: str = os.getenv("SERVICE_NAME", "")
    port: int = int(os.getenv("PORT", ""))
    log_level: str = os.getenv("LOG_LEVEL", "")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    db_url: str = os.getenv("DB_URL", "")
    db_username: str = os.getenv("DB_USERNAME", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.environ.get("DB_PORT", ""))
    db_name: str = os.getenv("DB_NAME", "")
    db_schema: str = os.environ.get("DB_SCHEMA", "")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))


    # Auth
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "")

    # HITL settings
    review_default_sla_seconds: int = int(os.getenv("REVIEW_DEFAULT_SLA_SECONDS", "300"))

    @property
    def get_db_url(self) -> str:
        if self.db_url:
            return self.db_url
        host = self.db_host.removeprefix("postgresql://")
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{host}:{self.db_port}/{self.db_name}"


settings = LocalSettings()
