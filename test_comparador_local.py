#!/usr/bin/env python3
"""
Test: Verificar que el comparador tiene todos los datos que necesita
"""

import sys
sys.path.insert(0, '/f:/MecaEnergy')

from app.services.ocr import extract_data_from_pdf
from datetime import date
import json

# Extraer datos del PDF
print("=" * 70)
print("VERIFICACIÓN: TODOS LOS DATOS NECESARIOS PARA COMPARADOR")
print("=" * 70)

factura_path = "f:/MecaEnergy/temp_facturas/Factura Iberdrola.pdf"
with open(factura_path, 'rb') as f:
    file_bytes = f.read()

extracted = extract_data_from_pdf(file_bytes)

print(f"\n✅ DATOS EXTRAÍDOS DEL OCR:")

# Campos requeridos por el comparador
required_fields = {
    "CUPS": ("cups", True),
    "ATR": ("atr", True),
    "Total Factura": ("total_factura", True),
    "Período Días": ("dias_facturados", True),
    "Consumo Total": ("consumo_kwh", True),
    "Consumo P1": ("consumo_p1_kwh", True),
    "Consumo P2": ("consumo_p2_kwh", True),
    "Consumo P3": ("consumo_p3_kwh", True),
    "Potencia P1": ("potencia_p1_kw", True),
    "Potencia P2": ("potencia_p2_kw", True),
    "Fecha Inicio": ("fecha_inicio_consumo", True),
    "Fecha Fin": ("fecha_fin_consumo", True),
}

all_ok = True
for label, (field, required) in required_fields.items():
    value = extracted.get(field)
    
    # Check if valid
    is_valid = value is not None and (
        (isinstance(value, (int, float)) and value > 0) or
        (isinstance(value, str) and value.strip()) or
        (isinstance(value, date))
    )
    
    status = "✅" if is_valid else "❌"
    if required and not is_valid:
        all_ok = False
    
    print(f"   {status} {label:20} = {value}")

print("\n" + "=" * 70)
print("VALIDACIÓN PARA COMPARADOR 2.0TD")
print("=" * 70)

# Validaciones específicas del comparador 2.0TD
atr = extracted['atr']
print(f"\n🔍 ATR Detectado: {atr}")

if atr == "2.0TD":
    print("   ✅ Es 2.0TD - Requiere 3 períodos de energía")
    
    required_2td = {
        "Consumo P1": extracted.get('consumo_p1_kwh'),
        "Consumo P2": extracted.get('consumo_p2_kwh'),
        "Consumo P3": extracted.get('consumo_p3_kwh'),
        "Potencia P1": extracted.get('potencia_p1_kw'),
        "Potencia P2": extracted.get('potencia_p2_kw'),
    }
    
    consumo_sum = sum([v or 0 for v in [
        extracted.get('consumo_p1_kwh'),
        extracted.get('consumo_p2_kwh'),
        extracted.get('consumo_p3_kwh'),
    ]])
    
    print(f"\n   ✅ Suma consumos P1+P2+P3 = {consumo_sum} kWh")
    print(f"      Consumo total OCR = {extracted['consumo_kwh']} kWh")
    
    if abs(consumo_sum - extracted['consumo_kwh']) < 0.1:
        print(f"      ✅ COINCIDEN (diferencia < 0.1)")
        all_ok = all_ok and True
    else:
        print(f"      ⚠️  DIFERENCIA: {abs(consumo_sum - extracted['consumo_kwh']):.2f} kWh")
    
    for label, value in required_2td.items():
        status = "✅" if value else "❌"
        print(f"   {status} {label:20} = {value}")

print("\n" + "=" * 70)
print("RESULTADO FINAL")
print("=" * 70)

if all_ok:
    print("\n✅ TODOS LOS DATOS REQUERIDOS ESTÁN PRESENTES Y VÁLIDOS")
    print("   El comparador debería funcionar correctamente en producción")
else:
    print("\n❌ FALTAN DATOS O ESTÁN INVÁLIDOS")
    print("   El comparador podría fallar en producción")

print("\n" + "=" * 70)

