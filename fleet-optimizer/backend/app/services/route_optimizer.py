"""Engine de otimização de rotas para frota logística.

Algoritmo: Nearest-Neighbor com penalização por incidentes Waze.
- Calcula próxima parada mais próxima considerando distância + tráfego
- Penaliza rotas com incidentes ativos (severidade >= threshold)
- Respeita janelas de tempo e prioridades
- Re-otimiza automaticamente após cada entrega confirmada
"""

import logging
import math
from datetime import datetime
from dataclasses import dataclass, field

from geopy.distance import geodesic

from app.core.config import get_settings
from app.services.waze_service import waze_service, WazeIncident

logger = logging.getLogger(__name__)
settings = get_settings()



@dataclass
class DeliveryPoint:
    """Ponto de entrega para otimização."""
    id: str
    lat: float
    lng: float
    priority_score: int = 50  # 0-100 (100 = mais urgente)
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    weight_kg: float = 0.0
    is_completed: bool = False


@dataclass
class OptimizedStop:
    """Parada otimizada com métricas calculadas."""
    delivery_id: str
    sequence: int
    lat: float
    lng: float
    distance_from_previous_km: float
    duration_from_previous_min: float
    eta: datetime | None = None
    incidents_nearby: int = 0
    penalty_score: float = 0.0


@dataclass
class OptimizationResult:
    """Resultado da otimização de rota."""
    stops: list[OptimizedStop] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_duration_min: float = 0.0
    optimization_score: float = 0.0
    incidents_avoided: int = 0



