#!/usr/bin/env python3
"""
Seed Database - Base de dados fictícia realista para demonstração.

Simula uma operação logística em São Paulo com:
- 8 motoristas (diferentes status)
- 35 entregas (vários estados, prioridades, janelas de tempo)
- 12 incidentes Waze ativos
- 3 rotas ativas (com entregas em progresso)
- Histórico de confirmações

Uso:
    python3 seed_database.py
    # Depois rodar: python3 server.py
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
import random
import uuid

# Adicionar path do server para usar init_db
sys.path.insert(0, os.path.dirname(__file__))


DB_FILE = os.path.join(os.path.dirname(__file__), "fleet_demo.db")
NOW = datetime(2026, 7, 28, 9, 30, 0)  # Simulando 09:30 de uma segunda-feira


def gen_id():
    return str(uuid.uuid4())[:8]


def main():
    """Cria banco SQLite persistente com dados fictícios."""
    # Remover banco antigo se existir
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db = sqlite3.connect(DB_FILE)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")

    print("=" * 60)
    print("  FLEET OPTIMIZER - Criando Base de Dados de Demonstração")
    print("=" * 60)

    # Criar tabelas
    create_tables(db)

    # Popular dados
    create_drivers(db)
    create_deliveries(db)
    create_incidents(db)
    create_routes(db)

    db.commit()
    db.close()

    print(f"\n[OK] Banco criado em: {DB_FILE}")
    print(f"[OK] Tamanho: {os.path.getsize(DB_FILE) / 1024:.1f} KB")
    print(f"\nPara usar: python3 server.py --db {DB_FILE}")



def create_tables(db):
    """Cria schema completo."""
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
""")


    db.executescript("""
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
    print("[1/4] Tabelas criadas")



def create_drivers(db):
    """Cria 8 motoristas com diferentes status e posições."""
    drivers = [
        # (id, nome, telefone, placa, tipo, status, lat, lng)
        ("drv-001", "Carlos Eduardo Silva", "(11) 99801-2345", "BRA-2E19", "van",
         "en_route", -23.5505, -46.6333),
        ("drv-002", "Ana Paula Oliveira", "(11) 98712-6789", "SPX-4K57", "truck",
         "delivering", -23.5631, -46.6542),
        ("drv-003", "Pedro Henrique Santos", "(11) 97634-1122", "MER-8C03", "moto",
         "en_route", -23.5430, -46.6200),
        ("drv-004", "Maria Fernanda Costa", "(11) 96545-3344", "LOG-1F92", "van",
         "available", -23.5710, -46.6480),
        ("drv-005", "Rafael Augusto Nunes", "(11) 95456-5566", "FRT-7J41", "truck",
         "break", -23.5580, -46.6700),
        ("drv-006", "Juliana de Souza Lima", "(11) 94367-7788", "EXP-3D66", "van",
         "en_route", -23.5750, -46.6850),
        ("drv-007", "Fernando Reis Campos", "(11) 93278-9900", "RPI-5B28", "moto",
         "available", -23.5480, -46.6400),
        ("drv-008", "Beatriz Martins Rocha", "(11) 92189-1234", "TRN-9H73", "van",
         "offline", None, None),
    ]

    for d in drivers:
        loc_time = NOW.isoformat() if d[6] else None
        db.execute(
            """INSERT INTO drivers
               (id, name, phone, vehicle_plate, vehicle_type, status,
                current_lat, current_lng, last_location_update, max_deliveries)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (*d, loc_time, 15 if d[4] == "moto" else 20)
        )

    print(f"[2/4] {len(drivers)} motoristas criados")



