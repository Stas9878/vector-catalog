# VectorCatalog

Учебный SaaS-каталог на FastAPI + Qdrant + PostgreSQL. Capstone курса Qdrant.

## Быстрый старт (разработка)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Qdrant и Postgres — отдельные контейнеры (уроки 6.1, 6.5)
python scripts/check_env.py
python scripts/seed_catalog.py --fresh
alembic upgrade head
uvicorn app.main:app --reload
```

Витрина: http://localhost:8000/?tenant=acme

## Production (Docker Compose)

```bash
cp .env.example .env
# Задайте QDRANT_API_KEY и SECRET_KEY в .env

docker compose up -d --build
docker compose exec app python scripts/seed_catalog.py --fresh
```

Приложение: http://localhost:8000/health

## Полезные команды

| Команда | Назначение |
|---------|------------|
| `python scripts/seed_catalog.py --fresh` | Пересоздать `products_v1` и алиас `products` |
| `python scripts/reindex_with_alias.py` | Blue-green: `products_v2` + swap алиаса |
| `./scripts/backup_snapshot.sh` | Snapshot коллекции через REST API |
| `alembic upgrade head` | Применить миграции Postgres |

## Структура

- `app/` — FastAPI, Qdrant, Postgres
- `app/qdrant/migrate.py` — алиасы коллекций
- `scripts/` — seed, reindex, backup, check_env
- `docker-compose.yml` — Qdrant + Postgres + приложение

Приложение обращается к алиасу `products`, а не к версии `products_v1` / `products_v2`.
