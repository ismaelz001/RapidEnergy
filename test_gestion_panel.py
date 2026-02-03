"""
Test manual del panel de gestión
"""
import requests
import json
from time import sleep

API_BASE = "http://localhost:8888"

print("🧪 TESTING PANEL DE GESTIÓN\n")
print("=" * 60)

# Test 1: CEO Stats
print("\n✅ TEST 1: GET /api/stats/ceo")
try:
    r = requests.get(f"{API_BASE}/api/stats/ceo", timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   📊 Facturas procesadas: {data['total_facturas_procesadas']}")
        print(f"   💰 Ahorro generado: €{data['total_ahorro_generado']:.2f}")
        print(f"   💳 Comisiones pendientes: €{data['comisiones_pendientes']:.2f}")
        print(f"   👥 Asesores activos: {data['asesores_activos']}")
        print(f"   ⚠️  Alertas: {len(data['alertas'])}")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Actividad Reciente
print("\n✅ TEST 2: GET /api/stats/actividad-reciente")
try:
    r = requests.get(f"{API_BASE}/api/stats/actividad-reciente", timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        actividades = r.json()
        print(f"   📝 Actividades encontradas: {len(actividades)}")
        for act in actividades[:3]:
            print(f"      - {act['tipo']}: {act['descripcion'][:50]}...")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Listar Comisiones (pendientes)
print("\n✅ TEST 3: GET /api/comisiones?estado=pendiente")
try:
    r = requests.get(f"{API_BASE}/api/comisiones", params={"estado": "pendiente"}, timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        comisiones = r.json()
        print(f"   💳 Comisiones pendientes: {len(comisiones)}")
        for com in comisiones[:3]:
            print(f"      - Factura #{com['factura_id']}: €{com['comision_total_eur']:.2f} - {com['estado']}")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Healthcheck
print("\n✅ TEST 4: GET /health (verificar que el servidor responde)")
try:
    r = requests.get(f"{API_BASE}/health", timeout=5)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✅ Servidor OK")
    else:
        print(f"   ⚠️  Respuesta inesperada")
except Exception as e:
    # Health endpoint puede no existir
    print(f"   ℹ️  Endpoint /health no disponible (normal)")

print("\n" + "=" * 60)
print("✅ Tests completados")
