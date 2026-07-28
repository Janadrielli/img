"""Serviço de integração com a API do Waze.

Utiliza a Waze Live Map API para obter:
- Incidentes em tempo real (acidentes, obras, congestionamentos)
- Dados de tráfego (velocidade média por segmento)
- ETA entre dois pontos considerando tráfego atual

Referência: https://developers.google.com/waze/intro-transport
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from geopy.distance import geodesic

from app.core.config import get_settings
from app.core.redis_client import RedisPubSub, redis_client
from app.models.incident import IncidentType, IncidentSeverity

logger = logging.getLogger(__name__)
settings = get_settings()


class WazeIncident:
    """Representação de um incidente do Waze."""

    def __init__(
        self,
        waze_id: str,
        lat: float,
        lng: float,
        incident_type: IncidentType,
        severity: int,
        description: str = "",
        delay_seconds: int = 0,
        speed_kmh: float | None = None,
        street: str = "",
        city: str = "",
    ):
        self.waze_id = waze_id
        self.lat = lat
        self.lng = lng
        self.incident_type = incident_type
        self.severity = severity
        self.description = description
        self.delay_seconds = delay_seconds
        self.speed_kmh = speed_kmh
        self.street = street
        self.city = city


class WazeRouteResult:
    """Resultado de cálculo de rota via Waze."""

    def __init__(
        self,
        duration_minutes: float,
        distance_km: float,
        incidents_on_route: list[WazeIncident],
        route_polyline: list[tuple[float, float]] | None = None,
    ):
        self.duration_minutes = duration_minutes
        self.distance_km = distance_km
        self.incidents_on_route = incidents_on_route
        self.route_polyline = route_polyline

    @property
    def total_delay_minutes(self) -> float:
        """Total de atraso causado por incidentes na rota."""
        return sum(i.delay_seconds for i in self.incidents_on_route) / 60.0

    @property
    def max_severity(self) -> int:
        """Maior severidade de incidente na rota."""
        if not self.incidents_on_route:
            return 0
        return max(i.severity for i in self.incidents_on_route)


class WazeService:
    """Serviço de integração com Waze para dados de tráfego em tempo real."""

    INCIDENT_TYPE_MAP = {
        "ACCIDENT": IncidentType.ACCIDENT,
        "JAM": IncidentType.JAM,
        "ROAD_CLOSED": IncidentType.ROAD_CLOSED,
        "HAZARD": IncidentType.HAZARD,
        "CONSTRUCTION": IncidentType.CONSTRUCTION,
        "POLICE": IncidentType.POLICE,
        "FLOOD": IncidentType.FLOOD,
    }

    def __init__(self):
        self.api_url = settings.waze_api_url
        self.api_key = settings.waze_api_key
        self.http_client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def get_incidents_in_area(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float = 10.0,
    ) -> list[WazeIncident]:
        """Busca incidentes ativos em uma área circular.

        Args:
            center_lat: Latitude do centro da área.
            center_lng: Longitude do centro da área.
            radius_km: Raio de busca em km.

        Returns:
            Lista de incidentes encontrados.
        """
        cache_key = f"waze:incidents:{center_lat:.3f}:{center_lng:.3f}:{radius_km}"
        cached = await RedisPubSub.cache_get(cache_key)
        if cached:
            import orjson
            data = orjson.loads(cached)
            return self._parse_incidents(data)

        # Calcular bounding box
        delta_lat = radius_km / 111.0
        delta_lng = radius_km / (111.0 * abs(
            __import__("math").cos(__import__("math").radians(center_lat))
        ))

        bbox = {
            "top": center_lat + delta_lat,
            "bottom": center_lat - delta_lat,
            "left": center_lng - delta_lng,
            "right": center_lng + delta_lng,
        }

        try:
            response = await self.http_client.get(
                f"{self.api_url}/georss",
                params={
                    "top": bbox["top"],
                    "bottom": bbox["bottom"],
                    "left": bbox["left"],
                    "right": bbox["right"],
                    "types": "alerts,jams",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Cache por 30s
            import orjson
            await RedisPubSub.cache_set(
                cache_key, orjson.dumps(data).decode(), ttl_seconds=30
            )

            return self._parse_incidents(data)

        except httpx.HTTPError as e:
            logger.error(f"Erro ao buscar incidentes do Waze: {e}")
            return []

    async def get_route_info(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> WazeRouteResult:
        """Calcula rota entre dois pontos com dados de tráfego.

        Args:
            origin_lat: Latitude de origem.
            origin_lng: Longitude de origem.
            dest_lat: Latitude de destino.
            dest_lng: Longitude de destino.

        Returns:
            WazeRouteResult com duração, distância e incidentes.
        """
        cache_key = (
            f"waze:route:{origin_lat:.4f},{origin_lng:.4f}"
            f":{dest_lat:.4f},{dest_lng:.4f}"
        )
        cached = await RedisPubSub.cache_get(cache_key)
        if cached:
            import orjson
            data = orjson.loads(cached)
            return self._parse_route_result(data, origin_lat, origin_lng, dest_lat, dest_lng)

        try:
            response = await self.http_client.get(
                f"{self.api_url}/row-TravelTimes/SearchResults",
                params={
                    "from": f"x:{origin_lng} y:{origin_lat}",
                    "to": f"x:{dest_lng} y:{dest_lat}",
                    "nPaths": 1,
                    "useCase": "LIVEMAP_PLANNING",
                    "at": 0,
                    "options": "AVOID_TRAILS",
                },
            )
            response.raise_for_status()
            data = response.json()

            import orjson
            await RedisPubSub.cache_set(
                cache_key, orjson.dumps(data).decode(), ttl_seconds=60
            )

            return self._parse_route_result(data, origin_lat, origin_lng, dest_lat, dest_lng)

        except httpx.HTTPError as e:
            logger.warning(f"Waze route API falhou, usando fallback: {e}")
            return self._fallback_route(origin_lat, origin_lng, dest_lat, dest_lng)

    async def get_eta_minutes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> float:
        """Retorna ETA em minutos entre dois pontos."""
        route = await self.get_route_info(origin_lat, origin_lng, dest_lat, dest_lng)
        return route.duration_minutes

    def _parse_incidents(self, data: dict) -> list[WazeIncident]:
        """Converte resposta da API em lista de WazeIncident."""
        incidents = []

        # Processar alertas
        for alert in data.get("alerts", []):
            incident_type = self.INCIDENT_TYPE_MAP.get(
                alert.get("type", ""), IncidentType.OTHER
            )
            incidents.append(WazeIncident(
                waze_id=str(alert.get("uuid", "")),
                lat=alert.get("location", {}).get("y", 0),
                lng=alert.get("location", {}).get("x", 0),
                incident_type=incident_type,
                severity=min(alert.get("confidence", 1), 5),
                description=alert.get("reportDescription", ""),
                delay_seconds=alert.get("reportRating", 0) * 60,
                street=alert.get("street", ""),
                city=alert.get("city", ""),
            ))

        # Processar congestionamentos
        for jam in data.get("jams", []):
            incidents.append(WazeIncident(
                waze_id=str(jam.get("uuid", "")),
                lat=jam.get("line", [{}])[0].get("y", 0) if jam.get("line") else 0,
                lng=jam.get("line", [{}])[0].get("x", 0) if jam.get("line") else 0,
                incident_type=IncidentType.JAM,
                severity=min(jam.get("level", 1) + 1, 5),
                description=f"Congestionamento - {jam.get('delay', 0)}s de atraso",
                delay_seconds=jam.get("delay", 0),
                speed_kmh=jam.get("speed", None),
                street=jam.get("street", ""),
                city=jam.get("city", ""),
            ))

        return incidents

    def _parse_route_result(
        self,
        data: dict,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> WazeRouteResult:
        """Converte resposta da API em WazeRouteResult."""
        routes = data.get("routes", data.get("alternatives", []))

        if routes:
            best_route = routes[0] if isinstance(routes, list) else routes
            duration_sec = best_route.get("totalSeconds", best_route.get("time", 0))
            distance_m = best_route.get("totalLength", best_route.get("length", 0))

            return WazeRouteResult(
                duration_minutes=duration_sec / 60.0,
                distance_km=distance_m / 1000.0,
                incidents_on_route=[],
            )

        # Se não retornou rotas, usar fallback
        return self._fallback_route(origin_lat, origin_lng, dest_lat, dest_lng)

    def _fallback_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> WazeRouteResult:
        """Calcula rota aproximada quando Waze API não está disponível."""
        distance_km = geodesic(
            (origin_lat, origin_lng), (dest_lat, dest_lng)
        ).kilometers
        # Fator de correção para distância real (~1.4x linha reta)
        real_distance_km = distance_km * 1.4
        # Velocidade média urbana
        duration_minutes = (real_distance_km / settings.default_speed_kmh) * 60

        return WazeRouteResult(
            duration_minutes=duration_minutes,
            distance_km=real_distance_km,
            incidents_on_route=[],
        )

    async def close(self):
        """Fecha o HTTP client."""
        await self.http_client.aclose()


# Singleton
waze_service = WazeService()
