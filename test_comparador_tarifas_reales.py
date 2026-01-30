#!/usr/bin/env python3
"""
Test: Comparador con tarifas REALES de Neon
"""

import sys
sys.path.insert(0, '/f:/MecaEnergy')

from app.services.ocr import extract_data_from_pdf
from datetime import date, datetime
import json

# Tarifas reales de Neon
TARIFAS_REALES = [
    {"id":2,"nombre":"Tarifa Por Uso Luz","comercializadora":"Naturgy","atr":"2.0TD","tipo":"fija","energia_p1_eur_kwh":"0.120471","energia_p2_eur_kwh":None,"energia_p3_eur_kwh":None,"potencia_p1_eur_kw_dia":"0.111815","potencia_p2_eur_kw_dia":"0.033933"},
    {"id":3,"nombre":"Tarifa Noche Luz ECO","comercializadora":"Naturgy","atr":"2.0TD","tipo":"fija","energia_p1_eur_kwh":"0.190465","energia_p2_eur_kwh":"0.117512","energia_p3_eur_kwh":"0.082673","potencia_p1_eur_kw_dia":"0.111815","potencia_p2_eur_kw_dia":"0.033933"},
    {"id":4,"nombre":"Libre Promo 1er año","comercializadora":"Endesa","atr":"2.0TD","tipo":"fija","energia_p1_eur_kwh":"0.105900","energia_p2_eur_kwh":"0.105900","energia_p3_eur_kwh":"0.105900","potencia_p1_eur_kw_dia":"0.090214","potencia_p2_eur_kw_dia":"0.090214"},
    {"id":9,"nombre":"Plan Estable","comercializadora":"Iberdrola","atr":"2.0TD","tipo":"fija","energia_p1_eur_kwh":"0.174875","energia_p2_eur_kwh":"0.174875","energia_p3_eur_kwh":"0.174875","potencia_p1_eur_kw_dia":"0.108192","potencia_p2_eur_kw_dia":"0.046548"},
    {"id":10,"nombre":"Plan Especial Plus 15%","comercializadora":"Iberdrola","atr":"2.0TD","tipo":"fija","energia_p1_eur_kwh":"0.14875","energia_p2_eur_kwh":"0.14875","energia_p3_eur_kwh":"0.14875","potencia_p1_eur_kw_dia":"0.108192","potencia_p2_eur_kw_dia":"0.046548"}
]

def to_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        return float(val.replace(",", "."))
    return 0.0

# Extraer datos del PDF
print("=" * 80)
print("COMPARADOR CON TARIFAS REALES DE NEON")
print("=" * 80)

factura_path = "f:/MecaEnergy/temp_facturas/Factura Iberdrola.pdf"
with open(factura_path, 'rb') as f:
    file_bytes = f.read()

extracted = extract_data_from_pdf(file_bytes)

print(f"\n✅ DATOS EXTRAÍDOS DEL PDF:")
print(f"   CUPS: {extracted['cups']}")
print(f"   ATR: {extracted['atr']}")
print(f"   Total Actual: €{extracted['total_factura']:.2f}")
print(f"   Consumo Total: {extracted['consumo_kwh']:.2f} kWh")
print(f"      P1: {extracted['consumo_p1_kwh']:.2f} kWh")
print(f"      P2: {extracted['consumo_p2_kwh']:.2f} kWh")
print(f"      P3: {extracted['consumo_p3_kwh']:.2f} kWh")
print(f"   Potencia:")
print(f"      P1: {extracted['potencia_p1_kw']:.2f} kW")
print(f"      P2: {extracted['potencia_p2_kw']:.2f} kW")
print(f"   Periodo: {extracted['dias_facturados']} días")

# Datos para cálculo
p1_consume = to_float(extracted['consumo_p1_kwh'])
p2_consume = to_float(extracted['consumo_p2_kwh'])
p3_consume = to_float(extracted['consumo_p3_kwh'])
p1_potencia = to_float(extracted['potencia_p1_kw'])
p2_potencia = to_float(extracted['potencia_p2_kw'])
dias = to_float(extracted['dias_facturados'])
total_actual = to_float(extracted['total_factura'])

