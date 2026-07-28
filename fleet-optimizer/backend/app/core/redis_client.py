"""Cliente Redis para cache e PubSub em tempo real."""

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    encoding="utf-8",
)


class RedisPubSub:
    """Gerenciador de PubSub para eventos em tempo real."""

    CHANNEL_DELIVERY_UPDATE = "delivery:update"
    CHANNEL_DRIVER_LOCATION = "driver:location"
    CHANNEL_ROUTE_CHANGE = "route:change"
    CHANNEL_INCIDENT_ALERT = "incident:alert"
    CHANNEL_PRIORITY_CHANGE = "priority:change"

    @staticmethod
    async def publish(channel: str, message: str) -> None:
        """Publica mensagem em um canal."""
        await redis_client.publish(channel, message)

    @staticmethod
    async def subscribe(channel: str):
        """Assina um canal e retorna o subscriber."""
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    @staticmethod
    async def cache_set(key: str, value: str, ttl_seconds: int = 60) -> None:
        """Armazena valor no cache com TTL."""
        await redis_client.set(key, value, ex=ttl_seconds)

    @staticmethod
    async def cache_get(key: str) -> str | None:
        """Recupera valor do cache."""
        return await redis_client.get(key)
