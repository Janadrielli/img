"""Schemas Pydantic para validação de request/response."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# === Enums ===

class DeliveryStatusEnum(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeliveryPriorityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class DriverStatusEnum(str, Enum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    DELIVERING = "delivering"
    RETURNING = "returning"
    OFFLINE = "offline"
    BREAK = "break"


# === Driver Schemas ===

class DriverBase(BaseModel):
    name: str
    phone: str
    vehicle_plate: str
    vehicle_type: str = "van"
    max_deliveries: int = 20
    max_weight_kg: float = 1000.0


class DriverCreate(DriverBase):
    pass


class DriverLocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class DriverResponse(DriverBase):
    id: uuid.UUID
    status: DriverStatusEnum
    current_lat: float | None = None
    current_lng: float | None = None
    last_location_update: datetime | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# === Delivery Schemas ===

class DeliveryBase(BaseModel):
    order_number: str
    customer_name: str
    customer_phone: str | None = None
    description: str | None = None
    address: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    weight_kg: float = 0.0
    volume_m3: float = 0.0
    priority: DeliveryPriorityEnum = DeliveryPriorityEnum.NORMAL
    priority_score: int = Field(default=50, ge=0, le=100)
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None


class DeliveryCreate(DeliveryBase):
    pass


class DeliveryUpdate(BaseModel):
    priority: DeliveryPriorityEnum | None = None
    priority_score: int | None = Field(default=None, ge=0, le=100)
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    status: DeliveryStatusEnum | None = None


class DeliveryResponse(DeliveryBase):
    id: uuid.UUID
    status: DeliveryStatusEnum
    sequence_order: int | None = None
    estimated_arrival: datetime | None = None
    confirmed_at: datetime | None = None
    receiver_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True



# === Confirmation Schema ===

class DeliveryConfirmation(BaseModel):
    """Confirmação de recebimento pelo motorista."""
    receiver_name: str = Field(..., min_length=2, max_length=200)
    notes: str | None = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


# === Route Schemas ===

class RouteStopResponse(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    sequence_order: int
    distance_from_previous_km: float
    duration_from_previous_min: float
    eta: datetime | None = None
    is_completed: bool
    has_active_incident: bool
    waze_incidents_on_path: int

    class Config:
        from_attributes = True


class RouteResponse(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    status: str
    origin_lat: float
    origin_lng: float
    total_distance_km: float
    total_duration_minutes: float
    total_stops: int
    completed_stops: int
    optimization_score: float
    stops: list[RouteStopResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class RouteOptimizeRequest(BaseModel):
    """Request para otimizar/re-otimizar rota de um motorista."""
    driver_id: uuid.UUID
    delivery_ids: list[uuid.UUID] | None = None  # None = todas pendentes


class RoutePriorityOverride(BaseModel):
    """Gestor muda a ordem das entregas manualmente."""
    delivery_ids_ordered: list[uuid.UUID]
    reason: str = ""


# === Incident Schemas ===

class IncidentResponse(BaseModel):
    id: uuid.UUID
    lat: float
    lng: float
    incident_type: str
    severity: int
    description: str | None
    delay_seconds: int
    street: str | None
    is_active: bool
    reported_at: datetime

    class Config:
        from_attributes = True


# === WebSocket Messages ===

class WSMessage(BaseModel):
    """Mensagem genérica de WebSocket."""
    event: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# === Dashboard Stats ===

class DashboardStats(BaseModel):
    total_drivers: int
    active_drivers: int
    total_deliveries_today: int
    pending_deliveries: int
    in_progress_deliveries: int
    completed_deliveries: int
    active_incidents: int
    avg_eta_minutes: float
