from fastapi.responses import HTMLResponse
from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.db.session import get_db_session
from app.qdrant.collection import COLLECTION_NAME
from app.db.events import get_recent_product_ids, record_event
from app.routes.catalog import TENANTS, get_client, resolve_tenant
from app.qdrant.recommend import recommend_for_user, recommend_similar

router = APIRouter()


@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_page(
    request: Request,
    product_id: int,
    tenant: str | None = Query(default=None),
    client: AsyncQdrantClient = Depends(get_client),
    db: AsyncSession = Depends(get_db_session)
) -> HTMLResponse:
    tenant = resolve_tenant(tenant)

    points = await client.retrieve(
        collection_name=COLLECTION_NAME,
        ids=[product_id],
        with_payload=True,
        with_vectors=False
    )
    if not points:
        raise HTTPException(status_code=404, detail="Товар не найден")

    point = points[0]
    if point.payload.get("tenant_id") != tenant:
        raise HTTPException(status_code=404, detail="Товар не найден")

    product = {"id": point.id, **point.payload}

    await record_event(db, tenant, product_id, "view")

    similar = await recommend_similar(
        client, tenant=tenant, product_id=product_id, limit=4
    )

    recent_ids = await get_recent_product_ids(db, tenant, limit=5)
    history_ids = [pid for pid in recent_ids if pid != product_id][:3]
    for_you = await recommend_for_user(
        client,
        tenant=tenant,
        positive_ids=history_ids,
        negative_ids=[product_id],
        limit=4
    )

    return request.app.state.templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "tenant": tenant,
            "tenants": TENANTS,
            "product": product,
            "similar": similar,
            "for_you": for_you,
            "has_history": bool(history_ids)
        }
    )
