"""Endpoints de Motoristas."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import RedisPubSub
from app.models.driver import Driver, DriverStatus
from app.api.schemas import (
    DriverCreate, DriverResponse, DriverLocationUpdate, DriverStatusEnum
)

router = APIRouter(prefix="/drivers", tags=["Motoristas"])


@router.get("/", response_model=list[DriverResponse])
async def list_drivers(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os motoristas."""
    query = select(Driver)
    if active_only:
        query = query.where(Driver.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=DriverResponse, status_code=201)
async def create_driver(
    data: DriverCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cadastra novo motorista."""
    driver = Driver(**data.model_dump())
    db.add(driver)
    await db.flush()
    await db.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna detalhes de um motorista."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    return driver



@router.patch("/{driver_id}/location")
async def update_driver_location(
    driver_id: uuid.UUID,
    data: DriverLocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza localização do motorista em tempo real."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")

    driver.current_lat = data.lat
    driver.current_lng = data.lng
    driver.last_location_update = datetime.utcnow()
    await db.flush()

    # Publicar atualização via Redis PubSub
    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_DRIVER_LOCATION,
        orjson.dumps({
            "driver_id": str(driver_id),
            "lat": data.lat,
            "lng": data.lng,
            "timestamp": datetime.utcnow().isoformat(),
            "status": driver.status.value,
        }).decode()
    )

    return {"status": "ok", "lat": data.lat, "lng": data.lng}


@router.patch("/{driver_id}/status")
async def update_driver_status(
    driver_id: uuid.UUID,
    new_status: DriverStatusEnum,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza status do motorista."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")

    driver.status = DriverStatus(new_status.value)
    await db.flush()

    import orjson
    await RedisPubSub.publish(
        RedisPubSub.CHANNEL_DRIVER_LOCATION,
        orjson.dumps({
            "driver_id": str(driver_id),
            "event": "status_change",
            "status": new_status.value,
            "timestamp": datetime.utcnow().isoformat(),
        }).decode()
    )

    return {"status": "ok", "new_status": new_status.value}
