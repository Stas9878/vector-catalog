# VectorCatalog

Репозиторий создан как финальный проект для моего курса на Stepik — [Qdrant: полный курс](https://stepik.org/course/292147/promo)

**VectorCatalog** — учебный SaaS-каталог товаров на FastAPI с гибридным поиском (dense + sparse), мультитенантностью и рекомендациями на базе Qdrant.

## Описание

VectorCatalog демонстрирует полный цикл работы с векторной БД в реальном веб-приложении:

- **Каталог** с пагинацией через Scroll API и изоляцией данных по `tenant_id`
- **Гибридный поиск** — семантика (dense) + ключевые слова (sparse) с fusion RRF
- **Фильтрация** по категории, цене и наличию на уровне payload
- **Рекомендации** — похожие товары и персональная лента «Рекомендуем вам» через Recommendation API
- **История просмотров** в PostgreSQL для персонализации
- **Blue-green переиндексация** через алиасы коллекций (`products` → `products_v1` / `products_v2`)
- **Production-деплой** одной командой Docker Compose

Проект использует:

- **Qdrant** — векторное хранилище, гибридный поиск, multitenancy, алиасы, snapshots
- **FastAPI** — асинхронный веб-фреймворк и HTML-витрина (Jinja2)
- **PostgreSQL + Alembic** — события просмотров и миграции схемы
- **sentence-transformers** — локальные dense-эмбеддинги без облачных API
- **Docker Compose** — Qdrant + Postgres + приложение с healthcheck

## Возможности

- 🔍 **Гибридный поиск** — prefetch dense + sparse, слияние через `Fusion.RRF`
- 🏢 **Мультитенантность** — два магазина (`acme`, `beta`) в одной коллекции с `is_tenant` индексом
- 🎯 **Recommendation API** — `positive` / `negative` для похожих товаров и персональных рекомендаций
- 📦 **Payload-фильтры** — категория, диапазон цен, наличие на складе
- 🔄 **Алиасы коллекций** — zero-downtime reindex без изменения кода приложения
- 💾 **Snapshots** — бэкап коллекции через REST API
- 🐳 **Docker-ready** — pinned-образ Qdrant, Postgres 18, автоматические миграции при старте
- 📊 **События просмотров** — история в Postgres для блока «Рекомендуем вам»

## Структура проекта

```
vector-catalog/
├── Dockerfile                    # Сборка образа (предзагрузка embedding-модели)
├── docker-compose.yml            # Qdrant + Postgres + app
├── docker-entrypoint.sh          # alembic upgrade + uvicorn
├── requirements.txt              # Зависимости Python
├── alembic.ini                   # Конфигурация миграций
│
├── alembic/                      # Миграции PostgreSQL
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_create_events.py  # Таблица событий просмотров
│
├── data/
│   └── catalog.csv               # Исходный каталог товаров (seed)
│
├── app/                          # Основное приложение
│   ├── main.py                   # FastAPI, lifespan, роутеры
│   ├── settings.py               # Pydantic Settings из .env
│   ├── embeddings.py             # Dense (sentence-transformers) + sparse
│   │
│   ├── routes/
│   │   ├── catalog.py            # GET / — витрина, scroll + tenant
│   │   ├── search.py             # GET /search — гибридный поиск
│   │   └── product.py            # GET /product/{id} — карточка + рекомендации
│   │
│   ├── qdrant/
│   │   ├── client.py             # AsyncQdrantClient
│   │   ├── collection.py         # Создание коллекции, индексы, алиас
│   │   ├── migrate.py            # ensure_alias, swap_alias, blue-green
│   │   ├── search.py             # hybrid_search, build_filter
│   │   └── recommend.py          # recommend_similar, recommend_for_user
│   │
│   ├── db/
│   │   ├── base.py               # SQLAlchemy Base
│   │   ├── session.py            # Async engine и get_db_session
│   │   ├── models.py             # Event (просмотры)
│   │   └── events.py             # record_event, get_recent_product_ids
│   │
│   ├── templates/                # Jinja2-шаблоны витрины
│   │   ├── base.html
│   │   ├── catalog.html
│   │   ├── search.html
│   │   └── product.html
│   │
│   └── static/                   # CSS, изображения
│
└── scripts/                      # Вспомогательные скрипты
    ├── check_env.py              # Проверка окружения перед разработкой
    ├── seed_catalog.py           # Загрузка CSV → Qdrant (--fresh)
    ├── reindex_with_alias.py     # Blue-green переиндексация
    └── backup_snapshot.sh        # Snapshot коллекции через curl
```

## Требования

- Python 3.11+
- Docker и Docker Compose (для production и инфраструктуры)
- Qdrant 1.18+ (локально или в Docker)
- PostgreSQL 18 (или запуск через Docker)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Stas9878/vector-catalog.git
cd vector-catalog
```

### 2. Создание виртуального окружения и установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта на основе `.env.example`:

```bash
cp .env.example .env
```

Сгенерируйте `SECRET_KEY` для продакшена:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Запуск Qdrant и PostgreSQL

Для локальной разработки поднимите только инфраструктуру:

```bash
docker compose up -d qdrant postgres
```

Или запустите Qdrant отдельно (уроки 1.4–1.6 курса).

### 5. Проверка окружения

```bash
python scripts/check_env.py
```

### 6. Миграции и загрузка каталога

```bash
alembic upgrade head
python scripts/seed_catalog.py --fresh
```

Флаг `--fresh` пересоздаёт коллекцию `products_v1`, индексы payload и алиас `products`.

### 7. Запуск приложения локально

```bash
uvicorn app.main:app --reload
```

Витрина: http://localhost:8000/?tenant=acme

Документация API: http://localhost:8000/docs

### 8. Запуск через Docker Compose (рекомендуется для production)

```bash
cp .env.example .env
# Задайте QDRANT_API_KEY и SECRET_KEY в .env

docker compose up -d --build
docker compose exec app python scripts/seed_catalog.py --fresh
```

Health-check: http://localhost:8000/health

## Веб-интерфейс и эндпоинты

Приложение отдаёт HTML-страницы. JSON API минимален — только health-check.

### `GET /health`

Проверка доступности сервиса.

**Ответ:**
```json
{
  "status": "ok",
  "env": "dev"
}
```

### `GET /`

Каталог товаров с пагинацией (Scroll API).

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `tenant` | Магазин: `acme` или `beta` (по умолчанию — `DEFAULT_TENANT` из `.env`) |
| `offset` | Курсор следующей страницы (из предыдущего ответа) |

**Пример:**
```
http://localhost:8000/?tenant=acme
http://localhost:8000/?tenant=beta&offset=...
```

На странице — сетка товаров (8 на страницу), переключатель tenant, ссылка на поиск.

### `GET /search`

Гибридный поиск с фильтрами по payload.

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `q` | Текстовый запрос (обязателен для поиска) |
| `tenant` | `acme` / `beta` |
| `category` | `laptop`, `phone`, `audio`, `kitchen` и др. |
| `min_price` | Минимальная цена |
| `max_price` | Максимальная цена |
| `in_stock` | `true` — только в наличии |

**Пример:**
```
http://localhost:8000/search?q=ноутбук&tenant=acme&category=laptop&in_stock=true
```

Пустой `q` возвращает форму поиска без результатов.

### `GET /product/{product_id}`

Карточка товара с рекомендациями.

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `tenant` | `acme` / `beta` |

**Поведение:**
1. Загрузка товара из Qdrant по `id` с проверкой `tenant_id`
2. Запись события `view` в PostgreSQL
3. Блок **«Похожие товары»** — `RecommendQuery(positive=[product_id])`
4. Блок **«Рекомендуем вам»** — на основе истории просмотров с `negative=[product_id]`

**Пример:**
```
http://localhost:8000/product/1?tenant=acme
```

**Коды ошибок:**
| Код | Ситуация |
|-----|----------|
| `404` | Товар не найден или принадлежит другому tenant |

### Пример сценария: поиск и рекомендации

```bash
# 1. Каталог магазина acme
open "http://localhost:8000/?tenant=acme"

# 2. Гибридный поиск
open "http://localhost:8000/search?q=wireless+headphones&tenant=acme"

# 3. Карточка товара — похожие и персональные рекомендации
open "http://localhost:8000/product/3?tenant=acme"

# 4. Просмотрите ещё 2–3 товара, вернитесь на карточку —
#    блок «Рекомендуем вам» обновится по истории из Postgres

# 5. Другой tenant — изолированный каталог
open "http://localhost:8000/?tenant=beta"
```

## Как это работает

### Архитектура данных

```
catalog.csv
     ↓ seed_catalog.py
┌─────────────────────────────────────┐
│  Qdrant: алиас "products"           │
│  → физическая коллекция products_v1 │
│                                     │
│  Точка: id, dense, sparse, payload  │
│  payload: tenant_id, title, price,  │
│           category, in_stock, ...   │
└─────────────────────────────────────┘
     ↑ query_points / scroll / recommend
     │
┌────┴────────────────────────────────┐
│  FastAPI (AsyncQdrantClient)        │
│  GET /  GET /search  GET /product   │
└────┬────────────────────────────────┘
     │ record_event (view)
     ↓
┌─────────────────────────────────────┐
│  PostgreSQL: таблица events         │
│  tenant_id, product_id, event_type  │
└─────────────────────────────────────┘
```

**Разделение ответственности:**
- **Qdrant** — векторы, поиск, рекомендации, multitenancy
- **PostgreSQL** — история просмотров (лёгкие события, не дублирует каталог)
- **Приложение** — обращается к алиасу `products`, не к версии `products_v1`

### Гибридный поиск

```
Запрос пользователя
        ↓
┌───────────────────┐     ┌───────────────────┐
│ encode_dense      │     │ encode_sparse     │
│ (MiniLM, 384 dim) │     │ (токены → hash)   │
└────────┬──────────┘     └────────┬──────────┘
         ↓                         ↓
    Prefetch dense            Prefetch sparse
    + query_filter            + query_filter
         └──────────┬──────────┘
                    ↓
            FusionQuery(RRF)
                    ↓
              top-12 товаров
```

Фильтр `tenant_id` обязателен в каждом запросе — данные `acme` и `beta` не пересекаются.

### Рекомендации

**Похожие товары:**
```python
RecommendQuery(recommend=RecommendInput(positive=[product_id]))
```

**Рекомендуем вам** (после истории просмотров):
```python
RecommendQuery(
    recommend=RecommendInput(
        positive=history_ids,      # недавно просмотренные
        negative=[product_id]      # текущий товар не дублируется
    )
)
```

### Blue-green переиндексация

```
products_v1 (текущая)  ←── алиас "products"
        │
        │  reindex_with_alias.py
        ↓
products_v2 (новая, полная загрузка)
        │
        │  swap_alias()
        ↓
products_v2  ←── алиас "products"
products_v1  (сохранена для отката)
```

Приложение всегда использует `COLLECTION_NAME = "products"` (алиас).

### Multitenancy

- Поле `tenant_id` в payload каждой точки
- Payload index с `is_tenant=True` для оптимизации
- Каждый HTTP-запрос фильтрует по `tenant_id` — без исключений

## Скрипты для разработки

| Скрипт | Назначение | Запуск |
|--------|------------|--------|
| `check_env.py` | Проверка venv, пакетов, Qdrant | `python scripts/check_env.py` |
| `seed_catalog.py` | Загрузка CSV в Qdrant | `python scripts/seed_catalog.py --fresh` |
| `reindex_with_alias.py` | Blue-green: новая версия + swap алиаса | `python scripts/reindex_with_alias.py` |
| `backup_snapshot.sh` | Snapshot коллекции через REST | `./scripts/backup_snapshot.sh` |

## Переменные окружения

### Локальная разработка vs Docker

| Переменная | Локально | В Docker Compose |
|------------|----------|------------------|
| `QDRANT_URL` | `http://localhost:6333` | `http://qdrant:6333` (задаётся в compose) |
| `DATABASE_URL` | `@localhost:5432` | `@postgres:5432` (задаётся в compose) |
| `QDRANT_API_KEY` | пусто или `test_key` | обязателен (Qdrant отклонит запросы без ключа) |
| `APP_ENV` | `dev` | `prod` |

### Основные переменные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `QDRANT_URL` | URL REST API Qdrant | `http://localhost:6333` |
| `QDRANT_API_KEY` | API-ключ (опционально в dev) | — |
| `QDRANT_IMAGE` | Образ Qdrant для compose | `qdrant/qdrant:v1.18.2` |
| `DATABASE_URL` | PostgreSQL (asyncpg) | `postgresql+asyncpg://vector:...@localhost:5432/vector_catalog` |
| `POSTGRES_PASSWORD` | Пароль Postgres в compose | `vector_pass` |
| `SECRET_KEY` | Секрет сессий (мин. 32 символа) | — |
| `DEFAULT_TENANT` | Tenant по умолчанию на витрине | `acme` |
| `EMBEDDING_MODEL` | Модель sentence-transformers | `sentence-transformers/all-MiniLM-L6-v2` |
| `APP_PORT` | Порт приложения | `8000` |

## Логирование

Логи uvicorn выводятся в stdout:

```bash
# Локально
uvicorn app.main:app --reload

# Docker
docker compose logs -f app
```

## Troubleshooting

### Qdrant недоступен / 401 Unauthorized

- Проверьте контейнер: `docker compose ps qdrant`
- В Docker `QDRANT_API_KEY` должен совпадать в сервисах `qdrant` и `app`
- Локально без ключа оставьте `QDRANT_API_KEY` пустым в `.env`
- Проверьте `QDRANT_URL` в `.env`

### PostgreSQL unhealthy (Docker)

- Postgres 18 монтирует volume в `/var/lib/postgresql`, не `/var/lib/postgresql/data`
- Проверьте: `docker compose logs postgres`
- Примените миграции: `docker compose exec app alembic upgrade head`

### Пустой каталог / «Товар не найден»

- Загрузите данные: `python scripts/seed_catalog.py --fresh`
- В Docker: `docker compose exec app python scripts/seed_catalog.py --fresh`
- Убедитесь, что `tenant` в URL совпадает с данными (`acme` / `beta`)

### Поиск не возвращает результатов

- Проверьте, что `q` не пустой
- Убедитесь, что seed выполнен и алиас `products` указывает на коллекцию с точками
- Dashboard Qdrant: http://localhost:6333/dashboard

### «Рекомендуем вам» пустой

- Блок появляется после просмотра нескольких товаров (история в Postgres)
- Нужны применённые миграции: `alembic upgrade head`
- Первый визит на карточку — только «Похожие товары»

### Медленный первый запрос

- При первом поиске загружается модель `sentence-transformers` (~80 МБ)
- В Docker образ модель предзагружается на этапе сборки (`Dockerfile`)

## Разработка

### Добавление поля в payload

1. Добавьте колонку в `data/catalog.csv`
2. Обновите `row_to_point()` в `scripts/seed_catalog.py`
3. При необходимости — `create_payload_index()` в `app/qdrant/collection.py`
4. Переиндексируйте: `python scripts/seed_catalog.py --fresh`

### Смена embedding-модели

1. Измените `EMBEDDING_MODEL` в `.env`
2. Обновите `DENSE_DIM` в `app/qdrant/collection.py`, если размерность изменилась
3. Пересоздайте коллекцию и переиндексируйте

### Новый tenant

1. Добавьте строки с новым `tenant_id` в `catalog.csv`
2. Добавьте tenant в `TENANTS` в `app/routes/catalog.py`
3. Обновите pattern в `app/settings.py` (`DEFAULT_TENANT`)
4. Запустите seed или reindex

## Лицензия

MIT License — используйте, изменяйте и распространяйте проект по своему усмотрению.

## Автор

[@Stas9878](https://github.com/Stas9878)
