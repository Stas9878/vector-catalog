from fastapi.responses import HTMLResponse
from qdrant_client import AsyncQdrantClient
from fastapi import APIRouter, Depends, Query, Request
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.settings import get_settings
from app.qdrant.collection import COLLECTION_NAME

router = APIRouter()

TENANTS = ["acme", "beta"]
PAGE_SIZE = 8


def get_client(request: Request) -> AsyncQdrantClient:
    return request.app.state.qdrant


def resolve_tenant(tenant: str | None) -> str:
    if tenant in TENANTS:
        return tenant
    return get_settings().DEFAULT_TENANT


@router.get("/", response_class=HTMLResponse)
async def catalog(
    request: Request,
    tenant: str | None = Query(default=None),
    offset: int | None = Query(default=None),
    client: AsyncQdrantClient = Depends(get_client)
) -> HTMLResponse:
    tenant = resolve_tenant(tenant)

    points, next_offset = await client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant))]
        ),
        limit=PAGE_SIZE,
        offset=offset,
        with_payload=True,
        with_vectors=False,
    )

    products = [{"id": point.id, **point.payload} for point in points]

    return request.app.state.templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "tenant": tenant,
            "tenants": TENANTS,
            "products": products,
            "next_offset": next_offset
        }
    )
