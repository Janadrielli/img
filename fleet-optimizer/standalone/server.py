#!/usr/bin/env python3
"""
Fleet Route Optimizer - Standalone Server (Zero Dependencies)

Servidor HTTP puro Python usando apenas stdlib.
Banco SQLite em memória. Sem necessidade de PostgreSQL, Redis ou pip install.

Uso:
    python3 server.py [--port 8000]

Endpoints:
    GET  /api/v1/dashboard/stats
    GET  /api/v1/drivers
    POST /api/v1/drivers
    PATCH /api/v1/drivers/{id}/location
    GET  /api/v1/deliveries
    POST /api/v1/deliveries
    POST /api/v1/deliveries/{id}/confirm
    PATCH /api/v1/deliveries/{id}
    GET  /api/v1/routes
    POST /api/v1/routes/optimize
    POST /api/v1/routes/{id}/override-priority
    GET  /api/v1/incidents
    GET  /health
    GET  / (frontend HTML)
"""

import http.server
import json
import sqlite3
import math
import uuid
import sys
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from typing import Any

# === Database Setup ===

DB_PATH = ":memory:"
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row
db.execute("PRAGMA journal_mode=WAL")
db.execute("PRAGMA foreign_keys=ON")


def init_db():
    """Cria todas as tabelas."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS drivers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_plate TEXT NOT NULL,
            vehicle_type TEXT DEFAULT 'van',
            status TEXT DEFAULT 'offline',
            current_lat REAL,
            current_lng REAL,
            last_location_update TEXT,
            is_active INTEGER DEFAULT 1,
            max_deliveries INTEGER DEFAULT 20,
            max_weight_kg REAL DEFAULT 1000.0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id TEXT PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            description TEXT,
            address TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            weight_kg REAL DEFAULT 0.0,
            volume_m3 REAL DEFAULT 0.0,
            priority TEXT DEFAULT 'normal',
            priority_score INTEGER DEFAULT 50,
            time_window_start TEXT,
            time_window_end TEXT,
            status TEXT DEFAULT 'pending',
            sequence_order INTEGER,
            confirmed_at TEXT,
            confirmed_lat REAL,
            confirmed_lng REAL,
            confirmation_notes TEXT,
            receiver_name TEXT,
            estimated_arrival TEXT,
            actual_arrival TEXT,
            route_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS routes (
            id TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL,
            status TEXT DEFAULT 'planned',
            origin_lat REAL NOT NULL,
            origin_lng REAL NOT NULL,
            origin_address TEXT DEFAULT 'Base',
            total_distance_km REAL DEFAULT 0.0,
            total_duration_minutes REAL DEFAULT 0.0,
            total_stops INTEGER DEFAULT 0,
            completed_stops INTEGER DEFAULT 0,
            optimization_score REAL DEFAULT 0.0,
            last_optimized_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        );

        CREATE TABLE IF NOT EXISTS route_stops (
            id TEXT PRIMARY KEY,
            route_id TEXT NOT NULL,
            delivery_id TEXT NOT NULL,
            sequence_order INTEGER NOT NULL,
            is_completed INTEGER DEFAULT 0,
            distance_from_previous_km REAL DEFAULT 0.0,
            duration_from_previous_min REAL DEFAULT 0.0,
            eta TEXT,
            waze_incidents_on_path INTEGER DEFAULT 0,
            has_active_incident INTEGER DEFAULT 0,
            arrived_at TEXT,
            FOREIGN KEY (route_id) REFERENCES routes(id),
            FOREIGN KEY (delivery_id) REFERENCES deliveries(id)
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            waze_id TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            street TEXT,
            city TEXT,
            incident_type TEXT NOT NULL,
            severity INTEGER DEFAULT 1,
            description TEXT,
            delay_seconds INTEGER DEFAULT 0,
            speed_kmh REAL,
            is_active INTEGER DEFAULT 1,
            reported_at TEXT DEFAULT (datetime('now')),
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit()



# === Route Optimization Engine ===

def haversine_km(lat1, lng1, lat2, lng2):
    """Distância haversine entre dois pontos em km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def point_to_segment_distance_km(plat, plng, slat, slng, elat, elng):
    """Distância de ponto a segmento de reta (km aproximado)."""
    dx = elng - slng
    dy = elat - slat
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq == 0:
        return haversine_km(plat, plng, slat, slng)
    t = max(0, min(1, ((plng - slng) * dx + (plat - slat) * dy) / seg_len_sq))
    proj_lat = slat + t * dy
    proj_lng = slng + t * dx
    return haversine_km(plat, plng, proj_lat, proj_lng)


