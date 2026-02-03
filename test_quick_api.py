"""Test rápido de endpoints del Panel CEO"""
import requests
import json

API = "http://localhost:8888"

print("🧪 TESTING PANEL CEO\n" + "="*60)

# Test 1: Stats CEO
print("\n✅ TEST 1: GET /api/stats/ceo")
try:
    r = requests.get(f"{API}/api/stats/ceo", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   📊 Facturas: {data['total_facturas_procesadas']}")
        print(f"   💰 Ahorro: €{data['total_ahorro_generado']:.2f}")
        print(f"   💳 Comisiones: €{data['comisiones_pendientes']:.2f}")
        print(f"   👥 Asesores: {data['asesores_activos']}")
        print(f"   ⚠️  Alertas: {len(data.get('alertas', []))}")
    else:
        print(f"   ❌ Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Listar users
print("\n✅ TEST 2: GET /api/users?role=comercial")
try:
    r = requests.get(f"{API}/api/users", params={"role": "comercial"}, timeout=5)
    if r.status_code == 200:
        users = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   👥 Comerciales: {len(users)}")
        for u in users[:3]:
            estado = "✅" if u['is_active'] else "🔴"
            print(f"      {estado} {u['name']} ({u['email']})")
    else:
        print(f"   ❌ Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Listar colaboradores
print("\n✅ TEST 3: GET /api/colaboradores")
try:
    r = requests.get(f"{API}/api/colaboradores", timeout=5)
    if r.status_code == 200:
        cols = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   🤝 Colaboradores: {len(cols)}")
    else:
        print(f"   ❌ Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Crear colaborador de prueba
print("\n✅ TEST 4: POST /api/colaboradores")
try:
    payload = {
        "nombre": "Pedro García TEST",
        "email": "pedro@test.com",
        "telefono": "600999888",
        "company_id": 1
    }
    r = requests.post(f"{API}/api/colaboradores", json=payload, timeout=5)
    if r.status_code == 201:
        data = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   ✅ Colaborador creado: ID {data['id']}")
    else:
        print(f"   ❌ Status: {r.status_code} - {r.text[:100]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Listar comisiones (pendientes)
print("\n✅ TEST 5: GET /api/comisiones?estado=pendiente")
try:
    r = requests.get(f"{API}/api/comisiones", params={"estado": "pendiente"}, timeout=5)
    if r.status_code == 200:
        comisiones = r.json()
        print(f"   Status: {r.status_code}")
        print(f"   💳 Comisiones pendientes: {len(comisiones)}")
    else:
        print(f"   ❌ Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("✅ TESTS COMPLETADOS")
print("\n💡 Servidor corriendo en http://localhost:8888")
print("📋 Docs API: http://localhost:8888/docs")