def create_deliveries(db):
    """Cria 35 entregas em diversos estados e prioridades."""
    # Endereços reais de São Paulo
    deliveries = [
        # === ENTREGAS CONFIRMADAS (já entregues hoje) ===
        ("del-001", "PED-2026-0001", "João Mendes Filho", "(11)91234-0001",
         "2x Caixas eletrônicos", "Rua Augusta, 1508 - Consolação",
         -23.5537, -46.6580, 12.5, "critical", 100, "confirmed",
         "João M. Filho", (NOW - timedelta(hours=1)).isoformat()),
        ("del-002", "PED-2026-0002", "Fernanda Lima Duarte", "(11)91234-0002",
         "Documentos urgentes", "Av. Paulista, 1000 - Bela Vista",
         -23.5631, -46.6542, 0.5, "critical", 98, "confirmed",
         "Recepção Edifício", (NOW - timedelta(minutes=45)).isoformat()),
        ("del-003", "PED-2026-0003", "Ricardo Almeida Torres", "(11)91234-0003",
         "Material de escritório", "Rua Oscar Freire, 719 - Pinheiros",
         -23.5620, -46.6720, 8.0, "high", 80, "confirmed",
         "Ricardo A.", (NOW - timedelta(minutes=30)).isoformat()),

        # === ENTREGAS EM ROTA (assigned/en_route) ===
        ("del-004", "PED-2026-0004", "Lucia Ferreira Santos", "(11)91234-0004",
         "Peças automotivas - FRÁGIL", "Av. Faria Lima, 2066 - Itaim Bibi",
         -23.5730, -46.6890, 25.0, "high", 85, "en_route", None, None),
        ("del-005", "PED-2026-0005", "Marco Aurélio Ribeiro", "(11)91234-0005",
         "Equipamento médico", "Rua Haddock Lobo, 400 - Cerqueira César",
         -23.5560, -46.6620, 15.0, "critical", 95, "en_route", None, None),
        ("del-006", "PED-2026-0006", "Camila de Souza Prado", "(11)91234-0006",
         "Alimentos refrigerados", "Av. Rebouças, 1200 - Pinheiros",
         -23.5650, -46.6780, 30.0, "high", 78, "assigned", None, None),
        ("del-007", "PED-2026-0007", "Bruno Martins Coelho", "(11)91234-0007",
         "Medicamentos controlados", "Rua da Consolação, 2300",
         -23.5490, -46.6530, 3.0, "critical", 99, "en_route", None, None),
        ("del-008", "PED-2026-0008", "Patrícia Gomes de Araújo", "(11)91234-0008",
         "Envelope contrato", "Av. Brig. Faria Lima, 3400 - Itaim",
         -23.5820, -46.6920, 0.3, "high", 82, "assigned", None, None),
        ("del-009", "PED-2026-0009", "André Luís Neves", "(11)91234-0009",
         "Peças industriais", "Rua Bela Cintra, 806 - Consolação",
         -23.5568, -46.6570, 45.0, "normal", 60, "assigned", None, None),
        ("del-010", "PED-2026-0010", "Juliana Dias Monteiro", "(11)91234-0010",
         "Amostras laboratório", "Av. Brasil, 1532 - Jardim América",
         -23.5600, -46.6710, 2.0, "high", 76, "en_route", None, None),
    ]


    # === ENTREGAS PENDENTES (aguardando atribuição) ===
    pending = [
        ("del-011", "PED-2026-0011", "Thiago Ramos Pereira", "(11)91234-0011",
         "Caixa livros", "Rua Pamplona, 518 - Jardim Paulista",
         -23.5670, -46.6490, 18.0, "normal", 55, "pending"),
        ("del-012", "PED-2026-0012", "Adriana Campos Vieira", "(11)91234-0012",
         "Material de limpeza", "Rua Cardeal Arcoverde, 2365 - Pinheiros",
         -23.5590, -46.6810, 22.0, "low", 30, "pending"),
        ("del-013", "PED-2026-0013", "Gustavo Silva Moreira", "(11)91234-0013",
         "Equipamento de TI", "Al. Santos, 1800 - Cerqueira César",
         -23.5620, -46.6550, 8.5, "high", 75, "pending"),
        ("del-014", "PED-2026-0014", "Isabela Rocha Andrade", "(11)91234-0014",
         "Flores - URGENTE casamento", "Rua Vittorio Fasano, 88 - Jardins",
         -23.5640, -46.6600, 5.0, "critical", 97, "pending"),
        ("del-015", "PED-2026-0015", "Leonardo Costa Barbosa", "(11)91234-0015",
         "Peças maquinário", "Av. Eng. Luís Carlos Berrini, 1376",
         -23.5960, -46.6890, 55.0, "normal", 50, "pending"),
        ("del-016", "PED-2026-0016", "Mariana Alves Teixeira", "(11)91234-0016",
         "Cosméticos importados", "Rua Amauri, 299 - Itaim Bibi",
         -23.5790, -46.6770, 4.0, "normal", 48, "pending"),
        ("del-017", "PED-2026-0017", "Felipe Cunha Resende", "(11)91234-0017",
         "Documentos judiciais", "Rua Funchal, 411 - Vila Olímpia",
         -23.5930, -46.6870, 0.8, "critical", 96, "pending"),
        ("del-018", "PED-2026-0018", "Carolina Pinto Machado", "(11)91234-0018",
         "Vinhos coleção", "Rua Jerônimo da Veiga, 164 - Itaim",
         -23.5810, -46.6800, 20.0, "normal", 45, "pending"),
        ("del-019", "PED-2026-0019", "Rodrigo Gomes Tavares", "(11)91234-0019",
         "Material construção", "Av. Juscelino Kubitschek, 1830",
         -23.5870, -46.6820, 80.0, "low", 25, "pending"),
        ("del-020", "PED-2026-0020", "Vanessa Lopes Ferraz", "(11)91234-0020",
         "Vacinas - MANTER REFRIGERADO", "Rua Leopoldo Couto Magalhães, 700",
         -23.5850, -46.6760, 6.0, "critical", 100, "pending"),
    ]


    # Mais entregas pendentes com janelas de tempo
    more_pending = [
        ("del-021", "PED-2026-0021", "Daniel Barros Figueiredo", "(11)91234-0021",
         "Equipamento médico portátil", "Rua Tabapuã, 1227 - Itaim",
         -23.5780, -46.6760, 7.0, "high", 72, "pending"),
        ("del-022", "PED-2026-0022", "Luciana Moura Castilho", "(11)91234-0022",
         "Uniformes corporativos", "Al. Campinas, 600 - Jardim Paulista",
         -23.5650, -46.6520, 12.0, "normal", 50, "pending"),
        ("del-023", "PED-2026-0023", "Henrique Dias Albuquerque", "(11)91234-0023",
         "Peças de reposição HVAC", "Av. Nove de Julho, 5229 - Jardim Europa",
         -23.5730, -46.6680, 35.0, "normal", 52, "pending"),
        ("del-024", "PED-2026-0024", "Aline Torres Nascimento", "(11)91234-0024",
         "Amostras grátis evento", "Rua Artur de Azevedo, 1800 - Pinheiros",
         -23.5570, -46.6830, 10.0, "low", 20, "pending"),
        ("del-025", "PED-2026-0025", "Vinícius Cardoso Braga", "(11)91234-0025",
         "Servidor rack - PESADO", "Rua Gomes de Carvalho, 1507 - Vila Olímpia",
         -23.5920, -46.6840, 95.0, "high", 70, "pending"),
        ("del-026", "PED-2026-0026", "Roberta Freitas Mendonça", "(11)91234-0026",
         "Cesta de Natal antecipada", "Rua Fidalga, 254 - Vila Madalena",
         -23.5470, -46.6910, 15.0, "low", 15, "pending"),
        ("del-027", "PED-2026-0027", "Eduardo Santana Leal", "(11)91234-0027",
         "Instrumentos musicais", "Rua Augusta, 2690 - Cerqueira César",
         -23.5520, -46.6610, 18.0, "normal", 40, "pending"),
        ("del-028", "PED-2026-0028", "Natália Vieira Campos", "(11)91234-0028",
         "Kit primeiros socorros hospital", "Rua Ministro Rocha Azevedo, 456",
         -23.5610, -46.6560, 5.0, "critical", 92, "pending"),
        ("del-029", "PED-2026-0029", "Márcio Peixoto Junior", "(11)91234-0029",
         "Materiais promocionais", "Av. Santo Amaro, 1000 - Brooklin",
         -23.6040, -46.6760, 25.0, "low", 22, "pending"),
        ("del-030", "PED-2026-0030", "Sandra Borges Cavalcanti", "(11)91234-0030",
         "Documentos cartório", "Rua Peixoto Gomide, 996 - Cerqueira César",
         -23.5580, -46.6530, 0.5, "high", 77, "pending"),
    ]


    # Entregas com falha
    failed = [
        ("del-031", "PED-2026-0031", "Renato Luz Cavalcante", "(11)91234-0031",
         "Tentativa anterior falhou - cliente ausente",
         "Rua Bandeira Paulista, 530 - Itaim",
         -23.5800, -46.6740, 8.0, "high", 83, "failed"),
        ("del-032", "PED-2026-0032", "Cláudia Ramos Duarte", "(11)91234-0032",
         "Endereço incorreto - aguardando novo endereço",
         "Av. Europa, 655 - Jardim Europa",
         -23.5710, -46.6700, 3.0, "normal", 60, "failed"),
    ]

    # Entregas canceladas
    cancelled = [
        ("del-033", "PED-2026-0033", "Empresa XYZ Ltda", "(11)91234-0033",
         "CANCELADO pelo cliente",
         "Rua Olimpíadas, 100 - Vila Olímpia",
         -23.5950, -46.6850, 50.0, "normal", 50, "cancelled"),
    ]

    all_deliveries = deliveries + pending + more_pending + failed + cancelled

    for d in all_deliveries:
        # Gerar janelas de tempo para parte das entregas
        tw_start = None
        tw_end = None
        if d[9] in ("critical", "high") and d[11] == "pending":
            tw_start = (NOW + timedelta(hours=random.randint(0, 2))).isoformat()
            tw_end = (NOW + timedelta(hours=random.randint(3, 6))).isoformat()

        confirmed_at = d[13] if len(d) > 13 else None
        receiver = d[12] if len(d) > 12 and d[11] == "confirmed" else None

        db.execute(
            """INSERT INTO deliveries
               (id, order_number, customer_name, customer_phone, description,
                address, lat, lng, weight_kg, priority, priority_score,
                status, time_window_start, time_window_end,
                confirmed_at, receiver_name, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
             d[9], d[10], d[11], tw_start, tw_end,
             confirmed_at, receiver, (NOW - timedelta(hours=3)).isoformat())
        )

    print(f"[3/4] {len(all_deliveries)} entregas criadas")
    print(f"       - {len(deliveries[:3])} confirmadas")
    print(f"       - {len(deliveries[3:])} em rota")
    print(f"       - {len(pending) + len(more_pending)} pendentes")
    print(f"       - {len(failed)} falhadas")
    print(f"       - {len(cancelled)} canceladas")



def create_incidents(db):
    """Cria 12 incidentes Waze realistas em São Paulo."""
    incidents = [
        # (id, lat, lng, rua, cidade, tipo, severidade, descrição, delay_s, velocidade)
        ("inc-001", -23.5615, -46.6550, "Av. Paulista (altura MASP)",
         "São Paulo", "accident", 5,
         "Colisão entre 3 veículos. Faixa esquerda bloqueada. Atendimento SAMU no local.",
         1800, 5.0),
        ("inc-002", -23.5730, -46.6880, "Av. Brig. Faria Lima (Pinheiros)",
         "São Paulo", "jam", 4,
         "Congestionamento severo sentido Butantã. Velocidade média 8km/h.",
         900, 8.0),
        ("inc-003", -23.5550, -46.6500, "Rua da Consolação (Higienópolis)",
         "São Paulo", "construction", 3,
         "Obra SABESP - faixa direita interditada até 18h.",
         420, 20.0),
        ("inc-004", -23.5650, -46.6700, "Av. Rebouças (altura Pinheiros)",
         "São Paulo", "hazard", 3,
         "Buraco grande na faixa central. Risco de dano ao veículo.",
         240, 25.0),
        ("inc-005", -23.5900, -46.6900, "Marginal Pinheiros (Pte. Cidade Jardim)",
         "São Paulo", "jam", 5,
         "Congestionamento total - acidente anterior. Tempo parado estimado 25min.",
         1500, 3.0),
        ("inc-006", -23.5480, -46.6350, "Rua Vergueiro (Liberdade)",
         "São Paulo", "police", 2,
         "Blitz policial - fiscalização documental. Fila de 200m.",
         180, 15.0),
        ("inc-007", -23.5820, -46.6820, "Rua Funchal (Vila Olímpia)",
         "São Paulo", "road_closed", 4,
         "Via interditada por evento. Desvio pela Rua Olimpíadas.",
         600, 0.0),
        ("inc-008", -23.5570, -46.6750, "Rua Teodoro Sampaio (Pinheiros)",
         "São Paulo", "jam", 3,
         "Congestionamento moderado por carga/descarga em fila dupla.",
         360, 12.0),
        ("inc-009", -23.5960, -46.6870, "Av. Eng. Luís Carlos Berrini",
         "São Paulo", "accident", 4,
         "Moto x carro. Faixa bloqueada. Motorista consciente.",
         720, 10.0),
        ("inc-010", -23.5690, -46.6620, "Rua Groenlândia (Jardim América)",
         "São Paulo", "flood", 3,
         "Ponto de alagamento após chuva forte. Nível 20cm.",
         480, 8.0),
        ("inc-011", -23.5510, -46.6430, "Av. Liberdade (Liberdade)",
         "São Paulo", "hazard", 2,
         "Semáforo apagado no cruzamento. Trânsito lento.",
         120, 18.0),
        ("inc-012", -23.5850, -46.6750, "Av. Santo Amaro (Brooklin)",
         "São Paulo", "jam", 3,
         "Fluxo intenso sentido Centro. Normal para horário.",
         300, 15.0),
    ]

    for inc in incidents:
        db.execute(
            """INSERT INTO incidents
               (id, lat, lng, street, city, incident_type, severity,
                description, delay_seconds, speed_kmh, is_active, reported_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,1,?)""",
            (*inc, (NOW - timedelta(minutes=random.randint(5, 60))).isoformat())
        )

    print(f"[4/4] {len(incidents)} incidentes Waze criados")
    sev_counts = {}
    for i in incidents:
        t = i[5]
        sev_counts[t] = sev_counts.get(t, 0) + 1
    for t, c in sorted(sev_counts.items()):
        print(f"       - {t}: {c}")



def create_routes(db):
    """Cria 3 rotas ativas com stops vinculados."""
    routes = [
        # Rota do Carlos (drv-001) - 7 stops, 3 já entregues
        {
            "id": "rte-001",
            "driver_id": "drv-001",
            "status": "active",
            "origin_lat": -23.5505,
            "origin_lng": -46.6333,
            "total_distance_km": 18.3,
            "total_duration_minutes": 45.0,
            "total_stops": 7,
            "completed_stops": 3,
            "optimization_score": 87.5,
            "stops": [
                ("del-001", 1, True, 2.8, 4.2),
                ("del-002", 2, True, 1.5, 2.3),
                ("del-003", 3, True, 2.1, 3.2),
                ("del-004", 4, False, 3.3, 5.0),
                ("del-005", 5, False, 1.8, 2.7),
                ("del-009", 6, False, 2.2, 3.3),
                ("del-010", 7, False, 2.5, 3.8),
            ]
        },
        # Rota da Ana (drv-002) - 5 stops, 0 entregues
        {
            "id": "rte-002",
            "driver_id": "drv-002",
            "status": "active",
            "origin_lat": -23.5631,
            "origin_lng": -46.6542,
            "total_distance_km": 12.7,
            "total_duration_minutes": 35.0,
            "total_stops": 5,
            "completed_stops": 0,
            "optimization_score": 91.2,
            "stops": [
                ("del-006", 1, False, 2.4, 3.6),
                ("del-007", 2, False, 1.9, 2.9),
                ("del-008", 3, False, 3.1, 4.7),
                ("del-011", 4, False, 2.0, 3.0),
                ("del-012", 5, False, 1.8, 2.7),
            ]
        },
        # Rota da Juliana (drv-006) - 4 stops, 0 entregues
        {
            "id": "rte-003",
            "driver_id": "drv-006",
            "status": "active",
            "origin_lat": -23.5750,
            "origin_lng": -46.6850,
            "total_distance_km": 9.8,
            "total_duration_minutes": 28.0,
            "total_stops": 4,
            "completed_stops": 0,
            "optimization_score": 93.0,
            "stops": [
                ("del-013", 1, False, 2.2, 3.3),
                ("del-016", 2, False, 1.5, 2.3),
                ("del-018", 3, False, 2.8, 4.2),
                ("del-019", 4, False, 3.0, 4.5),
            ]
        },
    ]

    for route in routes:
        started = (NOW - timedelta(hours=1)).isoformat()
        db.execute(
            """INSERT INTO routes
               (id, driver_id, status, origin_lat, origin_lng,
                total_distance_km, total_duration_minutes, total_stops,
                completed_stops, optimization_score, last_optimized_at, started_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (route["id"], route["driver_id"], route["status"],
             route["origin_lat"], route["origin_lng"],
             route["total_distance_km"], route["total_duration_minutes"],
             route["total_stops"], route["completed_stops"],
             route["optimization_score"], NOW.isoformat(), started)
        )

        for stop in route["stops"]:
            del_id, seq, completed, dist, dur = stop
            eta = (NOW + timedelta(minutes=seq * 8)).isoformat()
            incidents = random.randint(0, 2)
            stop_id = gen_id()
            arrived = (NOW - timedelta(minutes=random.randint(10, 50))).isoformat() if completed else None
            db.execute(
                """INSERT INTO route_stops
                   (id, route_id, delivery_id, sequence_order, is_completed,
                    distance_from_previous_km, duration_from_previous_min,
                    eta, waze_incidents_on_path, arrived_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (stop_id, route["id"], del_id, seq, 1 if completed else 0,
                 dist, dur, eta, incidents, arrived)
            )

            # Vincular entrega à rota
            status = "confirmed" if completed else "en_route"
            db.execute(
                "UPDATE deliveries SET route_id=?, sequence_order=?, status=? WHERE id=?",
                (route["id"], seq, status, del_id)
            )

    print(f"[5/4] {len(routes)} rotas ativas criadas com {sum(r['total_stops'] for r in routes)} stops")


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fleet_demo.db")
NOW = datetime(2026, 7, 28, 9, 30, 0)


def gen_id():
    return str(uuid.uuid4())[:8]


if __name__ == "__main__":
    main()
