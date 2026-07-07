from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    KeywordIndexParams,
    KeywordIndexType,
    PayloadSchemaType,
    SparseVectorParams,
    VectorParams,
)

COLLECTION_NAME = "products"
DENSE_DIM = 384


async def recreate_products_collection(client: AsyncQdrantClient) -> None:
    if await client.collection_exists(COLLECTION_NAME):
        await client.delete_collection(COLLECTION_NAME)

    await client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE)
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams()
        }
    )


async def create_payload_indexes(client: AsyncQdrantClient) -> None:
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="tenant_id",
        field_schema=KeywordIndexParams(
            type=KeywordIndexType.KEYWORD,
            is_tenant=True
        ),
        wait=True
    )
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
        wait=True
    )
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="price",
        field_schema=PayloadSchemaType.FLOAT,
        wait=True
    )
    await client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="in_stock",
        field_schema=PayloadSchemaType.BOOL,
        wait=True
    )


async def setup_products_collection(client: AsyncQdrantClient) -> None:
    await recreate_products_collection(client)
    await create_payload_indexes(client)
