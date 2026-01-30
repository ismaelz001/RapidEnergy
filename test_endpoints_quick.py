#!/usr/bin/env python
import requests
import json

print('='*70)
print('🚀 TESTING ENDPOINTS EN RENDER')
print('='*70)

BASE = 'https://rapidenergy.onrender.com'

# Test 1: Tarifas stats
print('\n📊 TEST 1: GET /debug/tarifas/stats')
print('-'*70)
try:
    r = requests.get(f'{BASE}/debug/tarifas/stats', timeout=20)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print('✅ Respuesta OK')
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
    else:
        print(f'❌ Error: {r.text[:300]}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: Comparador
print('\n\n🔍 TEST 2: POST /debug/comparador/factura/285')
print('-'*70)
try:
    r = requests.post(f'{BASE}/debug/comparador/factura/285', timeout=20)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print('✅ Respuesta OK')
        print(f'  Ofertas totales: {data.get("ofertas_totales")}')
        print(f'  Con ahorro: {data.get("ofertas_con_ahorro")}')
        print(f'  Sin ahorro: {data.get("ofertas_sin_ahorro")}')
        baseline = data.get("baseline_actual")
        if baseline:
            print(f'  Baseline: {baseline}€')
        print(f'  Método: {data.get("baseline_method")}')
    else:
        print(f'Status {r.status_code}')
        print(f'Error: {r.text[:300]}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 3: PDF
print('\n\n📄 TEST 3: GET /webhook/facturas/285/presupuesto.pdf')
print('-'*70)
try:
    r = requests.head(f'{BASE}/webhook/facturas/285/presupuesto.pdf', timeout=20)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        size = r.headers.get('content-length', '?')
        print(f'✅ PDF disponible ({size} bytes)')
    else:
        print(f'⚠️ Status {r.status_code}')
except Exception as e:
    print(f'❌ Error: {e}')

print('\n' + '='*70)
