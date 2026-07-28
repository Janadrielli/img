"""Endpoints do Dashboard."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.driver import Driver, DriverStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.incident import Incident
from app.api.schemas import DashboardStats, IncidentResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """Retorna estatísticas em tempo real do dashboard."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)

    # Drivers
    total_drivers = await db.scalar(select(func.count(Driver.id)))
    active_drivers = await db.scalar(
        select(func.count(Driver.id)).where(
            Driver.status.in_([DriverStatus.EN_ROUTE, DriverStatus.DELIVERING])
        )
    )

    # Deliveries
    total_today = await db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.created_at >= today_start
        )
    )
    pending = await db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.status == DeliveryStatus.PENDING
        )
    )
    in_progress = await db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.status.in_([
                DeliveryStatus.ASSIGNED,
                DeliveryStatus.EN_ROUTE,
                DeliveryStatus.ARRIVED,
            ])
        )
    )
    completed = await db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.status.in_([
                DeliveryStatus.DELIVERED,
                DeliveryStatus.CONFIRMED,
            ])
        )
    )

    # Incidents
    active_incidents = await db.scalar(
        select(func.count(Incident.id)).where(Incident.is_active == True)
    )

    return DashboardStats(
        total_drivers=total_drivers or 0,
        active_drivers=active_drivers or 0,
        total_deliveries_today=total_today or 0,
        pending_deliveries=pending or 0,
        in_progress_deliveries=in_progress or 0,
        completed_deliveries=completed or 0,
        active_incidents=active_incidents or 0,
        avg_eta_minutes=0.0,
    )


@router.get("/incidents", response_model=list[IncidentResponse])
async def get_active_incidents(
    db: AsyncSession = Depends(get_db),
):
    """Retorna incidentes ativos para exibição no mapa."""
    query = select(Incident).where(
        Incident.is_active == True
    ).order_by(Incident.severity.desc())
    result = await db.execute(query)
    return result.scalars().all()
