"""
Blue-green переиндексация каталога через алиас коллекции.
Запуск: python scripts/reindex_with_alias.py
"""
import csv
import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.embeddings import encode_dense, encode_sparse, product_text
from app.qdrant.client import get_qdrant_client
from app.qdrant.collection import (
    COLLECTION_NAME,
    create_payload_indexes,
    create_physical_collection,
)
from app.qdrant.migrate import get_alias_target, next_physical_name, swap_alias

CSV_PATH = project_root / "data" / "catalog.csv"


def load_rows() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def row_to_point(row: dict) -> PointStruct:
    text = product_text(row["title"], row["description"])
    return PointStruct(
        id=int(row["id"]),
        vector={
            "dense": encode_dense(text),
            "sparse": encode_sparse(text)
        },
        payload={
            "tenant_id": row["tenant_id"],
            "title": row["title"],
            "description": row["description"],
            "category": row["category"],
            "price": float(row["price"]),
            "in_stock": row["in_stock"].lower() == "true"
        }
    )


async def main() -> int:
    if not CSV_PATH.exists():
        print(f"FAIL  Не найден файл {CSV_PATH}")
        return 1

    rows = load_rows()
    client = get_qdrant_client()

    try:
        current = await get_alias_target(client)
        new_name = next_physical_name(current)
        print(f"Текущая коллекция: {current or '(алиас не создан)'}")
        print(f"Новая коллекция: {new_name}")

        if await client.collection_exists(new_name):
            await client.delete_collection(new_name)

        await create_physical_collection(client, new_name)
        await create_payload_indexes(client, new_name)

        points = [row_to_point(row) for row in rows]
        await client.upsert(collection_name=new_name, points=points, wait=True)

        old_count = 0
        if current and await client.collection_exists(current):
            old_count = (await client.count(current, exact=True)).count

        await swap_alias(client, alias=COLLECTION_NAME, collection_name=new_name)

        new_count = (await client.count(COLLECTION_NAME, exact=True)).count
        target = await get_alias_target(client)

        print(f"✅ Алиас {COLLECTION_NAME} → {target}")
        print(f"✅ Точек в алиасе: {new_count} (было в {current}: {old_count})")
        print(f"   Старая коллекция {current} сохранена для отката")
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
