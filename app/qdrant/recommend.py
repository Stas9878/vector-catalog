from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    RecommendInput,
    RecommendQuery,
)

from app.qdrant.collection import COLLECTION_NAME


def tenant_filter(tenant: str) -> Filter:
    return Filter(
        must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant))]
    )


async def recommend_similar(
    client: AsyncQdrantClient,
    *,
    tenant: str,
    product_id: int,
    limit: int = 4
) -> list[dict]:
    response = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=RecommendQuery(recommend=RecommendInput(positive=[product_id])),
        query_filter=tenant_filter(tenant),
        using="dense",
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    return [
        {"id": point.id, "score": point.score, **point.payload}
        for point in response.points
    ]


async def recommend_for_user(
    client: AsyncQdrantClient,
    *,
    tenant: str,
    positive_ids: list[int],
    negative_ids: list[int] | None = None,
    limit: int = 4
) -> list[dict]:
    if not positive_ids:
        return []

    response = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=RecommendQuery(
            recommend=RecommendInput(
                positive=positive_ids,
                negative=negative_ids or []
            )
        ),
        query_filter=tenant_filter(tenant),
        using="dense",
        limit=limit,
        with_payload=True,
        with_vectors=False
    )
    return [
        {"id": point.id, "score": point.score, **point.payload}
        for point in response.points
    ]
