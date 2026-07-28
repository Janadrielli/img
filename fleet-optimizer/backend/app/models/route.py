"""Modelos de Rota e Paradas."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, Enum, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RouteStatus(str, PyEnum):
    """Status da rota."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Route(Base):
    """Rota atribuída a um motorista."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False
    )
    status: Mapped[RouteStatus] = mapped_column(
        Enum(RouteStatus), default=RouteStatus.PLANNED
    )

    # Origem
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    origin_address: Mapped[str] = mapped_column(String(500), default="Base")

    # Métricas
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    total_duration_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    total_stops: Mapped[int] = mapped_column(Integer, default=0)
    completed_stops: Mapped[int] = mapped_column(Integer, default=0)

    # Otimização
    last_optimized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    optimization_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    driver = relationship("Driver", back_populates="routes", lazy="selectin")
    stops = relationship(
        "RouteStop", back_populates="route", lazy="selectin",
        order_by="RouteStop.sequence_order"
    )

    def __repr__(self) -> str:
        return f"<Route {self.id} - {self.status.value} ({self.completed_stops}/{self.total_stops})>"


class RouteStop(Base):
    """Parada individual dentro de uma rota."""

    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False
    )
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deliveries.id"), nullable=False
    )

    # Sequência na rota
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Métricas deste trecho
    distance_from_previous_km: Mapped[float] = mapped_column(Float, default=0.0)
    duration_from_previous_min: Mapped[float] = mapped_column(Float, default=0.0)
    eta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Waze data
    waze_route_time_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    waze_incidents_on_path: Mapped[int] = mapped_column(Integer, default=0)
    has_active_incident: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    departed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    route = relationship("Route", back_populates="stops")

    def __repr__(self) -> str:
        return f"<RouteStop #{self.sequence_order} route={self.route_id}>"
