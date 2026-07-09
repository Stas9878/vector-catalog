from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    KeywordIndexParams,
    KeywordIndexType,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)

from app.qdrant.migrate import COLLECTION_ALIAS, ensure_alias, get_alias_target

COLLECTION_NAME = COLLECTION_ALIAS
INITIAL_PHYSICAL = "products_v1"
DENSE_DIM = 384


async def _delete_if_exists(
    client: AsyncQdrantClient,
    collection_name: str | None
) -> None:
    if collection_name and await client.collection_exists(collection_name):
        await client.delete_collection(collection_name)


async def create_physical_collection(
    client: AsyncQdrantClient,
    collection_name: str
) -> None:
    await client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE)
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams()
        }
    )


async def create_payload_indexes(
    client: AsyncQdrantClient,
    collection_name: str
) -> None:
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="tenant_id",
        field_schema=KeywordIndexParams(
            type=KeywordIndexType.KEYWORD,
            is_tenant=True
        ),
        wait=True
    )
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="price",
        field_schema=PayloadSchemaType.FLOAT,
        wait=True
    )
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="in_stock",
        field_schema=PayloadSchemaType.BOOL,
        wait=True
    )


async def setup_products_collection(
    client: AsyncQdrantClient,
    *,
    recreate: bool = False
) -> str:
    physical = INITIAL_PHYSICAL

    if recreate:
        target = await get_alias_target(client)
        for name in {physical, target, COLLECTION_ALIAS, "products_v2"}:
            await _delete_if_exists(client, name)

    if not await client.collection_exists(physical):
        await create_physical_collection(client, physical)
        await create_payload_indexes(client, physical)

    await ensure_alias(client, alias=COLLECTION_ALIAS, collection_name=physical)
    return physical
