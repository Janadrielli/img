"""Endpoints de Rotas e Otimização."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import RedisPubSub
from app.models.driver import Driver
from app.models.delivery import Delivery, DeliveryStatus
from app.models.route import Route, RouteStop, RouteStatus
from app.api.schemas import (
    RouteResponse, RouteOptimizeRequest, RoutePriorityOverride
)
from app.services.route_optimizer import route_optimizer, DeliveryPoint

router = APIRouter(prefix="/routes", tags=["Rotas"])


@router.get("/", response_model=list[RouteResponse])
async def list_routes(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Lista rotas ativas."""
    query = select(Route)
    if active_only:
        query = query.where(
            Route.status.in_([RouteStatus.PLANNED, RouteStatus.ACTIVE])
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna detalhes de uma rota com suas paradas."""
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return route



@router.post("/optimize", response_model=RouteResponse, status_code=201)
async def optimize_route(
    request: RouteOptimizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cria rota otimizada para um motorista.

    Se delivery_ids não fornecido, usa todas as entregas pendentes.
    """
    driver = await db.get(Driver, request.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    if not driver.current_lat or not driver.current_lng:
        raise HTTPException(
            status_code=400,
            detail="Motorista sem localização. Atualize a posição primeiro."
        )

    # Buscar entregas
    if request.delivery_ids:
        deliveries = []
        for did in request.delivery_ids:
            d = await db.get(Delivery, did)
            if d and d.status == DeliveryStatus.PENDING:
                deliveries.append(d)
    else:
        query = select(Delivery).where(
            Delivery.status == DeliveryStatus.PENDING
        ).limit(driver.max_deliveries)
        result = await db.execute(query)
        deliveries = list(result.scalars().all())

    if not deliveries:
        raise HTTPException(status_code=400, detail="Nenhuma entrega pendente")

    # Converter para DeliveryPoints
    points = [
        DeliveryPoint(
            id=str(d.id),
            lat=d.lat,
            lng=d.lng,
            priority_score=d.priority_score,
            time_window_start=d.time_window_start,
            time_window_end=d.time_window_end,
            weight_kg=d.weight_kg,
        )
        for d in deliveries
    ]

    # Otimizar
    optimized = await route_optimizer.optimize_route(
        origin_lat=driver.current_lat,
        origin_lng=driver.current_lng,
        deliveries=points,
    )

    # Criar rota no banco
    route = Route(
        driver_id=driver.id,
        status=RouteStatus.ACTIVE,
        origin_lat=driver.current_lat,
        origin_lng=driver.current_lng,
        total_distance_km=optimized.total_distance_km,
        total_duration_minutes=optimized.total_duration_min,
        total_stops=len(optimized.stops),
        completed_stops=0,
        optimization_score=optimized.optimization_score,
        last_optimized_at=datetime.utcnow(),
    )
    db.add(route)
    await db.flush()

    # Criar stops
    for opt_stop in optimized.stops:
        stop = RouteStop(
            route_id=route.id,
            delivery_id=uuid.UUID(opt_stop.delivery_id),
            sequence_order=opt_stop.sequence,
            distance_from_previous_km=opt_stop.distance_from_previous_km,
            duration_from_previous_min=opt_stop.duration_from_previous_min,
            waze_incidents_on_path=opt_stop.incidents_nearby,
        )
        db.add(stop)
        await db.flush()

        # Vincular delivery à rota
        for d in deliveries:
            if str(d.id) == opt_stop.delivery_id:
                d.status = DeliveryStatus.ASSIGNED
                d.route_stop_id = stop.id
                d.sequence_order = opt_stop.sequence
                break

    await db.flush()
    await db.refresh(route)

    # Publicar evento
    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_ROUTE_CHANGE,
        orjson.dumps({
            "event": "route_created",
            "route_id": str(route.id),
            "driver_id": str(driver.id),
            "total_stops": len(optimized.stops),
            "total_distance_km": optimized.total_distance_km,
        }).decode()
    )

    return route



@router.post("/{route_id}/override-priority")
async def override_route_priority(
    route_id: uuid.UUID,
    override: RoutePriorityOverride,
    db: AsyncSession = Depends(get_db),
):
    """Gestor sobrescreve a ordem das entregas manualmente.

    Permite reordenar paradas conforme demandas urgentes.
    """
    route = await db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    if route.status not in [RouteStatus.PLANNED, RouteStatus.ACTIVE]:
        raise HTTPException(status_code=400, detail="Rota não pode ser alterada")

    # Reordenar stops conforme lista do gestor
    stops_q = select(RouteStop).where(
        RouteStop.route_id == route_id,
        RouteStop.is_completed == False,
    )
    result = await db.execute(stops_q)
    stops = {str(s.delivery_id): s for s in result.scalars().all()}

    for idx, delivery_id in enumerate(override.delivery_ids_ordered, start=1):
        stop = stops.get(str(delivery_id))
        if stop:
            stop.sequence_order = idx

    route.last_optimized_at = datetime.utcnow()
    await db.flush()

    # Publicar evento
    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_ROUTE_CHANGE,
        orjson.dumps({
            "event": "route_priority_override",
            "route_id": str(route_id),
            "driver_id": str(route.driver_id),
            "reason": override.reason,
            "new_order": [str(d) for d in override.delivery_ids_ordered],
        }).decode()
    )

    return {
        "status": "ok",
        "message": "Ordem das entregas atualizada pelo gestor.",
        "route_id": str(route_id),
        "new_order": [str(d) for d in override.delivery_ids_ordered],
    }


@router.get("/driver/{driver_id}/active", response_model=RouteResponse | None)
async def get_driver_active_route(
    driver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna a rota ativa do motorista."""
    query = select(Route).where(
        Route.driver_id == driver_id,
        Route.status == RouteStatus.ACTIVE,
    ).order_by(Route.created_at.desc()).limit(1)
    result = await db.execute(query)
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(
            status_code=404, detail="Nenhuma rota ativa para este motorista"
        )
    return route
