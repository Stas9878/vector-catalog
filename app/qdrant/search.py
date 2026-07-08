from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
    Range,
)

from app.qdrant.collection import COLLECTION_NAME
from app.embeddings import encode_dense_async, encode_sparse

PREFETCH_LIMIT = 30


def build_filter(
    tenant: str,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None
) -> Filter:
    must: list[FieldCondition] = [
        FieldCondition(key="tenant_id", match=MatchValue(value=tenant))
    ]

    if category:
        must.append(FieldCondition(key="category", match=MatchValue(value=category)))

    if min_price is not None or max_price is not None:
        must.append(
            FieldCondition(key="price", range=Range(gte=min_price, lte=max_price))
        )

    if in_stock is not None:
        must.append(FieldCondition(key="in_stock", match=MatchValue(value=in_stock)))

    return Filter(must=must)


async def hybrid_search(
    client: AsyncQdrantClient,
    *,
    query: str,
    query_filter: Filter,
    limit: int = 12
) -> list[dict]:
    dense = await encode_dense_async(query)
    sparse = encode_sparse(query)

    response = await client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(
                query=dense,
                using="dense",
                filter=query_filter,
                limit=PREFETCH_LIMIT
            ),
            Prefetch(
                query=sparse,
                using="sparse",
                filter=query_filter,
                limit=PREFETCH_LIMIT
            )
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=limit,
        with_payload=True,
        with_vectors=False
    )

    return [
        {"id": point.id, "score": point.score, **point.payload}
        for point in response.points
    ]
