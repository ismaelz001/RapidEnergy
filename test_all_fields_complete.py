#!/usr/bin/env python3
"""
Test exhaustivo de TODOS los campos contra ground truth
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr import extract_data_from_pdf

# Cargar ground truth
with open("temp_facturas/ground_truth.json", "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

test_files = {
    "Iberdrola": "temp_facturas/Factura Iberdrola.pdf",
    "Naturgy": "temp_facturas/factura Naturgy.pdf", 
    "Endesa": "temp_facturas/Factura.pdf",
    "HC_Energia": "temp_facturas/Fra Agosto.pdf"
}

print("=" * 100)
print("TEST EXHAUSTIVO DE TODOS LOS CAMPOS")
print("=" * 100)

total_tests = 0
passed_tests = 0
failed_tests = 0

for company, pdf_path in test_files.items():
    print(f"\n{'=' * 100}")
    print(f"TESTING: {company.upper()}")
    print(f"{'=' * 100}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    result = extract_data_from_pdf(pdf_bytes)
    gt = ground_truth[company]
    
    # Lista de campos a validar
    fields_to_check = [
        ("cliente", "titular", str, None),
        ("cups", "cups", str, None),
        ("atr", "atr", str, None),
        ("fecha_inicio_consumo", "fecha_inicio", str, None),
        ("fecha_fin_consumo", "fecha_fin", str, None),
        ("dias_facturados", "dias_facturados", int, 1),
        ("consumo_total_kwh", "consumo_kwh", float, 5.0),  # 5% tolerancia
        ("potencia_p1_kw", "potencia_p1_kw", float, 0.1),
        ("potencia_p2_kw", "potencia_p2_kw", float, 0.1),
        ("consumo_p1_kwh", "consumo_p1_kwh", float, 1.0),
        ("consumo_p2_kwh", "consumo_p2_kwh", float, 1.0),
        ("consumo_p3_kwh", "consumo_p3_kwh", float, 1.0),
        ("total_factura", "total_factura", float, 0.5),
        ("alquiler_contador", "alquiler_contador", float, 0.5),
        ("impuesto_electrico", "impuesto_electrico", float, 0.5),
        ("direccion", "direccion", str, None),
        ("localidad", "localidad", str, None),
    ]
    
    for ocr_field, gt_field, field_type, tolerance in fields_to_check:
        gt_val = gt.get(gt_field)
        
        # Skip si GT no tiene este campo
        if gt_val is None:
            continue
            
        total_tests += 1
        ocr_val = result.get(ocr_field)
        
        # Validación según tipo
        if field_type == str:
            # Para strings, normalizar y comparar
            if ocr_val:
                # SPECIAL CASE: Fechas en formato ISO son VÁLIDAS (2025-08-31 == 31/08/2025)
                if "fecha" in ocr_field and "/" in str(gt_val) and "-" in ocr_val:
                    # Convertir GT de DD/MM/YYYY a ISO para comparar
                    try:
                        from datetime import datetime
                        gt_date = datetime.strptime(str(gt_val), "%d/%m/%Y")
                        if ocr_val == gt_date.strftime("%Y-%m-%d"):
                            print(f"  OK {ocr_field}: {ocr_val} (ISO format)")
                            passed_tests += 1
                            continue
                    except:
                        pass
                
                ocr_normalized = ocr_val.upper().replace("Ó", "O").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ú", "U").replace("Ñ", "N")
                gt_normalized = str(gt_val).upper().replace("Ó", "O").replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ú", "U").replace("Ñ", "N")
                
                if ocr_normalized == gt_normalized:
                    print(f"  OK {ocr_field}: {ocr_val}")
                    passed_tests += 1
                else:
                    print(f"  FAIL {ocr_field}: OCR='{ocr_val}' vs GT='{gt_val}'")
                    failed_tests += 1
            else:
                print(f"  FAIL {ocr_field}: OCR=None vs GT='{gt_val}'")
                failed_tests += 1
                
        elif field_type == int:
            if ocr_val is not None:
                diff = abs(ocr_val - gt_val)
                if diff <= tolerance:
                    print(f"  OK {ocr_field}: {ocr_val} (GT={gt_val})")
                    passed_tests += 1
                else:
                    print(f"  FAIL {ocr_field}: OCR={ocr_val} vs GT={gt_val} (diff={diff})")
                    failed_tests += 1
            else:
                print(f"  FAIL {ocr_field}: OCR=None vs GT={gt_val}")
                failed_tests += 1
                
        elif field_type == float:
            if ocr_val is not None:
                # SPECIAL CASE: Impuesto eléctrico debe coincidir EXACTAMENTE (todos los decimales)
                if "impuesto" in ocr_field:
                    if abs(ocr_val - gt_val) < 0.01:  # Tolerancia mínima 1 céntimo
                        print(f"  OK {ocr_field}: {ocr_val} (exacto)")
                        passed_tests += 1
                    else:
                        print(f"  FAIL {ocr_field}: OCR={ocr_val} vs GT={gt_val} (debe ser exacto)")
                        failed_tests += 1
                elif isinstance(tolerance, float) and tolerance < 1:
                    # Tolerancia porcentual
                    diff_pct = abs(ocr_val - gt_val) / gt_val * 100 if gt_val != 0 else 0
                    if diff_pct <= tolerance * 100:
                        print(f"  OK {ocr_field}: {ocr_val:.2f} (GT={gt_val}, diff={diff_pct:.1f}%)")
                        passed_tests += 1
                    else:
                        print(f"  FAIL {ocr_field}: OCR={ocr_val:.2f} vs GT={gt_val} (diff={diff_pct:.1f}%)")
                        failed_tests += 1
                else:
                    # Tolerancia absoluta
                    diff = abs(ocr_val - gt_val)
                    if diff <= tolerance:
                        print(f"  OK {ocr_field}: {ocr_val:.2f} (GT={gt_val})")
                        passed_tests += 1
                    else:
                        print(f"  FAIL {ocr_field}: OCR={ocr_val:.2f} vs GT={gt_val} (diff={diff:.2f})")
                        failed_tests += 1
            else:
                print(f"  FAIL {ocr_field}: OCR=None vs GT={gt_val}")
                failed_tests += 1

print(f"\n{'=' * 100}")
print(f"RESUMEN FINAL - TODOS LOS CAMPOS")
print(f"{'=' * 100}")
print(f"Total tests: {total_tests}")
print(f"OK Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
print(f"FAIL Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

if passed_tests / total_tests >= 0.90:
    print(f"\n*** EXCELENTE: {passed_tests/total_tests*100:.1f}% accuracy - LISTO PARA DEPLOY ***")
elif passed_tests / total_tests >= 0.80:
    print(f"\n*** BUENO: {passed_tests/total_tests*100:.1f}% accuracy - Revisar fallos menores ***")
else:
    print(f"\n*** ATENCION: {passed_tests/total_tests*100:.1f}% accuracy - Revisar fallos criticos ***")

sys.exit(0 if failed_tests == 0 else 1)
