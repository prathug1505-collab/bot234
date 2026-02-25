"""
Semantic Cache Service
Caches AI responses in Redis to avoid redundant (expensive) inference calls.
Simple exact-match cache — upgrade to vector similarity cache for production.
"""

import hashlib
import json
from typing import Optional

from app.services.redis_client import redis_client

CACHE_TTL = 3600  # 1 hour


class SemanticCache:
    def _key(self, prompt: str) -> str:
        """SHA-256 hash of the prompt as the cache key."""
        h = hashlib.sha256(prompt.strip().lower().encode()).hexdigest()
        return f"ai_cache:{h}"

    async def get(self, prompt: str) -> Optional[str]:
        try:
            val = await redis_client.client.get(self._key(prompt))
            return json.loads(val) if val else None
        except Exception:
            return None  # Cache miss on error — fail open

    async def set(self, prompt: str, response: str) -> None:
        try:
            await redis_client.client.set(
                self._key(prompt),
                json.dumps(response),
                ex=CACHE_TTL,
            )
        except Exception:
            pass  # Non-critical — just skip caching

    async def invalidate(self, prompt: str) -> None:
        try:
            await redis_client.client.delete(self._key(prompt))
        except Exception:
            pass


# ---
# 💡 Upgrade path: Vector Similarity Cache
# Instead of exact SHA-256 matching, embed the prompt and search for
# semantically similar cached responses using Pinecone or pgvector.
# This can cache ~80% of user queries even when phrased differently.
# ---
