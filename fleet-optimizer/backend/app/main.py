"""FastAPI Application - Fleet Route Optimizer."""

import asyncio
import uuid
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.drivers import router as drivers_router
from app.api.deliveries import router as deliveries_router
from app.api.routes import router as routes_router
from app.api.dashboard import router as dashboard_router
from app.websocket.manager import ws_manager

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de otimização de rotas para frotas logísticas com integração Waze em tempo real.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(drivers_router, prefix="/api/v1")
app.include_router(deliveries_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")



# === Lifecycle Events ===

@app.on_event("startup")
async def startup_event():
    """Inicializa serviços no startup."""
    logger.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    await ws_manager.start_background_listener()
    logger.info("Redis PubSub listener ativo")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup no shutdown."""
    from app.services.waze_service import waze_service
    await waze_service.close()
    logger.info("Aplicação encerrada")


# === WebSocket Endpoint ===

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Endpoint WebSocket para comunicação em tempo real.

    Clientes (dashboard, app motorista) conectam aqui para receber:
    - Atualizações de localização de motoristas
    - Mudanças de status de entregas
    - Re-roteamentos automáticos
    - Alertas de incidentes
    - Mudanças de prioridade
    """
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Processar mensagens do cliente (ex: heartbeat, location update)
            import orjson
            try:
                msg = orjson.loads(data)
                event = msg.get("event", "")

                if event == "ping":
                    await ws_manager.send_to_client(client_id, {
                        "event": "pong",
                        "connections": ws_manager.connection_count,
                    })
                elif event == "subscribe":
                    channel = msg.get("channel", "")
                    if channel:
                        if channel not in ws_manager.channel_subscriptions:
                            ws_manager.channel_subscriptions[channel] = set()
                        ws_manager.channel_subscriptions[channel].add(client_id)

            except Exception:
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)


# === Health Check ===

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "ws_connections": ws_manager.connection_count,
    }
