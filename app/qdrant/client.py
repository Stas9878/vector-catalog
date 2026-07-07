from qdrant_client import AsyncQdrantClient

from app.config import get_settings


def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    kwargs = {"url": str(settings.QDRANT_URL)}
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    return AsyncQdrantClient(**kwargs)
