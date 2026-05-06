# ============================================
# Nexus-Graph AI Service — Redis Subscriber
# ============================================
# Listens on Redis Pub/Sub channels for events
# published by the Node.js gateway and feeds
# them into the LangGraph extraction pipeline.
# ============================================

from __future__ import annotations
import asyncio
import json
from typing import Any, Callable, Awaitable
import redis.asyncio as aioredis
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("nexus-ai.redis")


class RedisSubscriber:
    """Async Redis Pub/Sub subscriber that routes events to a handler."""

    def __init__(self):
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._task: asyncio.Task | None = None
        self._handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None

    async def connect(self) -> None:
        s = get_settings()
        self._redis = aioredis.from_url(s.redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("✅ Redis subscriber connected", extra={"meta": s.redis_url})

    async def disconnect(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("Redis subscriber disconnected")

    def set_handler(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._handler = handler

    async def start_listening(self) -> None:
        """Subscribe to all event channels and begin consuming."""
        s = get_settings()
        channels = [
            s.channel_slack,
            s.channel_github,
            s.channel_jira,
        ]
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(*channels)
        logger.info(f"📡 Subscribed to channels: {', '.join(channels)}")
        self._task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """Main consumer loop — reads messages and dispatches to handler."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                channel = message["channel"]
                try:
                    event = json.loads(message["data"])
                    if event.get("metadata", {}).get("ai_route") == "grpc_primary":
                        logger.debug(
                            f"Skipping Redis AI processing for gRPC-primary event {event.get('event_id', '?')[:12]}"
                        )
                        continue
                    logger.event(
                        f"Received event on [{channel}]",
                        meta=f"id={event.get('event_id', '?')[:12]}"
                    )
                    if self._handler:
                        await self._handler(event)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON on {channel}: {e}")
                except Exception as e:
                    logger.error(f"Handler error for {channel}: {e}")
        except asyncio.CancelledError:
            logger.info("Redis listener loop cancelled")
        except Exception as e:
            logger.error(f"Redis listener crashed: {e}")

    async def publish(self, channel: str, data: dict[str, Any]) -> None:
        """Publish a message (used for conflict-events, decision-events)."""
        if self._redis:
            await self._redis.publish(channel, json.dumps(data, default=str))
            logger.event(f"Published to [{channel}]")
