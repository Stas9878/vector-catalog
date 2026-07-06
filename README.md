# VectorCatalog

SaaS-платформа поиска и рекомендаций товаров на **FastAPI + Qdrant**.  
Pet-проект курса [Qdrant на Stepik](https://stepik.org/course/292147).

## Стек

- FastAPI, Jinja2 (HTML/CSS)
- qdrant-client, гибридный поиск, Recommendation API
- Docker Compose (production)

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

docker run -d --name vector-catalog-qdrant -p 6333:6333 \
  -v vector_catalog_qdrant:/qdrant/storage qdrant/qdrant:v1.18.2

python scripts/check_env.py
```

## Структура

См. урок «Архитектура и окружение» в модуле 6 курса.
