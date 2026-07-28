"""WebSocket Connection Manager para comunicação em tempo real.

Gerencia conexões de clientes (dashboard, motoristas) e distribui
eventos em tempo real via Redis PubSub.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
import orjson

from app.core.redis_client import RedisPubSub, redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Gerenciador de conexões WebSocket."""

    def __init__(self):
        # Conexões ativas: {client_id: WebSocket}
        self.active_connections: dict[str, WebSocket] = {}
        # Subscrições por canal: {channel: set(client_ids)}
        self.channel_subscriptions: dict[str, set[str]] = {}
        self._pubsub_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket, client_id: str):
        """Aceita nova conexão WebSocket."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WS conectado: {client_id} (total: {len(self.active_connections)})")

        # Inscrever em todos os canais por padrão
        for channel in [
            RedisPubSub.CHANNEL_DELIVERY_UPDATE,
            RedisPubSub.CHANNEL_DRIVER_LOCATION,
            RedisPubSub.CHANNEL_ROUTE_CHANGE,
            RedisPubSub.CHANNEL_INCIDENT_ALERT,
            RedisPubSub.CHANNEL_PRIORITY_CHANGE,
        ]:
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(client_id)

    def disconnect(self, client_id: str):
        """Remove conexão desconectada."""
        self.active_connections.pop(client_id, None)
        for channel_subs in self.channel_subscriptions.values():
            channel_subs.discard(client_id)
        logger.info(f"WS desconectado: {client_id}")


    async def broadcast(self, channel: str, message: dict):
        """Envia mensagem para todos os clientes inscritos no canal."""
        subscribers = self.channel_subscriptions.get(channel, set())
        payload = orjson.dumps({
            "channel": channel,
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
        }).decode()

        disconnected = []
        for client_id in subscribers:
            ws = self.active_connections.get(client_id)
            if ws:
                try:
                    await ws.send_text(payload)
                except Exception:
                    disconnected.append(client_id)

        for cid in disconnected:
            self.disconnect(cid)

    async def send_to_client(self, client_id: str, message: dict):
        """Envia mensagem para um cliente específico."""
        ws = self.active_connections.get(client_id)
        if ws:
            try:
                payload = orjson.dumps(message).decode()
                await ws.send_text(payload)
            except Exception:
                self.disconnect(client_id)

    async def start_redis_listener(self):
        """Inicia listener de Redis PubSub para redistribuir eventos."""
        pubsub = redis_client.pubsub()
        channels = [
            RedisPubSub.CHANNEL_DELIVERY_UPDATE,
            RedisPubSub.CHANNEL_DRIVER_LOCATION,
            RedisPubSub.CHANNEL_ROUTE_CHANGE,
            RedisPubSub.CHANNEL_INCIDENT_ALERT,
            RedisPubSub.CHANNEL_PRIORITY_CHANGE,
        ]
        await pubsub.subscribe(*channels)

        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                try:
                    data = orjson.loads(message["data"])
                    await self.broadcast(channel, data)
                except Exception as e:
                    logger.error(f"Erro processando mensagem PubSub: {e}")

    async def start_background_listener(self):
        """Inicia listener em background task."""
        if self._pubsub_task is None or self._pubsub_task.done():
            self._pubsub_task = asyncio.create_task(self.start_redis_listener())
            logger.info("Redis PubSub listener iniciado")

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton global
ws_manager = ConnectionManager()
