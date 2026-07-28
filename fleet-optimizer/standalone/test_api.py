#!/usr/bin/env python3
"""
Teste completo da API do Fleet Route Optimizer.
Roda o servidor em thread, executa requests, e reporta resultados.
"""
import threading
import time
import json
import urllib.request
import urllib.error
import sys
import os

# Importar o módulo do servidor
sys.path.insert(0, os.path.dirname(__file__))

# Preparar o servidor
import importlib.util
spec = importlib.util.spec_from_file_location("server", os.path.join(os.path.dirname(__file__), "server.py"))
srv_module = importlib.util.module_from_spec(spec)

# Execute apenas as definições, não o main()
exec(open(os.path.join(os.path.dirname(__file__), "server.py")).read().replace(
    'if __name__ == "__main__":\n    main()', ''
))

# Inicializar banco e dados
init_db()
seed_data()

# Iniciar servidor em thread
from http.server import ThreadingHTTPServer
PORT = 9876
server = ThreadingHTTPServer(("127.0.0.1", PORT), FleetAPIHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(0.5)

BASE = f"http://127.0.0.1:{PORT}"
passed = 0
failed = 0


def test(method, path, body=None, expected_status=200, description=""):
    global passed, failed
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    
    try:
        resp = urllib.request.urlopen(req)
        status = resp.status
        result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        status = e.code
        result = json.loads(e.read().decode())
    except Exception as e:
        print(f"  FAIL [{method} {path}] {description} - Exception: {e}")
        failed += 1
        return None

    ok = status == expected_status
    if ok:
        passed += 1
        print(f"  PASS [{method} {path}] {description} (HTTP {status})")
    else:
        failed += 1
        print(f"  FAIL [{method} {path}] {description} - Got HTTP {status}, expected {expected_status}")
        print(f"       Response: {json.dumps(result, ensure_ascii=False)[:200]}")
    
    return result


print("=" * 70)
print("  FLEET ROUTE OPTIMIZER - API Validation Tests")
print("=" * 70)

# --- 1. Health Check ---
print("\n1. Health Check")
r = test("GET", "/health", description="Health endpoint")

# --- 2. Dashboard Stats ---
print("\n2. Dashboard Stats")
r = test("GET", "/api/v1/dashboard/stats", description="Get dashboard statistics")
if r:
    assert r["total_drivers"] == 4, f"Expected 4 drivers, got {r['total_drivers']}"
    assert r["pending_deliveries"] == 10, f"Expected 10 pending, got {r['pending_deliveries']}"
    assert r["active_incidents"] == 5, f"Expected 5 incidents, got {r['active_incidents']}"
    print(f"       -> {r['total_drivers']} motoristas, {r['pending_deliveries']} pendentes, {r['active_incidents']} incidentes")

# --- 3. Drivers ---
print("\n3. Motoristas")
r = test("GET", "/api/v1/drivers", description="List all drivers")
if r:
    print(f"       -> {len(r)} motoristas retornados")
    for d in r:
        print(f"          {d['name']} | {d['status']} | loc=({d['current_lat']},{d['current_lng']})")

# --- 4. Deliveries ---
print("\n4. Entregas")
r = test("GET", "/api/v1/deliveries", description="List all deliveries")
if r:
    print(f"       -> {len(r)} entregas retornadas")
    for d in r[:5]:
        print(f"          {d['order_number']} | {d['priority']}(score:{d['priority_score']}) | {d['status']}")
    if len(r) > 5:
        print(f"          ... e mais {len(r)-5}")

# --- 5. Incidents ---
print("\n5. Incidentes Waze")
r = test("GET", "/api/v1/incidents", description="List active incidents")
if r:
    print(f"       -> {len(r)} incidentes ativos")
    for i in r:
        print(f"          {i['incident_type']} | sev:{i['severity']} | {i['street']} | +{i['delay_seconds']}s")

# --- 6. Optimize Route ---
print("\n6. Otimização de Rota (CORE FEATURE)")
r = test("POST", "/api/v1/routes/optimize",
         body={"driver_id": "d1"},
         expected_status=201,
         description="Optimize route for driver d1 (Carlos Silva)")
if r:
    print(f"       -> Rota criada: {r['id']}")
    print(f"       -> Total: {r['total_distance_km']}km | {r['total_duration_minutes']}min | Score: {r['optimization_score']}")
    print(f"       -> Paradas: {r['total_stops']}")
    route_id = r["id"]
    if "stops" in r:
        print("       -> Sequência otimizada:")
        for s in r["stops"][:5]:
            print(f"          #{s['sequence_order']} | {s['distance_from_previous_km']}km | {s['duration_from_previous_min']}min | incidents:{s['waze_incidents_on_path']}")

# --- 7. Confirm Delivery (triggers re-optimization) ---
print("\n7. Confirmação de Entrega + Re-Otimização Automática")
r = test("POST", "/api/v1/deliveries/del01/confirm",
         body={
             "receiver_name": "João Mendes (confirmado)",
             "notes": "Recebido em mãos",
             "lat": -23.5537,
             "lng": -46.6580
         },
         description="Confirm delivery del01 and trigger re-optimization")
if r:
    print(f"       -> Status: {r['status']}")
    print(f"       -> Confirmado em: {r['confirmed_at']}")
    print(f"       -> Re-otimizado: {r.get('re_optimized', False)}")
    print(f"       -> Msg: {r['message']}")

# --- 8. Check routes after re-optimization ---
print("\n8. Verificar Rota Após Re-Otimização")
r = test("GET", "/api/v1/routes", description="Get routes after re-optimization")
if r and len(r) > 0:
    route = r[0]
    print(f"       -> Rota {route['id']}: {route['completed_stops']}/{route['total_stops']} stops")
    print(f"       -> Distância atualizada: {route['total_distance_km']}km")

# --- 9. Override Priority (Manager intervention) ---
print("\n9. Override de Prioridade (Intervenção do Gestor)")
# Pegar entregas restantes na rota
deliveries_resp = test("GET", "/api/v1/deliveries", description="Get current deliveries")
if deliveries_resp and route_id:
    assigned = [d for d in deliveries_resp if d["status"] == "assigned"]
    if len(assigned) >= 2:
        # Inverter a ordem dos 2 primeiros
        new_order = [assigned[1]["id"], assigned[0]["id"]] + [d["id"] for d in assigned[2:]]
        r = test("POST", f"/api/v1/routes/{route_id}/override-priority",
                 body={"delivery_ids_ordered": new_order, "reason": "Cliente VIP precisa urgente"},
                 description="Manager overrides delivery order")
        if r:
            print(f"       -> Nova ordem definida pelo gestor")
            print(f"       -> Motivo: {r.get('reason')}")

# --- 10. Update delivery priority ---
print("\n10. Alterar Prioridade de Entrega")
r = test("PATCH", "/api/v1/deliveries/del07",
         body={"priority": "critical", "priority_score": 100},
         description="Elevate del07 to critical priority")
if r:
    print(f"       -> {r['order_number']}: {r['priority']} (score: {r['priority_score']})")

# --- 11. Update driver location ---
print("\n11. Atualizar Localização do Motorista")
r = test("PATCH", "/api/v1/drivers/d1/location",
         body={"lat": -23.5550, "lng": -46.6600},
         description="Update Carlos Silva location")
if r:
    print(f"       -> Nova posição: ({r['lat']}, {r['lng']})")

# --- Summary ---
print("\n" + "=" * 70)
print(f"  RESULTADOS: {passed} PASSED | {failed} FAILED | {passed+failed} TOTAL")
print("=" * 70)

if failed > 0:
    print("\n  *** ALGUNS TESTES FALHARAM ***")
    sys.exit(1)
else:
    print("\n  *** TODOS OS TESTES PASSARAM ***")
    print("  Sistema validado com sucesso no sandbox!")

server.shutdown()
