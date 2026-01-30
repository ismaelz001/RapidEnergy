#!/usr/bin/env python
import requests
import json

print('='*70)
print('🚀 QA AUDIT - FACTURA #286')
print('='*70)

BASE = 'https://rapidenergy.onrender.com'

# Test 1: Comparador para factura 286
print('\n🔍 TEST 1: POST /debug/comparador/factura/286')
print('-'*70)
try:
    r = requests.post(f'{BASE}/debug/comparador/factura/286', timeout=20)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        print('✅ Respuesta OK')
        print(f'\n  Datos de la factura:')
        print(f'    Cliente: {data.get("cliente")}')
        print(f'    CUPS: {data.get("cups")}')
        print(f'    ATR: {data.get("atr")}')
        print(f'    Total: {data.get("total_factura")}€')
        print(f'    Consumo: {data.get("consumo_total")} kWh')
        print(f'    Período: {data.get("periodo_dias")} días')
        print(f'\n  Comparador:')
        print(f'    Ofertas totales: {data.get("ofertas_totales")}')
        print(f'    Con ahorro: {data.get("ofertas_con_ahorro")}')
        print(f'    Sin ahorro: {data.get("ofertas_sin_ahorro")}')
        print(f'    Baseline: {data.get("baseline_actual")}€')
        print(f'    Método: {data.get("baseline_method")}')
        
        # Mostrar mejores ofertas si las hay
        mejores = data.get("mejores_ofertas", [])
        if mejores:
            print(f'\n  Mejores ofertas:')
            for i, oferta in enumerate(mejores[:3], 1):
                print(f'    {i}. {oferta.get("nombre", "N/A")} - Ahorro: {oferta.get("ahorro_anual", 0)}€/año')
    else:
        print(f'Status {r.status_code}')
        print(f'Error: {r.text[:300]}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: PDF
print('\n\n📄 TEST 2: Generar PDF presupuesto')
print('-'*70)
try:
    r = requests.get(f'{BASE}/webhook/facturas/286/presupuesto.pdf', timeout=20, allow_redirects=True)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        print(f'✅ PDF generado ({len(r.content)} bytes)')
        print(f'Content-Type: {r.headers.get("content-type")}')
    else:
        print(f'Status {r.status_code}')
        print(f'Response: {r.text[:300]}')
except Exception as e:
    print(f'❌ Error: {e}')

print('\n' + '='*70)