def count_incidents_on_path(from_lat, from_lng, to_lat, to_lng, incidents, corridor_km=0.5):
    """Incidentes dentro do corredor entre dois pontos."""
    on_path = []
    for inc in incidents:
        dist = point_to_segment_distance_km(
            inc["lat"], inc["lng"], from_lat, from_lng, to_lat, to_lng
        )
        if dist <= corridor_km:
            on_path.append(inc)
    return on_path


# Pesos do algoritmo
WEIGHT_DISTANCE = 0.4
WEIGHT_INCIDENTS = 0.3
WEIGHT_PRIORITY = 0.2
WEIGHT_TIME_WINDOW = 0.1

INCIDENT_PENALTY = {1: 0.1, 2: 0.3, 3: 0.6, 4: 1.0, 5: 2.0}
DEFAULT_SPEED_KMH = 40.0


def optimize_route(origin_lat, origin_lng, deliveries, incidents=None):
    """Nearest-neighbor com penalização por incidentes.

    Args:
        origin_lat, origin_lng: Posição atual do motorista
        deliveries: list of dicts com id, lat, lng, priority_score, time_window_end
        incidents: list of dicts com lat, lng, severity

    Returns:
        dict com stops (ordenados), total_distance_km, total_duration_min, optimization_score
    """
    if incidents is None:
        incidents = get_active_incidents()

    remaining = list(deliveries)
    current_lat, current_lng = origin_lat, origin_lng
    stops = []
    total_distance = 0.0
    total_duration = 0.0
    elapsed_min = 0.0
    sequence = 1
    now = datetime.utcnow()

    while remaining:
        best_idx = -1
        best_score = float("inf")
        best_dist = 0.0
        best_dur = 0.0
        best_inc_count = 0

        for idx, d in enumerate(remaining):
            dist_km = haversine_km(current_lat, current_lng, d["lat"], d["lng"]) * 1.3
            dur_min = (dist_km / DEFAULT_SPEED_KMH) * 60

            nearby_inc = count_incidents_on_path(
                current_lat, current_lng, d["lat"], d["lng"], incidents
            )
            inc_penalty = sum(INCIDENT_PENALTY.get(i.get("severity", 1), 0.5) for i in nearby_inc)

            priority_boost = (100 - d.get("priority_score", 50)) / 100.0

            # Time window penalty
            tw_penalty = 0.0
            tw_end = d.get("time_window_end")
            if tw_end:
                try:
                    tw_end_dt = datetime.fromisoformat(tw_end.replace("Z", "+00:00").replace("+00:00", ""))
                except:
                    tw_end_dt = None
                if tw_end_dt:
                    arrival = now + timedelta(minutes=elapsed_min + dur_min)
                    if arrival > tw_end_dt:
                        delay_min = (arrival - tw_end_dt).total_seconds() / 60
                        tw_penalty = min(delay_min / 30.0, 3.0)

            score = (
                WEIGHT_DISTANCE * (dist_km / 10.0) +
                WEIGHT_INCIDENTS * inc_penalty +
                WEIGHT_PRIORITY * priority_boost +
                WEIGHT_TIME_WINDOW * tw_penalty
            )

            if score < best_score:
                best_score = score
                best_idx = idx
                best_dist = dist_km
                best_dur = dur_min
                best_inc_count = len(nearby_inc)

        chosen = remaining.pop(best_idx)
        elapsed_min += best_dur
        eta = (now + timedelta(minutes=elapsed_min)).isoformat()

        stops.append({
            "delivery_id": chosen["id"],
            "sequence": sequence,
            "lat": chosen["lat"],
            "lng": chosen["lng"],
            "distance_from_previous_km": round(best_dist, 2),
            "duration_from_previous_min": round(best_dur, 1),
            "eta": eta,
            "incidents_nearby": best_inc_count,
            "score": round(best_score, 3),
        })

        total_distance += best_dist
        total_duration += best_dur
        current_lat, current_lng = chosen["lat"], chosen["lng"]
        sequence += 1

    max_possible = len(deliveries) * 20.0
    opt_score = max(0, 100 - (total_distance / max(max_possible, 1)) * 100)

    return {
        "stops": stops,
        "total_distance_km": round(total_distance, 2),
        "total_duration_min": round(total_duration, 1),
        "optimization_score": round(opt_score, 1),
    }


