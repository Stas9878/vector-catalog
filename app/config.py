from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки VectorCatalog из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    QDRANT_URL: AnyHttpUrl = Field(
        default="http://localhost:6333",
        description="URL Qdrant REST API"
    )
    QDRANT_API_KEY: str | None = Field(
        default=None,
        description="API key Qdrant (опционально для dev)"
    )

    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000, gt=0, lt=65536)
    APP_ENV: str = Field(default="dev", pattern="^(dev|prod)$")

    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Секретный ключ для cookie-сессий"
    )

    DEFAULT_TENANT: str = Field(
        default="acme",
        pattern="^(acme|beta)$",
        description="Tenant по умолчанию на витрине"
    )

    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Модель для dense-embedding (урок 6.2)"
    )

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
