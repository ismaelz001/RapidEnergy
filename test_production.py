#!/usr/bin/env python3
"""Production test for OCR extraction"""
import sys
sys.path.insert(0, '.')
from app.services.ocr import parse_invoice_text

# Test factura 285 (la que tenía el bug)
test_285 = """FACTURA Nº 285
PERIODO DE CONSUMO: 1 de enero a 31 de enero de 2025
DÍAS: 31

Potencia Contratada:
P1: 3.3 kW
P2: 1.5 kW

Consumos Desagregados:
P1 (Punta): 59 kWh
P2 (Llano): 0 kWh
P3 (Valle): 245 kWh

TOTAL FACTURA: 45.23 EUR
"""

result = parse_invoice_text(test_285)
print("\n=== FACTURA 285 PRODUCCION TEST ===\n")
print(f"P1 Potencia (kW): {result.get('potencia_p1_kw')} [DEBE SER 3.3]")
print(f"P2 Potencia (kW): {result.get('potencia_p2_kw')} [DEBE SER 1.5]")
print(f"P1 Consumo (kWh): {result.get('consumo_p1_kwh')} [DEBE SER 59]")
print(f"P2 Consumo (kWh): {result.get('consumo_p2_kwh')} [DEBE SER 0 o NONE]")
print(f"P3 Consumo (kWh): {result.get('consumo_p3_kwh')} [DEBE SER 245]")
print(f"Días: {result.get('dias_facturados')} [DEBE SER 31]")

# Validation
tests_passed = 0
tests_total = 6

if result.get('potencia_p1_kw') == 3.3:
    print("\n✓ P1 Potencia CORRECTO")
    tests_passed += 1
else:
    print(f"\n✗ P1 Potencia INCORRECTO: {result.get('potencia_p1_kw')} != 3.3")

if result.get('potencia_p2_kw') == 1.5:
    print("✓ P2 Potencia CORRECTO")
    tests_passed += 1
else:
    print(f"✗ P2 Potencia INCORRECTO: {result.get('potencia_p2_kw')} != 1.5")

if result.get('consumo_p1_kwh') == 59:
    print("✓ P1 Consumo CORRECTO")
    tests_passed += 1
else:
    print(f"✗ P1 Consumo INCORRECTO: {result.get('consumo_p1_kwh')} != 59")

if result.get('consumo_p2_kwh') in (0, None):
    print("✓ P2 Consumo CORRECTO")
    tests_passed += 1
else:
    print(f"✗ P2 Consumo INCORRECTO: {result.get('consumo_p2_kwh')} debería ser 0 o NONE")

if result.get('consumo_p3_kwh') == 245:
    print("✓ P3 Consumo CORRECTO")
    tests_passed += 1
else:
    print(f"✗ P3 Consumo INCORRECTO: {result.get('consumo_p3_kwh')} != 245")

if result.get('dias_facturados') == 31:
    print("✓ Días CORRECTO")
    tests_passed += 1
else:
    print(f"✗ Días INCORRECTO: {result.get('dias_facturados')} != 31")

print(f"\n[RESULTADO] {tests_passed}/{tests_total} tests pasados")
if tests_passed == tests_total:
    print("✓✓✓ LISTO PARA PRODUCCION ✓✓✓")
else:
    print(f"✗✗✗ FALLOS DETECTADOS ({tests_total - tests_passed} errores) ✗✗✗")