def get_active_incidents():
    """Busca incidentes ativos do banco."""
    rows = db.execute("SELECT * FROM incidents WHERE is_active = 1").fetchall()
    return [dict(r) for r in rows]



# === Seed Data ===

def seed_data():
    """Popula banco com dados de exemplo para validação."""
    # Motoristas (São Paulo)
    drivers = [
        ("d1", "Carlos Silva", "(11)99001-1234", "ABC-1234", "van", "en_route", -23.5505, -46.6333),
        ("d2", "Ana Oliveira", "(11)99002-5678", "DEF-5678", "truck", "delivering", -23.5615, -46.6553),
        ("d3", "Pedro Santos", "(11)99003-9012", "GHI-9012", "moto", "available", -23.5430, -46.6200),
        ("d4", "Maria Costa", "(11)99004-3456", "JKL-3456", "van", "offline", None, None),
    ]
    for d in drivers:
        db.execute(
            "INSERT OR IGNORE INTO drivers (id, name, phone, vehicle_plate, vehicle_type, status, current_lat, current_lng, last_location_update) VALUES (?,?,?,?,?,?,?,?,?)",
            (*d, datetime.utcnow().isoformat() if d[6] else None)
        )

    # Entregas (espalhadas por São Paulo)
    deliveries_data = [
        ("del01", "PED-2024-001", "João Mendes", "Rua Augusta, 1500 - Consolação", -23.5537, -46.6580, "critical", 100),
        ("del02", "PED-2024-002", "Fernanda Lima", "Av. Paulista, 1000 - Bela Vista", -23.5631, -46.6542, "high", 80),
        ("del03", "PED-2024-003", "Roberto Alves", "Rua Oscar Freire, 700 - Pinheiros", -23.5620, -46.6720, "high", 75),
        ("del04", "PED-2024-004", "Lucia Ferreira", "Av. Faria Lima, 2000 - Itaim Bibi", -23.5730, -46.6890, "normal", 50),
        ("del05", "PED-2024-005", "Marco Ribeiro", "Rua Haddock Lobo, 400 - Cerqueira César", -23.5560, -46.6620, "normal", 50),
        ("del06", "PED-2024-006", "Camila Souza", "Av. Rebouças, 1200 - Pinheiros", -23.5650, -46.6780, "normal", 45),
        ("del07", "PED-2024-007", "Bruno Martins", "Rua da Consolação, 2300 - Consolação", -23.5490, -46.6530, "low", 25),
        ("del08", "PED-2024-008", "Patrícia Gomes", "Av. Brigadeiro Faria Lima, 3400", -23.5820, -46.6920, "critical", 95),
        ("del09", "PED-2024-009", "André Neves", "Rua Bela Cintra, 800 - Consolação", -23.5568, -46.6570, "high", 70),
        ("del10", "PED-2024-010", "Juliana Dias", "Av. Brasil, 1500 - Jardim América", -23.5600, -46.6710, "normal", 55),
    ]
    for d in deliveries_data:
        db.execute(
            "INSERT OR IGNORE INTO deliveries (id, order_number, customer_name, address, lat, lng, priority, priority_score) VALUES (?,?,?,?,?,?,?,?)",
            d
        )

    # Incidentes Waze simulados
    incidents_data = [
        ("inc01", -23.5580, -46.6600, "Av. Paulista", "São Paulo", "accident", 4, "Acidente envolvendo 2 veículos", 600),
        ("inc02", -23.5700, -46.6850, "Av. Faria Lima", "São Paulo", "jam", 3, "Congestionamento intenso - 10min", 600),
        ("inc03", -23.5550, -46.6500, "Rua da Consolação", "São Paulo", "construction", 2, "Obra na via - faixa interditada", 300),
        ("inc04", -23.5650, -46.6700, "Av. Rebouças", "São Paulo", "hazard", 3, "Buraco na pista", 180),
        ("inc05", -23.5800, -46.6900, "Marginal Pinheiros", "São Paulo", "jam", 5, "Congestionamento crítico", 1200),
    ]
    for inc in incidents_data:
        db.execute(
            "INSERT OR IGNORE INTO incidents (id, lat, lng, street, city, incident_type, severity, description, delay_seconds) VALUES (?,?,?,?,?,?,?,?,?)",
            inc
        )

    db.commit()
    print(f"[SEED] {len(drivers)} motoristas, {len(deliveries_data)} entregas, {len(incidents_data)} incidentes carregados.")



