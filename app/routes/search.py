from fastapi.responses import HTMLResponse
from qdrant_client import AsyncQdrantClient
from fastapi import APIRouter, Depends, Query, Request

from app.qdrant.search import build_filter, hybrid_search
from app.routes.catalog import TENANTS, get_client, resolve_tenant

router = APIRouter()

CATEGORIES = [
    "laptop", "phone", "audio", "accessory",
    "kitchen", "home", "smart_home", "bedroom", "outdoor"
]


def parse_price(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    price = float(value)
    return price if price >= 0 else None


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = Query(default=""),
    tenant: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: str | None = Query(default=None),
    max_price: str | None = Query(default=None),
    in_stock: bool | None = Query(default=None),
    client: AsyncQdrantClient = Depends(get_client)
) -> HTMLResponse:
    tenant = resolve_tenant(tenant)
    query = q.strip()
    min_price = parse_price(min_price)
    max_price = parse_price(max_price)

    products: list[dict] = []
    if query:
        query_filter = build_filter(
            tenant=tenant,
            category=category or None,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        products = await hybrid_search(
            client,
            query=query,
            query_filter=query_filter
        )

    return request.app.state.templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "tenant": tenant,
            "tenants": TENANTS,
            "categories": CATEGORIES,
            "query": query,
            "category": category or "",
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock,
            "products": products
        }
    )
