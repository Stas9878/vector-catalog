"""
Проверка готовности окружения VectorCatalog.
Запуск: python scripts/check_env.py
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print("WARN  Виртуальное окружение не активировано")
        print("      Активируйте: source .venv/bin/activate")
        return False
    print("OK    Виртуальное окружение: активно")
    return True


def check_packages() -> bool:
    required = ["fastapi", "uvicorn", "jinja2", "qdrant_client", "pydantic"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"FAIL  Не установлены пакеты: {missing}")
        print("      Выполните: pip install -r requirements.txt")
        return False
    print(f"OK    Зависимости: установлены ({len(required)} пакетов)")
    return True


def check_config() -> bool:
    try:
        from app.config import get_settings

        settings = get_settings()
        if settings.SECRET_KEY == "change-me-in-production-use-secrets-module":
            print("WARN  SECRET_KEY не изменён (допустимо для dev)")
        print(f"OK    Конфигурация: загружена (режим: {settings.APP_ENV})")
        return True
    except Exception as exc:
        print(f"FAIL  Конфигурация: {exc}")
        return False


async def _check_qdrant_async() -> bool:
    from qdrant_client import AsyncQdrantClient

    from app.config import get_settings

    settings = get_settings()
    kwargs = {"url": str(settings.QDRANT_URL)}
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    client = AsyncQdrantClient(**kwargs)
    try:
        collections = await client.get_collections()
        count = len(collections.collections)
        print(f"OK    Qdrant: доступен ({count} коллекций)")
        return True
    finally:
        await client.close()


def check_qdrant() -> bool:
    try:
        return asyncio.run(_check_qdrant_async())
    except Exception as exc:
        print(f"FAIL  Qdrant: {exc}")
        print("      Поднимите контейнер (см. урок 6.1, шаг 3)")
        return False


def main() -> int:
    print("Проверка окружения VectorCatalog\n")

    checks = [
        check_venv(),
        check_packages(),
        check_config(),
        check_qdrant()
    ]

    print()
    if all(checks):
        print("✅ Окружение готово к разработке.")
        return 0
    print("Исправьте ошибки перед продолжением.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
