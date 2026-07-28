"""Modelo de Motorista."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DriverStatus(str, PyEnum):
    """Status possíveis do motorista."""
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    DELIVERING = "delivering"
    RETURNING = "returning"
    OFFLINE = "offline"
    BREAK = "break"


class Driver(Base):
    """Motorista da frota."""

    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), default="van")

    # Localização em tempo real
    current_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus), default=DriverStatus.OFFLINE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Capacidade
    max_deliveries: Mapped[int] = mapped_column(default=20)
    max_weight_kg: Mapped[float] = mapped_column(Float, default=1000.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    routes = relationship("Route", back_populates="driver", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Driver {self.name} ({self.status.value})>"