# === API Handlers ===

def json_response(handler, data, status=200):
    """Envia resposta JSON."""
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler):
    """Lê corpo da requisição como dict."""
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    body = handler.rfile.read(length)
    return json.loads(body)


def handle_get_stats(handler):
    """GET /api/v1/dashboard/stats"""
    total_drivers = db.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
    active_drivers = db.execute("SELECT COUNT(*) FROM drivers WHERE status IN ('en_route','delivering')").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM deliveries WHERE status='pending'").fetchone()[0]
    in_progress = db.execute("SELECT COUNT(*) FROM deliveries WHERE status IN ('assigned','en_route','arrived')").fetchone()[0]
    completed = db.execute("SELECT COUNT(*) FROM deliveries WHERE status IN ('delivered','confirmed')").fetchone()[0]
    total_today = db.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    active_incidents = db.execute("SELECT COUNT(*) FROM incidents WHERE is_active=1").fetchone()[0]

    json_response(handler, {
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "total_deliveries_today": total_today,
        "pending_deliveries": pending,
        "in_progress_deliveries": in_progress,
        "completed_deliveries": completed,
        "active_incidents": active_incidents,
        "avg_eta_minutes": 0.0,
    })


def handle_get_drivers(handler):
    """GET /api/v1/drivers"""
    rows = db.execute("SELECT * FROM drivers ORDER BY name").fetchall()
    json_response(handler, [dict(r) for r in rows])


def handle_create_driver(handler):
    """POST /api/v1/drivers"""
    data = read_body(handler)
    driver_id = str(uuid.uuid4())[:8]
    db.execute(
        "INSERT INTO drivers (id, name, phone, vehicle_plate, vehicle_type, status) VALUES (?,?,?,?,?,?)",
        (driver_id, data["name"], data["phone"], data["vehicle_plate"], data.get("vehicle_type", "van"), "available")
    )
    db.commit()
    row = db.execute("SELECT * FROM drivers WHERE id=?", (driver_id,)).fetchone()
    json_response(handler, dict(row), 201)


def handle_update_location(handler, driver_id):
    """PATCH /api/v1/drivers/{id}/location"""
    data = read_body(handler)
    now = datetime.utcnow().isoformat()
    db.execute(
        "UPDATE drivers SET current_lat=?, current_lng=?, last_location_update=? WHERE id=?",
        (data["lat"], data["lng"], now, driver_id)
    )
    db.commit()
    json_response(handler, {"status": "ok", "lat": data["lat"], "lng": data["lng"], "updated_at": now})


def handle_get_deliveries(handler, params):
    """GET /api/v1/deliveries"""
    query = "SELECT * FROM deliveries"
    conditions = []
    args = []
    if "status" in params:
        conditions.append("status=?")
        args.append(params["status"][0])
    if "priority" in params:
        conditions.append("priority=?")
        args.append(params["priority"][0])
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY priority_score DESC, created_at"
    rows = db.execute(query, args).fetchall()
    json_response(handler, [dict(r) for r in rows])


