"""Modelo de Entrega."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, Enum, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeliveryStatus(str, PyEnum):
    """Status possíveis de uma entrega."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeliveryPriority(str, PyEnum):
    """Níveis de prioridade."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Delivery(Base):
    """Entrega a ser realizada."""

    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Informações do pedido
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Endereço de entrega
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Peso e volume
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    volume_m3: Mapped[float] = mapped_column(Float, default=0.0)

    # Prioridade e janela de tempo
    priority: Mapped[DeliveryPriority] = mapped_column(
        Enum(DeliveryPriority), default=DeliveryPriority.NORMAL
    )
    priority_score: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    time_window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status e tracking
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), default=DeliveryStatus.PENDING
    )
    sequence_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Confirmação
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    confirmed_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    confirmation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    receiver_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ETA
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Vinculação à rota
    route_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Delivery {self.order_number} [{self.priority.value}] - {self.status.value}>"
