#!/usr/bin/env python
import requests
import json

BASE = 'https://rapidenergy.onrender.com'

print('='*70)
print('🔍 ANÁLISIS DETALLADO FACTURA #286')
print('='*70)

# Obtener datos completos del endpoint debug
r = requests.post(f'{BASE}/debug/comparador/factura/286', timeout=20)
data = r.json()

print('\n📊 RESPUESTA COMPLETA:')
print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

print('\n' + '='*70)
print('📋 RESUMEN:')
print('='*70)
print(f'Status: {r.status_code}')
print(f'Ofertas con ahorro: {data.get("ofertas_con_ahorro")} de {data.get("ofertas_totales")}')
print(f'Baseline: {data.get("baseline_actual")}€')
print(f'Método baseline: {data.get("baseline_method")}')

# Si hay mejores ofertas
mejores = data.get("mejores_ofertas", [])
if mejores:
    print(f'\n🏆 TOP 3 MEJORES OFERTAS:')
    for i, oferta in enumerate(mejores[:3], 1):
        print(f'  {i}. {oferta.get("nombre", "Desconocida")}')
        print(f'     Ahorro/año: {oferta.get("ahorro_anual", 0)}€')
        print(f'     Precio: {oferta.get("precio_energia", "N/A")}€/kWh')