def handle_create_delivery(handler):
    """POST /api/v1/deliveries"""
    data = read_body(handler)
    del_id = str(uuid.uuid4())[:8]
    db.execute(
        """INSERT INTO deliveries (id, order_number, customer_name, customer_phone,
           description, address, lat, lng, weight_kg, priority, priority_score,
           time_window_start, time_window_end)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (del_id, data["order_number"], data["customer_name"], data.get("customer_phone"),
         data.get("description"), data["address"], data["lat"], data["lng"],
         data.get("weight_kg", 0), data.get("priority", "normal"),
         data.get("priority_score", 50), data.get("time_window_start"),
         data.get("time_window_end"))
    )
    db.commit()
    row = db.execute("SELECT * FROM deliveries WHERE id=?", (del_id,)).fetchone()
    json_response(handler, dict(row), 201)


def handle_update_delivery(handler, delivery_id):
    """PATCH /api/v1/deliveries/{id}"""
    data = read_body(handler)
    sets = []
    args = []
    for key in ("priority", "priority_score", "status", "time_window_start", "time_window_end"):
        if key in data and data[key] is not None:
            sets.append(f"{key}=?")
            args.append(data[key])
    if sets:
        sets.append("updated_at=?")
        args.append(datetime.utcnow().isoformat())
        args.append(delivery_id)
        db.execute(f"UPDATE deliveries SET {', '.join(sets)} WHERE id=?", args)
        db.commit()
    row = db.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()
    if row:
        json_response(handler, dict(row))
    else:
        json_response(handler, {"error": "Entrega não encontrada"}, 404)



def handle_confirm_delivery(handler, delivery_id):
    """POST /api/v1/deliveries/{id}/confirm

    Confirma entrega e dispara re-otimização automática.
    """
    data = read_body(handler)
    row = db.execute("SELECT * FROM deliveries WHERE id=?", (delivery_id,)).fetchone()
    if not row:
        return json_response(handler, {"error": "Entrega não encontrada"}, 404)
    if row["status"] == "confirmed":
        return json_response(handler, {"error": "Entrega já confirmada"}, 400)

    now = datetime.utcnow().isoformat()
    db.execute(
        """UPDATE deliveries SET status='confirmed', confirmed_at=?, confirmed_lat=?,
           confirmed_lng=?, confirmation_notes=?, receiver_name=?, actual_arrival=?,
           updated_at=? WHERE id=?""",
        (now, data["lat"], data["lng"], data.get("notes"), data["receiver_name"], now, now, delivery_id)
    )

    # Marcar stop como completa e atualizar rota
    route_id = row["route_id"]
    if route_id:
        db.execute(
            "UPDATE route_stops SET is_completed=1, arrived_at=? WHERE delivery_id=? AND route_id=?",
            (now, delivery_id, route_id)
        )
        db.execute(
            "UPDATE routes SET completed_stops = completed_stops + 1 WHERE id=?",
            (route_id,)
        )

        # Re-otimizar entregas restantes
        remaining = db.execute(
            """SELECT d.* FROM deliveries d
               JOIN route_stops rs ON rs.delivery_id = d.id
               WHERE rs.route_id=? AND rs.is_completed=0""",
            (route_id,)
        ).fetchall()

        if remaining:
            remaining_dicts = [dict(r) for r in remaining]
            incidents = get_active_incidents()
            result = optimize_route(data["lat"], data["lng"], remaining_dicts, incidents)

            # Atualizar sequências
            for stop in result["stops"]:
                db.execute(
                    """UPDATE route_stops SET sequence_order=?, distance_from_previous_km=?,
                       duration_from_previous_min=?, waze_incidents_on_path=?
                       WHERE delivery_id=? AND route_id=?""",
                    (stop["sequence"], stop["distance_from_previous_km"],
                     stop["duration_from_previous_min"], stop["incidents_nearby"],
                     stop["delivery_id"], route_id)
                )
            db.execute(
                """UPDATE routes SET total_distance_km=?, total_duration_minutes=?,
                   optimization_score=?, last_optimized_at=? WHERE id=?""",
                (result["total_distance_km"], result["total_duration_min"],
                 result["optimization_score"], now, route_id)
            )
        else:
            db.execute("UPDATE routes SET status='completed', completed_at=? WHERE id=?", (now, route_id))

    db.commit()

    json_response(handler, {
        "status": "confirmed",
        "delivery_id": delivery_id,
        "confirmed_at": now,
        "receiver_name": data["receiver_name"],
        "message": "Entrega confirmada. Rota re-otimizada automaticamente.",
        "re_optimized": route_id is not None,
    })


def handle_get_routes(handler):
    """GET /api/v1/routes"""
    routes = db.execute("SELECT * FROM routes WHERE status IN ('planned','active') ORDER BY created_at DESC").fetchall()
    result = []
    for r in routes:
        route_dict = dict(r)
        stops = db.execute(
            "SELECT * FROM route_stops WHERE route_id=? ORDER BY sequence_order",
            (r["id"],)
        ).fetchall()
        route_dict["stops"] = [dict(s) for s in stops]
        result.append(route_dict)
    json_response(handler, result)


def handle_optimize_route(handler):
    """POST /api/v1/routes/optimize

    Cria rota otimizada para um motorista.
    """
    data = read_body(handler)
    driver_id = data["driver_id"]

    driver = db.execute("SELECT * FROM drivers WHERE id=?", (driver_id,)).fetchone()
    if not driver:
        return json_response(handler, {"error": "Motorista não encontrado"}, 404)
    if not driver["current_lat"]:
        return json_response(handler, {"error": "Motorista sem localização"}, 400)

    # Buscar entregas pendentes
    if "delivery_ids" in data and data["delivery_ids"]:
        placeholders = ",".join(["?"] * len(data["delivery_ids"]))
        deliveries = db.execute(
            f"SELECT * FROM deliveries WHERE id IN ({placeholders}) AND status='pending'",
            data["delivery_ids"]
        ).fetchall()
    else:
        deliveries = db.execute(
            "SELECT * FROM deliveries WHERE status='pending' ORDER BY priority_score DESC LIMIT ?",
            (driver["max_deliveries"],)
        ).fetchall()

    if not deliveries:
        return json_response(handler, {"error": "Nenhuma entrega pendente"}, 400)

    delivery_dicts = [dict(d) for d in deliveries]
    incidents = get_active_incidents()

    # Otimizar
    result = optimize_route(driver["current_lat"], driver["current_lng"], delivery_dicts, incidents)

    # Criar rota
    route_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    db.execute(
        """INSERT INTO routes (id, driver_id, status, origin_lat, origin_lng,
           total_distance_km, total_duration_minutes, total_stops, completed_stops,
           optimization_score, last_optimized_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (route_id, driver_id, "active", driver["current_lat"], driver["current_lng"],
         result["total_distance_km"], result["total_duration_min"],
         len(result["stops"]), 0, result["optimization_score"], now)
    )

    # Criar stops e vincular deliveries
    for stop in result["stops"]:
        stop_id = str(uuid.uuid4())[:8]
        db.execute(
            """INSERT INTO route_stops (id, route_id, delivery_id, sequence_order,
               distance_from_previous_km, duration_from_previous_min, eta, waze_incidents_on_path)
               VALUES (?,?,?,?,?,?,?,?)""",
            (stop_id, route_id, stop["delivery_id"], stop["sequence"],
             stop["distance_from_previous_km"], stop["duration_from_previous_min"],
             stop["eta"], stop["incidents_nearby"])
        )
        db.execute(
            "UPDATE deliveries SET status='assigned', route_id=?, sequence_order=? WHERE id=?",
            (route_id, stop["sequence"], stop["delivery_id"])
        )

    # Atualizar status do motorista
    db.execute("UPDATE drivers SET status='en_route' WHERE id=?", (driver_id,))
    db.commit()

    # Retornar rota completa
    route = dict(db.execute("SELECT * FROM routes WHERE id=?", (route_id,)).fetchone())
    stops = db.execute("SELECT * FROM route_stops WHERE route_id=? ORDER BY sequence_order", (route_id,)).fetchall()
    route["stops"] = [dict(s) for s in stops]
    json_response(handler, route, 201)


def handle_override_priority(handler, route_id):
    """POST /api/v1/routes/{id}/override-priority

    Gestor sobrescreve a ordem das entregas.
    """
    data = read_body(handler)
    ordered_ids = data.get("delivery_ids_ordered", [])
    reason = data.get("reason", "")

    route = db.execute("SELECT * FROM routes WHERE id=?", (route_id,)).fetchone()
    if not route:
        return json_response(handler, {"error": "Rota não encontrada"}, 404)

    now = datetime.utcnow().isoformat()
    for idx, del_id in enumerate(ordered_ids, start=1):
        db.execute(
            "UPDATE route_stops SET sequence_order=? WHERE delivery_id=? AND route_id=? AND is_completed=0",
            (idx, del_id, route_id)
        )
        db.execute("UPDATE deliveries SET sequence_order=? WHERE id=?", (idx, del_id))

    db.execute("UPDATE routes SET last_optimized_at=? WHERE id=?", (now, route_id))
    db.commit()

    json_response(handler, {
        "status": "ok",
        "message": "Ordem atualizada pelo gestor.",
        "route_id": route_id,
        "reason": reason,
        "new_order": ordered_ids,
    })


def handle_get_incidents(handler):
    """GET /api/v1/incidents"""
    rows = db.execute("SELECT * FROM incidents WHERE is_active=1 ORDER BY severity DESC").fetchall()
    json_response(handler, [dict(r) for r in rows])



# === HTTP Request Handler ===

class FleetAPIHandler(http.server.BaseHTTPRequestHandler):
    """Handler HTTP que roteia requests para os handlers adequados."""

    def log_message(self, format, *args):
        """Override para log mais limpo."""
        sys.stdout.write(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {args[0]}\n")
        sys.stdout.flush()

    def handle_one_request(self):
        """Override para capturar BrokenPipe."""
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            params = parse_qs(parsed.query)

            if path == "" or path == "/":
                self._serve_frontend()
            elif path == "/health":
                json_response(self, {"status": "healthy", "service": "Fleet Route Optimizer", "version": "1.0.0-standalone"})
            elif path == "/api/v1/dashboard/stats":
                handle_get_stats(self)
            elif path == "/api/v1/drivers":
                handle_get_drivers(self)
            elif path == "/api/v1/deliveries":
                handle_get_deliveries(self, params)
            elif path == "/api/v1/routes":
                handle_get_routes(self)
            elif path == "/api/v1/incidents" or path == "/api/v1/dashboard/incidents":
                handle_get_incidents(self)
            else:
                json_response(self, {"error": "Not found", "path": path}, 404)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path == "/api/v1/drivers":
                handle_create_driver(self)
            elif path == "/api/v1/deliveries":
                handle_create_delivery(self)
            elif path == "/api/v1/routes/optimize":
                handle_optimize_route(self)
            elif path.startswith("/api/v1/deliveries/") and path.endswith("/confirm"):
                delivery_id = path.split("/")[4]
                handle_confirm_delivery(self, delivery_id)
            elif path.startswith("/api/v1/routes/") and path.endswith("/override-priority"):
                route_id = path.split("/")[4]
                handle_override_priority(self, route_id)
            else:
                json_response(self, {"error": "Not found", "path": path}, 404)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_PATCH(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path.startswith("/api/v1/drivers/") and path.endswith("/location"):
                driver_id = path.split("/")[4]
                handle_update_location(self, driver_id)
            elif path.startswith("/api/v1/deliveries/"):
                delivery_id = path.split("/")[4]
                handle_update_delivery(self, delivery_id)
            else:
                json_response(self, {"error": "Not found", "path": path}, 404)
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def _serve_frontend(self):
        """Serve o dashboard HTML estático."""
        # Try multiple paths for index.html
        candidates = [
            os.path.join(os.getcwd(), "index.html"),
            os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "index.html"),
        ]
        # Also try __file__ if it exists
        try:
            candidates.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))
        except NameError:
            pass

        html_path = None
        for c in candidates:
            if os.path.exists(c):
                html_path = c
                break

        if html_path:
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            json_response(self, {"message": "Fleet Route Optimizer API", "docs": "/health", "endpoints": [
                "GET /api/v1/dashboard/stats",
                "GET /api/v1/drivers",
                "GET /api/v1/deliveries",
                "GET /api/v1/routes",
                "GET /api/v1/incidents",
                "POST /api/v1/routes/optimize",
                "POST /api/v1/deliveries/{id}/confirm",
                "POST /api/v1/routes/{id}/override-priority",
            ]})


