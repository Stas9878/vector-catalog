from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    CreateAlias,
    CreateAliasOperation,
    DeleteAlias,
    DeleteAliasOperation,
)

COLLECTION_ALIAS = "products"
PHYSICAL_PREFIX = "products_v"


async def get_alias_target(
    client: AsyncQdrantClient,
    alias: str = COLLECTION_ALIAS
) -> str | None:
    aliases = await client.get_aliases()
    for item in aliases.aliases:
        if item.alias_name == alias:
            return item.collection_name
    return None


async def ensure_alias(
    client: AsyncQdrantClient,
    *,
    alias: str,
    collection_name: str
) -> None:
    target = await get_alias_target(client, alias)
    if target == collection_name:
        return

    if target is None:
        await client.update_collection_aliases(
            change_aliases_operations=[
                CreateAliasOperation(
                    create_alias=CreateAlias(
                        collection_name=collection_name,
                        alias_name=alias
                    )
                )
            ]
        )
        return

    await swap_alias(client, alias=alias, collection_name=collection_name)


async def swap_alias(
    client: AsyncQdrantClient,
    *,
    alias: str,
    collection_name: str
) -> None:
    target = await get_alias_target(client, alias)
    operations = []
    if target is not None:
        operations.append(
            DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=alias))
        )
    operations.append(
        CreateAliasOperation(
            create_alias=CreateAlias(
                collection_name=collection_name,
                alias_name=alias
            )
        )
    )
    await client.update_collection_aliases(change_aliases_operations=operations)


def next_physical_name(current: str | None) -> str:
    if current is None or not current.startswith(PHYSICAL_PREFIX):
        return f"{PHYSICAL_PREFIX}1"

    version = int(current.removeprefix(PHYSICAL_PREFIX))
    return f"{PHYSICAL_PREFIX}{version + 1}"