class RouteOptimizer:
    """Engine principal de otimização de rotas.

    Combina:
    1. Nearest-neighbor heuristic para ordenação base
    2. Penalização por incidentes Waze (severidade * peso)
    3. Boost de prioridade (entregas urgentes sobem na fila)
    4. Respeito a janelas de tempo
    """

    # Pesos para score composto
    WEIGHT_DISTANCE = 0.4
    WEIGHT_INCIDENTS = 0.3
    WEIGHT_PRIORITY = 0.2
    WEIGHT_TIME_WINDOW = 0.1

    # Penalização por severidade de incidente
    INCIDENT_PENALTY = {
        1: 0.1,   # Mínimo - quase ignora
        2: 0.3,   # Baixo
        3: 0.6,   # Moderado
        4: 1.0,   # Alto - penalização total
        5: 2.0,   # Crítico - dobro de penalização
    }

    async def optimize_route(
        self,
        origin_lat: float,
        origin_lng: float,
        deliveries: list[DeliveryPoint],
        incidents: list[WazeIncident] | None = None,
        current_time: datetime | None = None,
    ) -> OptimizationResult:
        """Otimiza a sequência de entregas a partir da posição atual.

        Args:
            origin_lat: Latitude atual (motorista).
            origin_lng: Longitude atual (motorista).
            deliveries: Lista de entregas pendentes.
            incidents: Incidentes ativos na região (se None, busca do Waze).
            current_time: Horário atual para cálculo de janelas.

        Returns:
            OptimizationResult com a sequência otimizada.
        """
        if not deliveries:
            return OptimizationResult()

        current_time = current_time or datetime.utcnow()

        # Filtrar apenas entregas não completadas
        pending = [d for d in deliveries if not d.is_completed]
        if not pending:
            return OptimizationResult()

        # Buscar incidentes se não fornecidos
        if incidents is None:
            incidents = await waze_service.get_incidents_in_area(
                origin_lat, origin_lng, radius_km=15.0
            )

        # Executar nearest-neighbor com scoring composto
        result = await self._nearest_neighbor_weighted(
            origin_lat, origin_lng, pending, incidents, current_time
        )

        return result


    async def _nearest_neighbor_weighted(
        self,
        origin_lat: float,
        origin_lng: float,
        deliveries: list[DeliveryPoint],
        incidents: list[WazeIncident],
        current_time: datetime,
    ) -> OptimizationResult:
        """Nearest-neighbor com pesos compostos."""
        remaining = list(deliveries)
        current_lat, current_lng = origin_lat, origin_lng
        stops: list[OptimizedStop] = []
        total_distance = 0.0
        total_duration = 0.0
        incidents_avoided = 0
        elapsed_minutes = 0.0

        sequence = 1
        while remaining:
            best_idx = -1
            best_score = float("inf")
            best_distance = 0.0
            best_duration = 0.0
            best_incidents_count = 0

            for idx, delivery in enumerate(remaining):
                # Calcular distância
                dist_km = geodesic(
                    (current_lat, current_lng),
                    (delivery.lat, delivery.lng)
                ).kilometers * 1.3  # Fator de correção urbana

                # Duração estimada (km/h médio)
                duration_min = (dist_km / settings.default_speed_kmh) * 60

                # Contar incidentes no caminho
                nearby_incidents = self._count_incidents_on_path(
                    current_lat, current_lng,
                    delivery.lat, delivery.lng,
                    incidents
                )
                incident_penalty = sum(
                    self.INCIDENT_PENALTY.get(i.severity, 0.5)
                    for i in nearby_incidents
                )

                # Score de prioridade (menor = melhor)
                priority_boost = (100 - delivery.priority_score) / 100.0

                # Penalização por janela de tempo
                time_penalty = self._time_window_penalty(
                    delivery, current_time, elapsed_minutes + duration_min
                )

                # Score composto (menor = melhor)
                score = (
                    self.WEIGHT_DISTANCE * (dist_km / 10.0) +
                    self.WEIGHT_INCIDENTS * incident_penalty +
                    self.WEIGHT_PRIORITY * priority_boost +
                    self.WEIGHT_TIME_WINDOW * time_penalty
                )

                if score < best_score:
                    best_score = score
                    best_idx = idx
                    best_distance = dist_km
                    best_duration = duration_min
                    best_incidents_count = len(nearby_incidents)

            # Selecionar melhor próxima parada
            chosen = remaining.pop(best_idx)
            elapsed_minutes += best_duration

            eta = current_time.__class__(
                current_time.year, current_time.month, current_time.day,
                current_time.hour, current_time.minute
            )

            stops.append(OptimizedStop(
                delivery_id=chosen.id,
                sequence=sequence,
                lat=chosen.lat,
                lng=chosen.lng,
                distance_from_previous_km=round(best_distance, 2),
                duration_from_previous_min=round(best_duration, 1),
                incidents_nearby=best_incidents_count,
                penalty_score=round(best_score, 3),
            ))

            total_distance += best_distance
            total_duration += best_duration
            if best_incidents_count > 0:
                incidents_avoided += best_incidents_count

            current_lat, current_lng = chosen.lat, chosen.lng
            sequence += 1

        # Calcular score geral de otimização (0-100)
        max_possible_distance = len(deliveries) * 20.0
        opt_score = max(0, 100 - (total_distance / max_possible_distance) * 100)

        return OptimizationResult(
            stops=stops,
            total_distance_km=round(total_distance, 2),
            total_duration_min=round(total_duration, 1),
            optimization_score=round(opt_score, 1),
            incidents_avoided=incidents_avoided,
        )


    def _count_incidents_on_path(
        self,
        from_lat: float,
        from_lng: float,
        to_lat: float,
        to_lng: float,
        incidents: list[WazeIncident],
        corridor_km: float = 0.5,
    ) -> list[WazeIncident]:
        """Conta incidentes dentro do corredor entre dois pontos."""
        on_path = []
        for incident in incidents:
            dist_to_line = self._point_to_line_distance_km(
                incident.lat, incident.lng,
                from_lat, from_lng,
                to_lat, to_lng
            )
            if dist_to_line <= corridor_km:
                on_path.append(incident)
        return on_path

    def _point_to_line_distance_km(
        self,
        point_lat: float, point_lng: float,
        line_start_lat: float, line_start_lng: float,
        line_end_lat: float, line_end_lng: float,
    ) -> float:
        """Distância aproximada de ponto a segmento de reta (km)."""
        # Vetor do segmento
        dx = line_end_lng - line_start_lng
        dy = line_end_lat - line_start_lat
        seg_len_sq = dx * dx + dy * dy

        if seg_len_sq == 0:
            return geodesic(
                (point_lat, point_lng),
                (line_start_lat, line_start_lng)
            ).kilometers

        # Projeção do ponto no segmento
        t = max(0, min(1, (
            (point_lng - line_start_lng) * dx +
            (point_lat - line_start_lat) * dy
        ) / seg_len_sq))

        proj_lat = line_start_lat + t * dy
        proj_lng = line_start_lng + t * dx

        return geodesic(
            (point_lat, point_lng), (proj_lat, proj_lng)
        ).kilometers

    def _time_window_penalty(
        self,
        delivery: DeliveryPoint,
        current_time: datetime,
        eta_minutes: float,
    ) -> float:
        """Calcula penalização por violação de janela de tempo."""
        if not delivery.time_window_end:
            return 0.0

        from datetime import timedelta
        arrival_time = current_time + timedelta(minutes=eta_minutes)

        if arrival_time > delivery.time_window_end:
            # Atraso em minutos
            delay = (arrival_time - delivery.time_window_end).total_seconds() / 60
            return min(delay / 30.0, 3.0)  # Max 3.0 de penalidade

        if delivery.time_window_start and arrival_time < delivery.time_window_start:
            # Chegaria muito cedo - leve penalidade
            early = (delivery.time_window_start - arrival_time).total_seconds() / 60
            return min(early / 60.0, 1.0)

        return 0.0

    async def re_optimize_after_delivery(
        self,
        driver_lat: float,
        driver_lng: float,
        remaining_deliveries: list[DeliveryPoint],
    ) -> OptimizationResult:
        """Re-otimiza rota após motorista confirmar uma entrega.

        Chamado automaticamente quando uma entrega é confirmada.
        Recalcula a melhor sequência a partir da posição atual.
        """
        logger.info(
            f"Re-otimizando rota: {len(remaining_deliveries)} entregas restantes "
            f"a partir de ({driver_lat}, {driver_lng})"
        )
        return await self.optimize_route(
            origin_lat=driver_lat,
            origin_lng=driver_lng,
            deliveries=remaining_deliveries,
        )


# Singleton
route_optimizer = RouteOptimizer()
