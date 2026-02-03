#!/usr/bin/env python3
"""
Suite de testeos pre-deploy: Validaciones adicionales
"""
import sys
sys.path.insert(0, '.')
from app.services.ocr import extract_data_from_pdf
import json
from pathlib import Path

print("=" * 100)
print("SUITE PRE-DEPLOY: VALIDACIONES ADICIONALES")
print("=" * 100)

test_files = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf",
    "Endesa": "temp_facturas/Factura.pdf",
    "HC_Energia": "temp_facturas/Fra Agosto.pdf"
}

# Cargar ground truth
with open("temp_facturas/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

print("\n[TEST 1] Validación de tipos de datos")
print("-" * 100)
for company, pdf_path in test_files.items():
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    
    # Validar tipos
    errors = []
    if result.get("consumo_kwh") and not isinstance(result["consumo_kwh"], (int, float)):
        errors.append(f"consumo_kwh: {type(result['consumo_kwh'])}")
    if result.get("dias_facturados") and not isinstance(result["dias_facturados"], (int, float)):
        errors.append(f"dias_facturados: {type(result['dias_facturados'])}")
    if result.get("total_factura") and not isinstance(result["total_factura"], (int, float)):
        errors.append(f"total_factura: {type(result['total_factura'])}")
    
    status = "✅ OK" if not errors else f"❌ FAIL: {errors}"
    print(f"{company:15} {status}")

print("\n[TEST 2] Validación de rangos de valores")
print("-" * 100)
for company, pdf_path in test_files.items():
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    
    errors = []
    if result.get("dias_facturados"):
        dias = result["dias_facturados"]
        # Aceptar períodos desde 1 día (incluyendo facturas parciales y períodos > 32 días)
        if not (1 <= dias <= 370):
            errors.append(f"dias_facturados {dias} fuera de rango [1-370]")
    
    if result.get("consumo_kwh"):
        consumo = result["consumo_kwh"]
        if consumo < 0 or consumo > 10000:
            errors.append(f"consumo_kwh {consumo} fuera de rango [0-10000]")
    
    if result.get("total_factura"):
        total = result["total_factura"]
        if total < 0 or total > 1000:
            errors.append(f"total_factura {total} fuera de rango [0-1000]")
    
    status = "✅ OK" if not errors else f"❌ FAIL: {errors}"
    print(f"{company:15} {status}")

print("\n[TEST 3] Validación de fechas (ISO format)")
print("-" * 100)
import re
for company, pdf_path in test_files.items():
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    
    errors = []
    iso_pattern = r"^\d{4}-\d{2}-\d{2}$"
    
    if result.get("fecha_inicio_consumo"):
        if not re.match(iso_pattern, result["fecha_inicio_consumo"]):
            errors.append(f"fecha_inicio: formato incorrecto {result['fecha_inicio_consumo']}")
    
    if result.get("fecha_fin_consumo"):
        if not re.match(iso_pattern, result["fecha_fin_consumo"]):
            errors.append(f"fecha_fin: formato incorrecto {result['fecha_fin_consumo']}")
    
    status = "✅ OK" if not errors else f"❌ FAIL: {errors}"
    print(f"{company:15} {status}")

print("\n[TEST 4] Validación de coherencia (relaciones entre campos)")
print("-" * 100)
for company, pdf_path in test_files.items():
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    
    errors = []
    
    # Si tenemos consumos por periodo, suma debe estar próxima a consumo_total
    consumos_periodo = [result.get(f"consumo_p{i}_kwh") for i in [1,2,3,4] if result.get(f"consumo_p{i}_kwh")]
    if consumos_periodo and result.get("consumo_kwh"):
        suma = sum(consumos_periodo)
        consumo_total = result["consumo_kwh"]
        diff_pct = abs(suma - consumo_total) / max(suma, consumo_total) * 100 if max(suma, consumo_total) > 0 else 0
        if diff_pct > 15:  # 15% de tolerancia
            errors.append(f"suma_periodos {suma:.2f} vs consumo_total {consumo_total:.2f} (diff {diff_pct:.1f}%)")
    
    # Validar ATR
    atr = result.get("atr")
    if atr and not re.match(r"^[0-9]\.[0-9]TD$", atr):
        errors.append(f"ATR formato incorrecto: {atr}")
    
    status = "✅ OK" if not errors else f"⚠️  WARN: {errors}"
    print(f"{company:15} {status}")

print("\n[TEST 5] Validación de campos críticos (no None)")
print("-" * 100)
critical_fields = ["titular", "cups", "atr", "fecha_inicio_consumo", "fecha_fin_consumo", 
                  "dias_facturados", "consumo_kwh", "potencia_p1_kw", "total_factura"]

for company, pdf_path in test_files.items():
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    
    missing = [f for f in critical_fields if result.get(f) is None]
    status = f"✅ OK ({len(critical_fields)}/{len(critical_fields)})" if not missing else f"❌ MISSING: {missing}"
    print(f"{company:15} {status}")

print("\n" + "=" * 100)
print("PRE-DEPLOY TESTS COMPLETADOS")
print("=" * 100)
