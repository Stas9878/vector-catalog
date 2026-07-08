import re
import asyncio
from hashlib import blake2b
from functools import lru_cache

from qdrant_client.models import SparseVector


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


@lru_cache(maxsize=1)
def _get_dense_model():
    from sentence_transformers import SentenceTransformer
    from app.settings import get_settings

    return SentenceTransformer(get_settings().EMBEDDING_MODEL)


def encode_dense(text: str) -> list[float]:
    model = _get_dense_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


async def encode_dense_async(text: str) -> list[float]:
    return await asyncio.to_thread(encode_dense, text)


def _token_index(token: str, dim: int = 32768) -> int:
    digest = blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") % dim


def encode_sparse(text: str) -> SparseVector:
    weights: dict[int, float] = {}
    for token in _tokenize(text):
        idx = _token_index(token)
        weights[idx] = weights.get(idx, 0.0) + 1.0

    if not weights:
        return SparseVector(indices=[], values=[])

    indices = sorted(weights)
    values = [weights[i] for i in indices]
    return SparseVector(indices=indices, values=values)


def product_text(title: str, description: str) -> str:
    return f"{title}. {description}"
