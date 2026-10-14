import json
import uuid
import logging
from typing import List, Optional, Dict, Any
import redis.asyncio as aioredis
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest
from app.config import settings

logger = logging.getLogger("lisa.memory")


class MemoryService:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.qdrant_client: Optional[AsyncQdrantClient] = None
        self.collection_name: str = "lisa_user_memory"
        self._qdrant_initialized: bool = False

    # -----------------------------------------------------------------------
    # Redis Session & Short-Term Memory
    # -----------------------------------------------------------------------
    async def get_redis(self) -> aioredis.Redis:
        if self.redis_client is None:
            self.redis_client = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
        return self.redis_client

    async def get_chat_history(self, session_id: str, limit: int = 10) -> List[dict]:
        """Fetch the last N messages for the session from Redis."""
        try:
            r = await self.get_redis()
            raw_history = await r.lrange(f"chat_history:{session_id}", -limit, -1)
            return [json.loads(item) for item in raw_history]
        except Exception as e:
            logger.warning(f"Could not fetch chat history from Redis: {e}")
            return []

    async def append_chat_message(self, session_id: str, role: str, content: str):
        """Append a message to the session's chat history with a TTL (24h)."""
        try:
            r = await self.get_redis()
            key = f"chat_history:{session_id}"
            message = json.dumps({"role": role, "content": content})
            await r.rpush(key, message)
            await r.ltrim(key, -30, -1)  # retain last 30 messages
            await r.expire(key, 86400)   # 24 hours TTL
        except Exception as e:
            logger.warning(f"Could not append chat message to Redis: {e}")

    async def set_pending_action(self, session_id: str, action_data: dict, ttl: int = 300):
        """Save a pending action requiring PIN authorization (5 min TTL)."""
        try:
            r = await self.get_redis()
            key = f"pending_auth:{session_id}"
            await r.setex(key, ttl, json.dumps(action_data))
        except Exception as e:
            logger.error(f"Error setting pending action in Redis: {e}")

    async def get_pending_action(self, session_id: str) -> Optional[dict]:
        """Retrieve any pending action requiring PIN authorization."""
        try:
            r = await self.get_redis()
            key = f"pending_auth:{session_id}"
            data = await r.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error fetching pending action from Redis: {e}")
            return None

    async def clear_pending_action(self, session_id: str):
        """Clear pending action once verified or cancelled."""
        try:
            r = await self.get_redis()
            await r.delete(f"pending_auth:{session_id}")
        except Exception as e:
            logger.error(f"Error clearing pending action: {e}")

    # -----------------------------------------------------------------------
    # Qdrant Long-Term Semantic Vector Memory Layer
    # -----------------------------------------------------------------------
    async def get_qdrant(self) -> AsyncQdrantClient:
        if self.qdrant_client is None:
            self.qdrant_client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY or None,
            )
        return self.qdrant_client

    async def ensure_qdrant_collection(self):
        """Ensure the semantic memory collection exists in Qdrant (vector size 768)."""
        if self._qdrant_initialized:
            return
        try:
            client = await self.get_qdrant()
            collections = await client.get_collections()
            collection_names = [col.name for col in collections.collections]
            if self.collection_name not in collection_names:
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest.VectorParams(
                        size=768,  # Size for Gemini text-embedding-004
                        distance=rest.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}'")
            self._qdrant_initialized = True
        except Exception as e:
            logger.warning(f"Could not connect or initialize Qdrant collection: {e}")

    async def save_semantic_memory(
        self,
        user_id: str,
        text: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Store semantic memory vector with user payload in Qdrant."""
        if not vector:
            return
        try:
            await self.ensure_qdrant_collection()
            client = await self.get_qdrant()
            point_id = str(uuid.uuid4())
            payload = {
                "user_id": user_id,
                "text": text,
                **(metadata or {}),
            }
            await client.upsert(
                collection_name=self.collection_name,
                points=[
                    rest.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.info(f"Saved long-term memory for user '{user_id}': {text[:40]}...")
        except Exception as e:
            logger.error(f"Error saving semantic memory to Qdrant: {e}")

    async def search_semantic_memories(
        self,
        user_id: str,
        query_vector: List[float],
        limit: int = 3,
    ) -> List[str]:
        """Search Qdrant for relevant semantic memories matching query vector."""
        if not query_vector:
            return []
        try:
            await self.ensure_qdrant_collection()
            client = await self.get_qdrant()
            search_result = await client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="user_id",
                            match=rest.MatchValue(value=user_id),
                        )
                    ]
                ),
                limit=limit,
            )
            return [hit.payload.get("text", "") for hit in search_result if hit.payload]
        except Exception as e:
            logger.warning(f"Could not search Qdrant semantic memories: {e}")
            return []


memory_service = MemoryService()
