"""Endpoints de Entregas e Confirmação."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import RedisPubSub
from app.models.delivery import Delivery, DeliveryStatus, DeliveryPriority
from app.models.driver import Driver
from app.models.route import Route, RouteStop, RouteStatus
from app.api.schemas import (
    DeliveryCreate, DeliveryResponse, DeliveryUpdate,
    DeliveryConfirmation, DeliveryStatusEnum, DeliveryPriorityEnum
)
from app.services.route_optimizer import route_optimizer, DeliveryPoint

router = APIRouter(prefix="/deliveries", tags=["Entregas"])


@router.get("/", response_model=list[DeliveryResponse])
async def list_deliveries(
    status: DeliveryStatusEnum | None = None,
    priority: DeliveryPriorityEnum | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Lista entregas com filtros opcionais."""
    query = select(Delivery).order_by(
        Delivery.priority_score.desc(), Delivery.created_at
    )
    if status:
        query = query.where(Delivery.status == DeliveryStatus(status.value))
    if priority:
        query = query.where(Delivery.priority == DeliveryPriority(priority.value))
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()



@router.post("/", response_model=DeliveryResponse, status_code=201)
async def create_delivery(
    data: DeliveryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria nova entrega."""
    delivery = Delivery(**data.model_dump())
    db.add(delivery)
    await db.flush()
    await db.refresh(delivery)

    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_DELIVERY_UPDATE,
        orjson.dumps({
            "event": "new_delivery",
            "delivery_id": str(delivery.id),
            "priority": delivery.priority.value,
            "address": delivery.address,
        }).decode()
    )
    return delivery


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(
    delivery_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna detalhes de uma entrega."""
    delivery = await db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")
    return delivery


@router.patch("/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(
    delivery_id: uuid.UUID,
    data: DeliveryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza entrega (prioridade, status, janela de tempo)."""
    delivery = await db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "priority":
                setattr(delivery, field, DeliveryPriority(value.value))
            elif field == "status":
                setattr(delivery, field, DeliveryStatus(value.value))
            else:
                setattr(delivery, field, value)

    await db.flush()
    await db.refresh(delivery)

    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_PRIORITY_CHANGE,
        orjson.dumps({
            "event": "delivery_updated",
            "delivery_id": str(delivery_id),
            "changes": update_data,
        }).decode()
    )
    return delivery



@router.post("/{delivery_id}/confirm")
async def confirm_delivery(
    delivery_id: uuid.UUID,
    confirmation: DeliveryConfirmation,
    db: AsyncSession = Depends(get_db),
):
    """Confirma recebimento de entrega pelo motorista.

    Gatilho: re-otimiza rota automaticamente após confirmação.
    """
    delivery = await db.get(Delivery, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega não encontrada")

    if delivery.status == DeliveryStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Entrega já confirmada")

    # Registrar confirmação
    delivery.status = DeliveryStatus.CONFIRMED
    delivery.confirmed_at = datetime.utcnow()
    delivery.confirmed_lat = confirmation.lat
    delivery.confirmed_lng = confirmation.lng
    delivery.confirmation_notes = confirmation.notes
    delivery.receiver_name = confirmation.receiver_name
    delivery.actual_arrival = datetime.utcnow()

    # Marcar stop da rota como completa
    if delivery.route_stop_id:
        stop = await db.get(RouteStop, delivery.route_stop_id)
        if stop:
            stop.is_completed = True
            stop.arrived_at = datetime.utcnow()

            # Atualizar contagem da rota
            route = await db.get(Route, stop.route_id)
            if route:
                route.completed_stops += 1

    await db.flush()

    # Publicar evento de confirmação
    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_DELIVERY_UPDATE,
        orjson.dumps({
            "event": "delivery_confirmed",
            "delivery_id": str(delivery_id),
            "receiver_name": confirmation.receiver_name,
            "lat": confirmation.lat,
            "lng": confirmation.lng,
            "timestamp": datetime.utcnow().isoformat(),
        }).decode()
    )

    # Disparar re-otimização automática
    await _trigger_re_optimization(delivery, confirmation, db)

    return {
        "status": "confirmed",
        "delivery_id": str(delivery_id),
        "confirmed_at": delivery.confirmed_at.isoformat(),
        "message": "Entrega confirmada. Rota re-otimizada automaticamente.",
    }


async def _trigger_re_optimization(
    delivery: Delivery,
    confirmation: DeliveryConfirmation,
    db: AsyncSession,
):
    """Dispara re-otimização da rota do motorista após confirmação."""
    if not delivery.route_stop_id:
        return

    stop = await db.get(RouteStop, delivery.route_stop_id)
    if not stop:
        return

    route = await db.get(Route, stop.route_id)
    if not route or route.status != RouteStatus.ACTIVE:
        return

    # Buscar entregas restantes na rota
    remaining_stops_q = select(RouteStop).where(
        RouteStop.route_id == route.id,
        RouteStop.is_completed == False,
    ).order_by(RouteStop.sequence_order)
    result = await db.execute(remaining_stops_q)
    remaining_stops = result.scalars().all()

    if not remaining_stops:
        route.status = RouteStatus.COMPLETED
        route.completed_at = datetime.utcnow()
        await db.flush()
        return

    # Converter para DeliveryPoints
    delivery_points = []
    for rs in remaining_stops:
        del_obj = await db.get(Delivery, rs.delivery_id)
        if del_obj:
            delivery_points.append(DeliveryPoint(
                id=str(del_obj.id),
                lat=del_obj.lat,
                lng=del_obj.lng,
                priority_score=del_obj.priority_score,
                time_window_start=del_obj.time_window_start,
                time_window_end=del_obj.time_window_end,
            ))

    # Re-otimizar a partir da posição atual do motorista
    optimized = await route_optimizer.re_optimize_after_delivery(
        driver_lat=confirmation.lat,
        driver_lng=confirmation.lng,
        remaining_deliveries=delivery_points,
    )

    # Atualizar sequências na rota
    for opt_stop in optimized.stops:
        for rs in remaining_stops:
            if str(rs.delivery_id) == opt_stop.delivery_id:
                rs.sequence_order = opt_stop.sequence
                rs.distance_from_previous_km = opt_stop.distance_from_previous_km
                rs.duration_from_previous_min = opt_stop.duration_from_previous_min
                rs.waze_incidents_on_path = opt_stop.incidents_nearby
                break

    route.total_distance_km = optimized.total_distance_km
    route.total_duration_minutes = optimized.total_duration_min
    route.optimization_score = optimized.optimization_score
    route.last_optimized_at = datetime.utcnow()
    await db.flush()

    # Publicar nova rota via PubSub
    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_ROUTE_CHANGE,
        orjson.dumps({
            "event": "route_re_optimized",
            "route_id": str(route.id),
            "driver_id": str(route.driver_id),
            "remaining_stops": len(optimized.stops),
            "total_distance_km": optimized.total_distance_km,
            "total_duration_min": optimized.total_duration_min,
        }).decode()
    )
