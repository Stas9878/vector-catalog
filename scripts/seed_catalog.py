"""
Загрузка каталога из CSV в Qdrant.
Запуск: python scripts/seed_catalog.py
"""
import csv
import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.qdrant.client import get_qdrant_client
from app.embeddings import encode_dense, encode_sparse, product_text
from app.qdrant.collection import COLLECTION_NAME, setup_products_collection

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
        print("Создание коллекции и индексов...")
        await setup_products_collection(client)

        points = [row_to_point(row) for row in rows]
        await client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)

        total = (await client.count(COLLECTION_NAME, exact=True)).count
        acme = (
            await client.count(
                COLLECTION_NAME,
                count_filter=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value="acme"))]
                ),
                exact=True
            )
        ).count
        beta = (
            await client.count(
                COLLECTION_NAME,
                count_filter=Filter(
                    must=[FieldCondition(key="tenant_id", match=MatchValue(value="beta"))]
                ),
                exact=True
            )
        ).count

        print(f"✅ Загружено точек: {total}")
        print(f"✅ tenant acme: {acme}, tenant beta: {beta}")
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