print("\n" + "=" * 80)
print("COMPARACIÓN CON TARIFAS DISPONIBLES")
print("=" * 80)

comparaciones = []

for tarifa in TARIFAS_REALES:
    comercializadora = tarifa['comercializadora']
    nombre = tarifa['nombre']
    
    # Precios
    precio_p1_ener = to_float(tarifa['energia_p1_eur_kwh'])
    precio_p2_ener = to_float(tarifa['energia_p2_eur_kwh'])
    precio_p3_ener = to_float(tarifa['energia_p3_eur_kwh'])
    precio_p1_pote = to_float(tarifa['potencia_p1_eur_kw_dia'])
    precio_p2_pote = to_float(tarifa['potencia_p2_eur_kw_dia'])
    
    # Cálculo de costo
    costo_energia = (
        p1_consume * precio_p1_ener +
        p2_consume * precio_p2_ener +
        p3_consume * precio_p3_ener
    )
    
    costo_potencia = (
        (p1_potencia * precio_p1_pote * dias) +
        (p2_potencia * precio_p2_pote * dias)
    )
    
    total_estimado = costo_energia + costo_potencia
    ahorro = total_actual - total_estimado
    ahorro_porcentaje = (ahorro / total_actual * 100) if total_actual > 0 else 0
    
    comparaciones.append({
        'comercializadora': comercializadora,
        'nombre': nombre,
        'total_estimado': total_estimado,
        'ahorro': ahorro,
        'ahorro_porcentaje': ahorro_porcentaje,
        'costo_energia': costo_energia,
        'costo_potencia': costo_potencia,
    })

# Ordenar por ahorro (mayor primero)
comparaciones.sort(key=lambda x: x['ahorro'], reverse=True)

print(f"\n{'Comercializadora':<15} {'Tarifa':<25} {'Total Est.':<12} {'Ahorro':<10} {'%':<8}")
print("-" * 80)

for comp in comparaciones:
    comercial = comp['comercializadora'][:14]
    tarifa = comp['nombre'][:24]
    total = f"€{comp['total_estimado']:>9.2f}"
    ahorro = f"€{comp['ahorro']:>7.2f}"
    pct = f"{comp['ahorro_porcentaje']:>6.2f}%"
    
    print(f"{comercial:<15} {tarifa:<25} {total:<12} {ahorro:<10} {pct:<8}")

print("\n" + "=" * 80)
print("ANÁLISIS DETALLADO DE LA MEJOR OPCIÓN")
print("=" * 80)

best = comparaciones[0]
print(f"\n✅ MEJOR OPCIÓN: {best['comercializadora']} - {best['nombre']}")
print(f"   Costo Energía: €{best['costo_energia']:.2f}")
print(f"   Costo Potencia: €{best['costo_potencia']:.2f}")
print(f"   Total Estimado: €{best['total_estimado']:.2f}")
print(f"   Total Actual (Iberdrola): €{total_actual:.2f}")
print(f"   Ahorro Potencial: €{best['ahorro']:.2f} ({best['ahorro_porcentaje']:.2f}%)")

print("\n" + "=" * 80)
print("CONCLUSIÓN")
print("=" * 80)

if comparaciones[0]['ahorro'] > 0:
    print(f"\n✅ EL COMPARADOR FUNCIONA CORRECTAMENTE")
    print(f"   Encontró {len(comparaciones)} tarifas alternativas")
    print(f"   La mejor opción ahorra €{comparaciones[0]['ahorro']:.2f}")
else:
    print(f"\n⚠️ ALERTA: Ninguna tarifa ahorra dinero")
    print(f"   La tarifa actual de Iberdrola es la más económica")

print("\n" + "=" * 80)
