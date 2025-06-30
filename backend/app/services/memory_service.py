import redis.asyncio as redis
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
from ..core.config import settings
from ..core.logging import logger


class MemoryService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.redis_url, db=settings.redis_db, decode_responses=True
        )
        self.default_ttl = 3600 * 24 * 7

    async def store_conversation(
        self, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> bool:
        try:
            key = f"conversation:{conversation_id}"
            data = {
                "messages": messages,
                "last_updated": datetime.utcnow().isoformat(),
                "message_count": len(messages),
            }

            await self.redis_client.setex(key, self.default_ttl, json.dumps(data))

            return True

        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}")
            return False

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        try:
            key = f"conversation:{conversation_id}"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            return None

    async def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        try:
            conversation = await self.get_conversation(conversation_id)

            if not conversation:
                conversation = {
                    "messages": [],
                    "last_updated": datetime.utcnow().isoformat(),
                    "message_count": 0,
                }

            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }

            conversation["messages"].append(message)
            conversation["last_updated"] = datetime.utcnow().isoformat()
            conversation["message_count"] = len(conversation["messages"])

            return await self.store_conversation(
                conversation_id, conversation["messages"]
            )

        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return False

    async def get_conversation_messages(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        try:
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                return conversation.get("messages", [])
            return []

        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        try:
            key = f"conversation:{conversation_id}"
            result = await self.redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return False

    async def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        try:
            key = f"summary:{conversation_id}"
            summary = await self.redis_client.get(key)
            return summary

        except Exception as e:
            logger.error(f"Error getting conversation summary: {str(e)}")
            return None

    async def store_conversation_summary(
        self, conversation_id: str, summary: str
    ) -> bool:
        try:
            key = f"summary:{conversation_id}"
            await self.redis_client.setex(key, self.default_ttl, summary)
            return True

        except Exception as e:
            logger.error(f"Error storing conversation summary: {str(e)}")
            return False

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        try:
            key = f"preferences:{user_id}"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)
            return {}

        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}

    async def store_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        try:
            key = f"preferences:{user_id}"
            await self.redis_client.setex(
                key, self.default_ttl, json.dumps(preferences)
            )
            return True

        except Exception as e:
            logger.error(f"Error storing user preferences: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        try:
            await self.redis_client.ping()
            return {
                "status": "healthy",
                "connection": "ok",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
