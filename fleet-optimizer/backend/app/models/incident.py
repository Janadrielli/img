"""Modelo de Incidente (dados do Waze)."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, Enum, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IncidentType(str, PyEnum):
    """Tipos de incidente do Waze."""
    ACCIDENT = "accident"
    JAM = "jam"
    ROAD_CLOSED = "road_closed"
    HAZARD = "hazard"
    CONSTRUCTION = "construction"
    POLICE = "police"
    FLOOD = "flood"
    OTHER = "other"


class IncidentSeverity(int, PyEnum):
    """Severidade do incidente (1=leve, 5=crítico)."""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


class Incident(Base):
    """Incidente reportado pelo Waze que afeta rotas."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    waze_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)

    # Localização
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    street: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Classificação
    incident_type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType), nullable=False
    )
    severity: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Impacto
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    length_meters: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raio de influência (metros)
    influence_radius_m: Mapped[float] = mapped_column(Float, default=500.0)

    # Ativo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Incident {self.incident_type.value} severity={self.severity} at ({self.lat},{self.lng})>"