# === Main ===

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    # Suporte a --db para banco persistente
    db_file = None
    for i, arg in enumerate(sys.argv):
        if arg == "--db" and i + 1 < len(sys.argv):
            db_file = sys.argv[i + 1]

    print("=" * 60)
    print("  FLEET ROUTE OPTIMIZER - Standalone Server")
    print("  Zero dependencies | SQLite | Pure Python")
    print("=" * 60)

    global db
    if db_file and os.path.exists(db_file):
        db.close()
        db = sqlite3.connect(db_file, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        count_drivers = db.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
        count_del = db.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
        count_inc = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        count_routes = db.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
        print(f"\n[DB] Usando banco persistente: {db_file}")
        print(f"     {count_drivers} motoristas | {count_del} entregas | {count_inc} incidentes | {count_routes} rotas")
    else:
        init_db()
        seed_data()

    print(f"\n[SERVER] Rodando em http://localhost:{port}")
    print(f"[SERVER] API docs: http://localhost:{port}/health")
    print(f"[SERVER] Dashboard: http://localhost:{port}/")
    print(f"\n[READY] Pronto para receber requests!\n")
    sys.stdout.flush()

    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer(("0.0.0.0", port), FleetAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Encerrando...")
        server.shutdown()


if __name__ == "__main__":
    main()
