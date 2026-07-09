from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Event


async def record_event(
    session: AsyncSession,
    tenant_id: str,
    product_id: int,
    event_type: str
) -> None:
    session.add(
        Event(
            tenant_id=tenant_id,
            product_id=product_id,
            event_type=event_type
        )
    )
    await session.commit()


async def get_recent_product_ids(
    session: AsyncSession,
    tenant_id: str,
    limit: int = 5
) -> list[int]:
    stmt = (
        select(Event.product_id)
        .where(
            Event.tenant_id == tenant_id,
            Event.event_type == "view"
        )
        .order_by(Event.id.desc())
        .limit(limit * 3)
    )
    rows = (await session.execute(stmt)).scalars().all()

    seen: set[int] = set()
    result: list[int] = []
    for product_id in rows:
        if product_id in seen:
            continue
        seen.add(product_id)
        result.append(product_id)
        if len(result) >= limit:
            break
    return result
